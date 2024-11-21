import subprocess

from global_def import *
from dataclasses import dataclass
from typing import List,Dict

class UsbVideo:
    def __init__(self):
        self.connected_devices = []

    def find_usb_devices(self, device_map):
        matching_devices = []
        try:
            result = subprocess.run(["lsusb"], capture_output=True, text=True, check=True)
            usb_lines = result.stdout.splitlines()
            self.connected_devices.clear()
            for line in usb_lines:
                parts = line.split()
                if len(parts) >= 6:
                    vendor_product = parts[5]
                    vendor_id, product_id = vendor_product.split(":")
                    self.connected_devices.append(UsbDeviceInfo(vendor_id=vendor_id, product_id=product_id, description=""))

            for device in self.connected_devices:
                for predefined_device in device_map.values():
                    if (device.vendor_id == predefined_device.vendor_id and
                            device.product_id == predefined_device.product_id):
                        matching_devices.append(predefined_device)
        except Exception as e:
            print(f"Error reading USB devices: {e}")

        return matching_devices
