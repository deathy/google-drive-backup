Google Drive Backup
===================

A python script to backup your google drive contents.

## Features
* Downloads entire Google Drive folder all the time
* Downloads to fixed `downloads/` sub folder
* File type behavior:
    * normal files which have been uploaded are downloaded as-is
    * google documents (docs,spreadsheets,drawings,presentations,etc) are exported in all possible export formats ( this
    means more files and space, but exporting all gives you a choice later on)
* Uses OAuth2 authentication and can remember authentication
* _'feature'_: doesn't check modification times, always downloads everything. There are other better diff/backup tools 
for incremental backup which you can use after 

## Requirements
* Google API Python library. To install run
`pip install --upgrade google-api-python-client` or
`easy_install --upgrade google-api-python-client`

## Setup
* Edit `client_secrets_sample.json` and add your Google API client id and client secret (If you don't have one, [get it here](https://code.google.com/apis/console/)).
* Save it as `client_secrets.json`.
* Now, if you run `python drive.py`, a browser window/tab will open for you to authenticate the script.
* Once authentication is done, the script will start downloading your *My Drive*. Refer the next section for more options.
