import os

from flask_routes.routes_ops import get_sleep_mode_default, get_brightness_mode_default, get_target_city_default, \
    get_city_list, get_reboot_mode_default, get_brightness_value_default, mp4_extends, jpg_extends, jpeg_extends, \
    png_extends, playlist_extends, get_default_play_mode_default, get_playlist_default, get_frame_rate_res_default, \
    get_icled_type_default, get_still_image_period_default, get_icled_current_gain_values_default, \
    get_audio_enable_default, get_preview_enable_default, get_media_crop_values_default, get_hdmi_crop_values_default
from global_def import log, internal_media_folder, PlaylistFolder, play_type, ThumbnailFileFolder
from flask import render_template, send_from_directory, Response, request, redirect, url_for
import hashlib
import glob
import json
from flask_wtf import Form
from wtforms import validators, RadioField, SubmitField, IntegerField, SelectField, StringField, TimeField, DateField, \
    DateTimeField
from main import app
from qlocalmessage import send_message
from global_def import log, Version

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY


def get_playlist_list():
    playlist_list = []
    for playlist_tmp in sorted(glob.glob(playlist_extends)):
        # log.debug("playlist_tmp = %s", playlist_tmp)
        if os.path.isfile(playlist_tmp):
            fname_url = playlist_tmp.split("/")
            fname = fname_url[len(fname_url) - 1]
            # log.debug("fname : %s", fname)
            playlist_list.append(fname)
    if len(playlist_list) == 0:
        playlist_list.append("")
    return playlist_list


def find_file_maps():
    maps = {}

    # log.debug("mp4_extends = %s", mp4_extends)
    # need to add png/jpg/jpeg
    for file_name in sorted(glob.glob(mp4_extends)):
        if os.path.isfile(file_name):
            list_file_url = file_name.split("/")
            tmp_video_name = list_file_url[len(list_file_url) - 1]
            key = tmp_video_name
            prefix_video_name = tmp_video_name.split(".")[0]
            # log.debug("video_extension = %s", video_extension)
            preview_file_name = hashlib.md5(prefix_video_name.encode('utf-8')).hexdigest() + ".webp"
            maps[key] = preview_file_name
    for file_name in sorted(glob.glob(jpg_extends)):
        if os.path.isfile(file_name):
            list_file_url = file_name.split("/")
            tmp_video_name = list_file_url[len(list_file_url) - 1]
            key = tmp_video_name
            prefix_video_name = tmp_video_name.split(".")[0]
            # log.debug("video_extension = %s", video_extension)
            preview_file_name = hashlib.md5(prefix_video_name.encode('utf-8')).hexdigest() + ".webp"
            maps[key] = preview_file_name
    for file_name in sorted(glob.glob(jpeg_extends)):
        if os.path.isfile(file_name):
            list_file_url = file_name.split("/")
            tmp_video_name = list_file_url[len(list_file_url) - 1]
            key = tmp_video_name
            prefix_video_name = tmp_video_name.split(".")[0]
            # log.debug("video_extension = %s", video_extension)
            preview_file_name = hashlib.md5(prefix_video_name.encode('utf-8')).hexdigest() + ".webp"
            maps[key] = preview_file_name
    for file_name in sorted(glob.glob(png_extends)):
        if os.path.isfile(file_name):
            list_file_url = file_name.split("/")
            tmp_video_name = list_file_url[len(list_file_url) - 1]
            key = tmp_video_name
            prefix_video_name = tmp_video_name.split(".")[0]
            # log.debug("video_extension = %s", video_extension)
            preview_file_name = hashlib.md5(prefix_video_name.encode('utf-8')).hexdigest() + ".webp"
            maps[key] = preview_file_name

    return maps


def get_file_list() -> list:
    file_list = []
    for fname in sorted(glob.glob(mp4_extends)):
        if os.path.isfile(fname):
            fname = fname.strip(internal_media_folder + "/")
            file_list.append(fname)
    for fname in sorted(glob.glob(jpg_extends)):
        if os.path.isfile(fname):
            fname = fname.strip(internal_media_folder + "/")
            file_list.append(fname)
    for fname in sorted(glob.glob(jpeg_extends)):
        if os.path.isfile(fname):
            fname = fname.strip(internal_media_folder + "/")
            file_list.append(fname)
    for fname in sorted(glob.glob(png_extends)):
        if os.path.isfile(fname):
            fname = fname.strip(internal_media_folder + "/")
            file_list.append(fname)

    return file_list


