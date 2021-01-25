# Motivation
This project is intended to simplify the provision of firmware images for remote over-the-air (OTA) updates using the ESP8266 OTA library (see references).  It can also serve as a simple repository for firmware images for multiple projects.

The code was written to work as a Heroku service, but should work fine on any server with only minor modifications.

# Endpoints
<span style="background-color:#0f6ab4; width:50px; color: white; display: inline-block;    text-align: center;">GET</span> `get/<name>`
> Return the firmware associated with &lt;name>; does not perform any version checks.


<span style="background-color:#0f6ab4; width:50px; color: white; display: inline-block;    text-align: center;">GET</span> `get-esp/<name>`
> The ESP OTA library sends a hash along with its request in the `HTTP_X_ESP8266_SKETCH_MD5` header.  This endpoint will check the sent hash against the one in the database.  If the hashes match, a 302 code is returned, which signals ESP OTA that no update is required; if they do not match, the firmware associated with &lt;name> will be sent, which will trigger the device to update.
>
>Note that the header `HTTP_X_ESP8266_SKETCH_MD5` is mandatory with this endpoint, and is automatically supplied with the standard ESP OTA request.

<span style="background-color:#10a54a; width:50px; color: white; display: inline-block;    text-align: center;">POST</span> `upload`
> Upload a new version of the firmware.
>
> Sample curl request that can be used to update the firmware on the server:
>
> `curl -F "firmware=@<firmware_file>" -H "key: <your_key>" <server-url>/upload`
>
> Substitute your firmware file, key, and server URL as appropriate.  Note that the `@` is required.


# Errors
In case of error, the service will return a code of 400, along with a brief string message describing the problem.

### Errors retrieving firmware
- `Could not find name`: Requested name does not exist.
- `No firwmare for name`: No firmware has been uploaded for the specified name.
- `Missing header: HTTP_X_ESP8266_SKETCH_MD5`: When requeting firmware using the get-esp endpoint, required header `HTTP_X_ESP8266_SKETCH_MD5` is missing.  This header is added automatically by the standard ESP OTA code.

### Errors uploading firmware
- `Missing file`: No file was included with request (file should be passed with the name "firmware" -- see curl example under upload).
- `Empty filename`: Specified filename is empty.
- `Missing key`: Request did not include a required key header.
- `Bad key`: Key is incorrect or unknown.
- `Too big`: Supplied file is too large for the system.

# Requirements
The service uses a Postgres database to store project information as well as the firware images themselves.  The table structure is specified in the code, but you'll have to create them manually.

# Adding projects
To add a new project, you'll need to add a record to the app table; all that's needed is a unique name and key, which acts as a password.  Keep this key private.  Users can download the firmware images using the name, so won't need your key.

There are currently no plans to add any project management endpoints, though pull requests to do this would be considered.


# References
https://arduino-esp8266.readthedocs.io/en/latest/ota_updates/readme.html#http-server
