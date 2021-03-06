# (C) 2021 Chris Eykamp
#
# To deploy to Heroku:
#   For production: git push pro master
#
# View logs: heroku logs --tail --remote pro
#
# curl -F "firmware=@filename" -H "key: 12345" https://firmware-update-service.herokuapp.com/put
#
"""
Start postgres from cmd:
    heroku pg:psql -a firmware-update-service

Postgres table structure:

    CREATE TABLE firmware (
        key TEXT UNIQUE NOT NULL,
        md5 TEXT NOT NULL,
        firmware BYTEA NOT NULL );

    CREATE TABLE app (
        key TEXT UNIQUE NOT NULL,
        name TEXT UNIQUE NOT NULL );
"""

import hashlib
from collections import namedtuple
from typing import NamedTuple, Tuple, Union
from flask import Flask, request, Response
import psycopg2
import os
from enum import Enum


app = Flask(__name__)

DATABASE_URL = os.environ["DATABASE_URL"]       # Heroku maintains this value

conn = psycopg2.connect(DATABASE_URL, sslmode="require")

HashedFirmware = NamedTuple("HashedFirmware", [("data", bytes), ("md5", str)])    # Type def for firmware info

MEGABYTES = 1024 * 1024


class VersionCheck(Enum):
    NONE = 0
    ESP = 1


@app.route('/')
def welcome():
    return "Welcome to the Trans-Planetary Corporation Firmware Update Service!"


@app.route("/get/<name>", methods=["GET"])
def update(name):
    """ Endpoint for retrieving firmware with no version checks. """
    return send_firmware(name, VersionCheck.NONE)


@app.route("/get-esp/<name>", methods=["GET"])
def update_esp(name):
    """ Endpoint tailored to ESP8266 OTA script. """
    return send_firmware(name, VersionCheck.ESP)


def send_firmware(name: str, version_check: VersionCheck) -> Union[Response, Tuple[str, int]]:
    try:
        firmware = get_firmware_from_database(name)
    except Exception as ex:
        return str(ex), 400

    if version_check == VersionCheck.ESP:
        if "HTTP_X_ESP8266_SKETCH_MD5" not in request.headers:
            return "Missing header: HTTP_X_ESP8266_SKETCH_MD5", 400

        client_md5 = request.headers["HTTP_X_ESP8266_SKETCH_MD5"]
        if client_md5 == firmware.md5:
            # Already have most recent firmware
            return "", 302

    # Sending firmware
    return Response(firmware.data, mimetype="application/octet-stream", headers={"X-MD5": firmware.md5})


    # Other available headers from ESP OTA:
    # 'HTTP_CONNECTION': 'close',
    # 'HTTP_HOST': 'www.abc.org:8989',
    # 'HTTP_USER_AGENT': 'ESP8266-http-Update',
    # 'HTTP_X_ESP8266_AP_MAC': '2E:3A:E8:18:1C:38',
    # 'HTTP_X_ESP8266_CHIP_SIZE': '4194304',
    # 'HTTP_X_ESP8266_FREE_SPACE': '2818048',
    # 'HTTP_X_ESP8266_MODE': 'sketch',
    # 'HTTP_X_ESP8266_SDK_VERSION': '2.2.1(cfd48f3)',
    # 'HTTP_X_ESP8266_SKETCH_MD5': '3f74331d79d8124c238361dcebbf3dc4',
    # 'HTTP_X_ESP8266_SKETCH_SIZE': '324512',
    # 'HTTP_X_ESP8266_STA_MAC': '2D:3A:E8:01:2C:38',
    # 'HTTP_X_ESP8266_VERSION': '0.120',


@app.route("/upload", methods=["POST"])
def upload_firmware():
    """
    Upload a new copy of the firmware to the database. Need to provide a file
    called "firmware" and a header called "key" with the secret app key in it.

    curl -F "firmware=@filename" -H "key: 12345" https://firmware-update-service.herokuapp.com/upload
    """
    if "key" not in request.headers:
        return "Missing key", 400

    key = request.headers["key"]        # Apparently case insensitive
    cur = conn.cursor()

    # Is this a known key?
    if not app_exists(cur, key):
        return "Bad key", 400

    # Upload with filename "file"
    if "firmware" not in request.files:
        print(f"Missing file: request.files = {request.files}", flush=True)
        return "Missing file", 400

    file = request.files["firmware"]
    if file.filename == "":
        return "Empty filename", 400

    # Insert new firmware record
    firmware = file.stream.read()

    if len(firmware) > 3 * MEGABYTES:
        return "Too big", 400

    # Delete any existing firmware records
    query = "DELETE FROM firmware WHERE key = %s;"
    cur.execute(query, [key])

    md5 = hashlib.md5(firmware).hexdigest()
    query = "INSERT INTO firmware (key, md5, firmware) VALUES(%s, %s, %s);"
    cur.execute(query, [key, md5, firmware])

    conn.commit()       # Make insert permanent

    return "Ok", 200


def app_exists(cur, key: str) -> bool:
    query = "SELECT * FROM app WHERE key = %s;"
    cur.execute(query, [key])

    return cur.fetchone() is not None


def get_firmware_from_database(name: str) -> HashedFirmware:
    cur = conn.cursor()

    # Get key
    query = "SELECT key FROM app WHERE name = %s"
    cur.execute(query, [name])
    row = cur.fetchone()
    if not row:
        print(f"Cound not find name '{name}' in app table", flush=True)
        raise Exception("Could not find name")
    key = row[0]

    # Use key to get firmware
    query = "SELECT firmware, md5 FROM firmware WHERE key = %s"
    row = cur.execute(query, [key])
    row = cur.fetchone()
    if not row:
        print(f"No firmware for key '{key}' ('{name}') in firmware table", flush=True)
        raise Exception("No firwmare for name")

    return HashedFirmware(row[0], row[1])



if __name__ == "__main__":
    app.run()