def get_single_file_default() -> str:
    try:
        with open(os.getcwd() + "/static/default_launch_type.dat", "r") as launch_type_config_file:
            tmp = launch_type_config_file.read()
            default_launch_type_int = int(tmp.split(":")[0])
            default_launch_type_params_str = tmp.split(":")[1]
            if default_launch_type_int == play_type.play_single:
                log.debug("get_single_file_default :" + default_launch_type_params_str)
                return default_launch_type_params_str
            else:
                file_list = get_file_list()
                log.debug("file_list[0] :" + file_list[0])
                return file_list[0]
    except Exception as e:
        log.debug(e)
    file_list = get_file_list()
    return file_list[0]


def find_playlist_maps() -> map:
    playlist_nest_dict = {}
    for playlist_tmp in sorted(glob.glob(playlist_extends)):
        # log.debug("playlist_tmp = %s", playlist_tmp)
        if os.path.isfile(playlist_tmp):
            playlist_name_list = playlist_tmp.split("/")
            playlist_name = playlist_name_list[len(playlist_name_list) - 1]
            playlist_nest_dict[playlist_name] = {}
            f = open(playlist_tmp)
            lines = f.readlines()
            for line in lines:
                line = line.strip("\n")
                fname_url = line.split("/")
                fname = fname_url[len(fname_url) - 1]
                prefix_video_name = fname.split(".")[0]
                # log.debug("video_extension = %s", video_extension)
                preview_file_name = hashlib.md5(prefix_video_name.encode('utf-8')).hexdigest() + ".webp"
                # bug
                # if the fname is the same as item before, there is only one in nest!!!!!
                playlist_nest_dict[playlist_name][fname] = preview_file_name

    # print(playlist_nest_dict)

    return playlist_nest_dict


@app.route('/set_default_play_mode/<data>', methods=['POST'])
def set_default_play_mode(data):
    log.debug("set_default_play_mode data :" + data)
    # send_message(set_default_play_mode_option=data)
    tmp = data
    default_mode = "0"
    default_params = ""
    try:
        if "none_mode" in tmp:
            default_mode = "0"
            default_params = ""
        elif "single_file_mode" in tmp:
            default_mode = "1"
            default_params = tmp.split(":")[1]
        elif "playlist_mode" in tmp:
            default_mode = "2"
            default_params = tmp.split(":")[1]
        elif "hdmi_in_mode" in tmp:
            default_mode = "3"
            default_params = ""
        elif "cms_mode" in tmp:
            default_mode = "4"
            default_params = ""
    except Exception as e:
        log.debug(e)

    str_tmp = default_mode + ":" + default_params
    log.debug("str_tmp = %s", str_tmp)

    try:
        with open(os.getcwd() + "/static/default_launch_type.dat", "w") as launch_type_config_file:
            launch_type_config_file.write(str_tmp)
            launch_type_config_file.flush()
            launch_type_config_file.truncate()
            launch_type_config_file.close()
            os.popen("sync")
    except Exception as e:
        log.debug(e)
    status_code = Response(status=200)
    return status_code


@app.route('/get_thumbnail/<filename>')
def route_get_thumbnail(filename):
    # log.debug("fname = %s", filename)
    return send_from_directory(internal_media_folder + ThumbnailFileFolder, filename, as_attachment=True)


@app.route('/set_brightness_algo/<data>', methods=['POST'])
def set_brightness_algo(data):
    log.debug("set_brightness_algo data :" + data)
    send_message(set_brightness_algo=data)
    status_code = Response(status=200)
    return status_code


@app.route('/set_target_city/<data>', methods=['POST'])
def set_target_city(data):
    log.debug("set_target_city, data = %s", data)
    send_message(set_target_city=data)
    status_code = Response(status=200)
    return status_code


