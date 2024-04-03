import os
import platform
import signal
import subprocess
import re
from global_def import log


def mute_audio_sinks(mute=True):
    result = subprocess.run(['pactl', 'list', 'short', 'sinks'], stdout=subprocess.PIPE, text=True)
    output = result.stdout

    sink_ids = [line.split('\t')[0] for line in output.strip().split('\n') if line]
    max_sink = 5
    for sink_id in sink_ids:
        max_sink = max_sink - 1
        mute_flag = '1' if mute else '0'
        subprocess.run(['pactl', 'set-sink-mute', sink_id, mute_flag])
        if max_sink <= 0:
            break


class SoundDevices:
    def __init__(self):
        self.audio_process = None
        self.pulseaudio_command = "pulseaudio"
        self.tc358743_card = None
        self.tc358743_device = None
        self.headphones_card = None
        self.headphones_device = None
        subprocess.Popen("pkill -f arecord", shell=True)
        mute_audio_sinks(False)

    def pulse_audio_status(self):
        try:
            subprocess.check_call([self.pulseaudio_command, '--check'])
            return True
        except subprocess.CalledProcessError:
            return False

    def start_pulse_audio(self):
        if self.pulse_audio_status():
            log.debug("PulseAudio is already running.")
            return True
        else:
            try:
                subprocess.check_call([self.pulseaudio_command, '--start'])
                log.debug("PulseAudio started successfully.")
                return True
            except subprocess.CalledProcessError:
                log.debug("Failed to start PulseAudio.")
                return False

    def capture_hdmi_rcv_devices(self):
        result = subprocess.run(['arecord', '-l'], stdout=subprocess.PIPE, text=True)
        output = result.stdout
        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            match = re.search(r'card (\d+): tc358743.*device (\d+):', output)
        else:
            match = re.search(r'card (\d+): Audio.*device (\d+):', output)

        if match:
            self.tc358743_card = match.group(1)
            self.tc358743_device = match.group(2)
            # log.debug(f"tc358743 hw: {self.tc358743_card},{self.tc358743_device}")
            return self.tc358743_card, self.tc358743_device
        else:
            return None, None

    def capture_Headphones_devices(self):
        result = subprocess.run(['aplay', '-l'], stdout=subprocess.PIPE, text=True)
        output = result.stdout

        if platform.machine() in ('arm', 'arm64', 'aarch64'):
            match = re.search(r'card (\d+): Headphones.*device (\d+):', output)
        else:
            match = re.search(r'card (\d+): Audio.*device (\d+):', output)

        if match:
            self.headphones_card = match.group(1)
            self.headphones_device = match.group(2)
            # log.debug(f"Headphone hw: {self.headphones_card},{self.headphones_device}")
            return self.headphones_card, self.headphones_device
        else:
            return None, None

    def start_play(self, source_card, source_device, sink_card, sink_device,
                   fmt="cd", file_type="wav", buf_us="500000", period_us="100000"):

        audio_source = f"hw:{source_card},{source_device}"
        audio_sink = f"hw:{sink_card},{sink_device}"
        audio_recorder = (
            f"arecord -q -D {audio_source} -f {fmt} -t {file_type} "
            f"--buffer-time={buf_us} --period-time={period_us}"
        )
        audio_play = f"aplay -q -D {audio_sink} -"
        audio_cmd = f"{audio_recorder} | {audio_play}"

        log.debug("audio.cmd : %s", audio_cmd)
        try:
            self.audio_process = subprocess.Popen(audio_cmd, shell=True, preexec_fn=os.setsid,
                                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        except Exception as e:
            log.debug(f"Start error: {e}")

    def stop_play(self):
        if hasattr(self, 'audio_process') and self.audio_process:
            os.killpg(os.getpgid(self.audio_process.pid), signal.SIGINT)
            try:
                self.audio_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(self.audio_process.pid), signal.SIGTERM)
                try:
                    self.audio_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    os.killpg(os.getpgid(self.audio_process.pid), signal.SIGKILL)
            finally:
                self.audio_process = None

