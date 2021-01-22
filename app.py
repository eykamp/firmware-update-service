# To deploy to Heroku:
#   For staging: git push stage master
#   For production: git push pro master


import hashlib
from collections import namedtuple
from typing import NamedTuple
from flask import Flask, request, Response

app = Flask(__name__)

FIRMWARE_LOCATION = "firmware-images"            # Location on the server

HashedFirmware = NamedTuple("HashedFirmware", [("data", bytes), ("md5", str)])    # Type def for firmware info


def get_firmware(firmware_path: str) -> HashedFirmware:
    with open(firmware_path, "rb") as f:
        bin_image = f.read()
    md5 = hashlib.md5(bin_image).hexdigest()
    print("Found firmware bytes={} md5={}".format(len(bin_image), md5))
    return HashedFirmware(bin_image, md5)


@app.route('/')
def welcome():
    return "Welcome to the Trans-Planetary Corporation Firmware Update Service!"


# door_opener.ino.bin
@app.route("/update/<name>", methods=["GET"])
def update(name):
    # Returns the full file/path of the latest firmware, or None if we are
    # already running the latest
    client_md5 = request.headers["HTTP_X_ESP8266_SKETCH_MD5"]

    firmware = get_firmware(FIRMWARE_LOCATION + "/" + name)
    if client_md5 == firmware.md5:
        print("Already have most recent firmware")
        return "", 302

    print("Sending firmware")
    return Response(firmware.data, mimetype="application/octet-stream", headers={"X-MD5": firmware.md5})


    # Other available headers
    # 'HTTP_CONNECTION': 'close',
    # 'HTTP_HOST': 'www.abc.org:8989',
    # 'HTTP_USER_AGENT': 'ESP8266-http-Update',
    # 'HTTP_X_ESP8266_AP_MAC': '2E:3A:E8:08:2C:38',
    # 'HTTP_X_ESP8266_CHIP_SIZE': '4194304',
    # 'HTTP_X_ESP8266_FREE_SPACE': '2818048',
    # 'HTTP_X_ESP8266_MODE': 'sketch',
    # 'HTTP_X_ESP8266_SDK_VERSION': '2.2.1(cfd48f3)',
    # 'HTTP_X_ESP8266_SKETCH_MD5': '3f74331d79d8124c238361dcebbf3dc4',
    # 'HTTP_X_ESP8266_SKETCH_SIZE': '324512',
    # 'HTTP_X_ESP8266_STA_MAC': '2C:3A:E8:08:2C:38',
    # 'HTTP_X_ESP8266_VERSION': '0.120',

if __name__ == "__main__":
    app.run()