@app.route('/set_sleep_mode/<data>', methods=['POST'])
def set_sleep_mode(data):
    log.debug("set_sleep_mode, data = %s", data)
    send_message(set_sleep_mode=data)
    status_code = Response(status=200)
    return status_code


@app.route('/set_audio_preview_res_values/<data>', methods=['POST'])
def set_audio_preview_res_values(data):
    log.debug("set_audio_preview_mode, data = %s", data)
    send_message(set_audio_preview_mode=data)
    status_code = Response(status=200)
    return status_code


@app.route('/set_media_crop_res_values/<data>', methods=['POST'])
def set_media_crop_res_values(data):
    log.debug("set_media_crop_res_values, data = %s", data)
    send_message(set_media_crop_values=data)
    status_code = Response(status=200)
    return status_code


@app.route('/set_hdmi_crop_res_values/<data>', methods=['POST'])
def set_hdmi_crop_res_values(data):
    log.debug("set_hdmi_crop_res_values, data = %s", data)
    send_message(set_hdmi_crop_values=data)
    status_code = Response(status=200)
    return status_code


@app.route('/set_brightness_values/<data>', methods=['POST'])
def set_brightness_values(data):
    log.debug("set_brightness_values data :" + data)
    send_message(set_frame_brightness_values_option=data)
    status_code = Response(status=200)
    return status_code


@app.route('/set_icled_type_gain/<data>', methods=['POST'])
def set_icled_type_gain(data):
    log.debug("set_icled_type_gain data :" + data)
    send_message(set_icled_type_gain=data)
    status_code = Response(status=200)
    return status_code

@app.route('/set_image_period_values/<data>', methods=['POST'])
def set_image_period_values(data):
    log.debug("set_image_period_values data :" + data)
    send_message(set_image_period_values=data)
    status_code = Response(status=200)
    return status_code

@app.route('/set_frame_rate_res_values/<data>', methods=['POST'])
def set_frame_rate_res_values(data):
    log.debug("set_frame_rate_res_values data :" + data)
    send_message(set_frame_rate_res_values=data)
    status_code = Response(status=200)
    return status_code


@app.route('/uploads', methods=['POST'])
def uploads():
    log.debug("request.method : %s", request.method)
    # print("request.files['file']", request.files['file'])
    f = request.files['file']
    f.save(internal_media_folder + "/" + f.filename)
    # send_message(internal_medialist_change=True)
    '''if request.method == 'POST':
        f = request.files['file']
        f.save(f.filename)'''
    # return refresh_template()
    # time.sleep(10)
    return redirect(url_for("index"))


class BrightnessAlgoForm(Form):
    style = {'class': 'ourClasses', 'style': 'font-size:24px;color:white', }
    brightness_mode_switcher = RadioField(

        label="Brightness Mode",
        id="brightness_mode_switcher",
        choices=[('Fix Mode', 'Fix Mode'),
                 ('Time Mode', 'Time Mode'),
                 ('ALS Mode', 'ALS Mode'),
                 ('Test Mode', 'Test Mode')],
        default=get_brightness_mode_default(),

        render_kw=style,

    )
    # style = {'class': 'ourClasses', 'style': 'font-size:24px;color:white', }
    sleep_mode_switcher = RadioField(
        "Sleep Mode",
        id="sleep_mode_switcher",
        choices=[('Disable', 'Disable'),
                 ('Enable', 'Enable'),
                 ],
        default=get_sleep_mode_default(),
        render_kw=style,

    )
    city_style = {'class': 'ourClasses', 'style': 'font-size:24px;color:black;size:320px;width:200px', }
    city_selectfiled = SelectField(
        "City",
        id="city_selected",
        # choices=get_city_hash_map(),
        choices=get_city_list(),
        default=get_target_city_default(),
        render_kw=city_style,
    )

    reboot_style = {'class': 'ourClasses', 'style': 'font-size:24px;color:black;size:320px;width:200px', }
    reboot_mode_switcher = RadioField(
        "Reboot Mode",
        id="reboot_mode_switcher",
        choices=[('Disable', 'Disable'),
                 ('Enable', 'Enable'),
                 ],
        default=get_reboot_mode_default(),
        render_kw=style,
    )


class LaunchTypeForm(Form):
    # default play mode switcher
    style = {'class': 'ourClasses', 'style': 'font-size:24px;color:white', }

    launch_type_switcher = RadioField(
        label="Default Play Mode",
        id="default_play_mode_switcher",
        choices=[
            ('none_mode', 'None MODE'),
            ('single_file_mode', 'Single File Mode'),
            ('playlist_mode', 'Playlist Mode'),
            ('hdmi_in_mode', 'HDMI-In Mode'),
            # ('cms_mode', 'CMS Mode')
        ],
        default=get_default_play_mode_default(),
        render_kw=style,
    )

    icled_type_switcher = RadioField(
        label="ICLed Type",
        id="icled_type_switcher",
        choices=[
            ('anapex', 'Anapex'),
            ('aos', 'AOS')
        ],
        default=get_icled_type_default(),
        render_kw=style,
    )

    # single file list
    single_file_selectfield_style = {'class': 'ourClasses',
                                     'style': 'font-size:24px;color:black;size:320px;width:300px', }
    single_file_selectfiled = SelectField(
        "Default Play File Name",
        id="single_file_selected",
        # choices=get_city_hash_map(),
        choices=get_file_list(),
        default=get_single_file_default(),
        render_kw=single_file_selectfield_style,
    )

    # playlist list
    playlist_selectfield_style = {
        'class': 'ourClasses',
        'style': 'font-size:24px;color:black;size:320px;width:300px',
    }

    playlist_selectfield = SelectField(
        "Default Playlist Name",
        id="playlist_selected",
        # choices=get_city_hash_map(),
        choices=get_playlist_list(),
        default=get_playlist_default(),
        render_kw=single_file_selectfield_style,
    )


def refresh_template():
    maps = find_file_maps()
    playlist_nest_dict = find_playlist_maps()

    playlist_js_file = open("static/playlist.js", "w")
    playlist_json = json.dumps(playlist_nest_dict)
    playlist_js_file.write("var jsonstr = " + playlist_json)
    playlist_js_file.flush()
    playlist_js_file.truncate()
    playlist_js_file.close()

    default_play_form = LaunchTypeForm()
    default_play_form.launch_type_switcher.data = get_default_play_mode_default()
    default_play_form.icled_type_switcher.data = get_icled_type_default()

    default_play_form.single_file_selectfiled.choices = get_file_list()
    default_play_form.playlist_selectfield.choices = get_playlist_list()
    default_play_form.single_file_selectfiled.data = get_single_file_default()
    default_play_form.playlist_selectfield.data = get_playlist_default()

    brightness_algo_form = BrightnessAlgoForm()
    brightness_algo_form.sleep_mode_switcher.data = get_sleep_mode_default()
    brightness_algo_form.city_selectfiled.data = get_target_city_default()
    brightness_algo_form.reboot_mode_switcher.data = get_reboot_mode_default()
    brightness_algo_form.brightness_mode_switcher.data = get_brightness_mode_default()

    brightnessvalues = get_brightness_value_default()
    icled_current_gain_values = get_icled_current_gain_values_default()
    frame_res_rate_values = get_frame_rate_res_default()
    still_image_period = get_still_image_period_default()
    audio_enable = get_audio_enable_default()
    preview_enable = get_preview_enable_default()

    media_crop_values = get_media_crop_values_default()
    hdmi_crop_values = get_hdmi_crop_values_default()

    return render_template("index.html", title="GIS TLED", files=maps, sw_version=Version,
                           form=brightness_algo_form, brightnessvalues=brightnessvalues,
                           playlist_nest_dict=playlist_nest_dict, default_play_form=default_play_form,
                           frame_res_rate_values=frame_res_rate_values, still_image_period=still_image_period,
                           icled_current_gain_values=icled_current_gain_values, audio_enable=audio_enable,
                           preview_enable=preview_enable, media_crop_values=media_crop_values,
                           hdmi_crop_values=hdmi_crop_values)


@app.route("/")
def index():
    log.debug("flask route index")
    # send_message(cmd="got_index")
    return refresh_template()
