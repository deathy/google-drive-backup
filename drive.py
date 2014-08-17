"""Download your entire Google Drive folder

Command-line application that downloads entire Google Drive folder to a 'downloaded/' folder.
All possible exports are performed.

Usage:
    $ python drive.py
"""

__author__ = 'viky.nandha@gmail.com (Vignesh Nandha Kumar); jeanbaptiste.bertrand@gmail.com (Jean-Baptiste Bertrand); Cristian Vat'

import httplib2, os, sys, re, time

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import AccessTokenRefreshError, flow_from_clientsecrets
from oauth2client.tools import run

# CLIENT_SECRETS, name of a file containing the OAuth 2.0 information for this
# application, including client_id and client_secret, which are found
# on the API Access tab on the Google APIs
# Console <http://code.google.com/apis/console>

CLIENT_SECRETS = "client_secrets.json"  # the path to the client_secrets has to be defined in this conf file

# Helpful message to display in the browser if the CLIENT_SECRETS file
# is missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

%s

with information from the APIs Console <https://code.google.com/apis/console>.

""" % os.path.join(os.path.dirname(__file__), CLIENT_SECRETS)

# Set up a Flow object to be used if we need to authenticate.
FLOW = flow_from_clientsecrets(CLIENT_SECRETS,
                               scope='https://www.googleapis.com/auth/drive',
                               message=MISSING_CLIENT_SECRETS_MESSAGE)

extensions = {
    # generic mime types and extensions
    'text/html': '.html',
    'text/plain': '.txt',
    'image/jpeg': '.jpg',
    'image/svg+xml': '.svg',
    'image/png': '.png',
    'application/pdf': '.pdf',
    'application/rtf': '.rtf',
    # microsoft office document mime types and extensions ( http://technet.microsoft.com/en-us/library/cc179224.aspx )
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document':'.docx',
    'application/vnd.ms-word.document.macroEnabled.12':'.docm',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.template':'.dotx',
    'application/vnd.ms-word.template.macroEnabled.12':'.dotm',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':'.xlsx',
    'application/vnd.ms-excel.sheet.macroEnabled.12':'.xlsm',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.template':'.xltx',
    'application/vnd.ms-excel.template.macroEnabled.12':'.xltm',
    'application/vnd.ms-excel.sheet.binary.macroEnabled.12':'.xlsb',
    'application/vnd.ms-excel.addin.macroEnabled.12':'.xlam',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation':'.pptx',
    'application/vnd.ms-powerpoint.presentation.macroEnabled.12':'.pptm',
    'application/vnd.openxmlformats-officedocument.presentationml.slideshow':'.ppsx',
    'application/vnd.ms-powerpoint.slideshow.macroEnabled.12':'.ppsm',
    'application/vnd.openxmlformats-officedocument.presentationml.template':'.potx',
    'application/vnd.ms-powerpoint.template.macroEnabled.12':'.potm',
    'application/vnd.ms-powerpoint.addin.macroEnabled.12':'.ppam',
    'application/vnd.openxmlformats-officedocument.presentationml.slide':'.sldx',
    'application/vnd.ms-powerpoint.slide.macroEnabled.12':'.sldm',
    'application/onenote':'.onetoc',
    # open document (open office) mime types and extensions ( http://en.wikipedia.org/wiki/OpenDocument_technical_specification#Documents )
    'application/vnd.oasis.opendocument.text': '.odt',
    'application/vnd.oasis.opendocument.spreadsheet': '.ods',
    'application/x-vnd.oasis.opendocument.spreadsheet': '.ods',
    'application/vnd.oasis.opendocument.presentation': '.odp',
    'application/vnd.oasis.opendocument.graphics': '.odg',
    'application/vnd.oasis.opendocument.chart': '.odc',
    'application/vnd.oasis.opendocument.formula': 'odf',
    'application/vnd.oasis.opendocument.image': '.odi',
    'application/vnd.oasis.opendocument.text-master': '.odm',
    'application/vnd.sun.xml.base': '.odm',
    'application/vnd.oasis.opendocument.base': '.odm',
    'application/vnd.oasis.opendocument.database': 'odb'
}


def ensure_dir(directory):
    if not os.path.exists(directory):
        print("Creating directory: %s" % directory)
        os.makedirs(directory)


def is_google_doc(drive_file):
    return True if re.match('^application/vnd\.google-apps\..+', drive_file['mimeType']) else False


def get_folder_contents(service, http, folder, base_path='./', depth=0):
    print("\n" + ' ' * depth + "Getting contents of folder %s" % folder['title'])
    try:
        folder_contents = service.files().list(q="'%s' in parents" % folder['id']).execute()
    except:
        print("ERROR: Couldn't get contents of folder %s. Retrying..." % folder['title'])
        get_folder_contents(service, http, folder, base_path, depth)
        return
    folder_contents = folder_contents['items']
    dest_path = base_path + folder['title'].replace('/', '_') + '/'

    def is_file(item):
        return item['mimeType'] != 'application/vnd.google-apps.folder'

    def is_folder(item):
        return item['mimeType'] == 'application/vnd.google-apps.folder'

    for item in folder_contents:
        if is_folder(item):
            print(' ' * depth + "[] " + item['title'])
        else:
            print(' ' * depth + "-- " + item['title'])

    ensure_dir(dest_path)
    for item in filter(is_file, folder_contents):
        # Check if it is a native Gdoc
        if 'exportLinks' in item:
            for exportMimeType in item['exportLinks'].keys():
                if not exportMimeType in extensions:
                    print("Couldn't find mime-type mapping: " + exportMimeType)
                    continue
                extension = extensions[exportMimeType]
                full_path = dest_path + clean_file_name(item['title']) + extension
                if download_file(service, item, dest_path, exportMimeType):
                    print("Created %s" % full_path)
                else:
                    print("ERROR while saving %s" % full_path)
        if 'downloadUrl' in item:
            full_path = dest_path + clean_file_name(item['title'])
            if download_file(service, item, dest_path, 'DIRECT_DOWNLOAD'):
                print("Created %s" % full_path)
            else:
                print("ERROR while saving %s" % full_path)

    for item in filter(is_folder, folder_contents):
        get_folder_contents(service, http, item, dest_path, depth + 1)


def clean_file_name(original):
    return original.replace('/', '_').replace('?', '_')


def download_file(service, drive_file, dest_path, dest_mimeType):
    """Download a file's content.

    Args:
    service: Drive API service instance.
    drive_file: Drive File instance.

    Returns:
    File's content if successful, None otherwise.
    """
    # Showing progress
    print drive_file['title'] + " download in progress..."
    if is_google_doc(drive_file):
        if 'exportLinks' in drive_file:
            if not dest_mimeType in extensions:
                return False
            extension = extensions[dest_mimeType]
            file_location = dest_path + drive_file['title'].replace('/', '_') + os.extsep + extension
            # From the "export_mimeType" dictionary, retrieving data corresponding to the source mimeType:
            # Retrieving the target mimeType (index 0) for putting it as a download url parameter
            download_url = drive_file.get('exportLinks')[dest_mimeType]
        else:
            # if source mimeType is unknown, the google doc can't be exported
            print drive_file['title'] + " can't be exported (" + drive_file['mimeType'] + " mimeType)"
            return False
    else:
        file_location = dest_path + drive_file['title'].replace('/', '_')
        download_url = drive_file['downloadUrl']
    if download_url:
        try:
            resp, content = service._http.request(download_url)
        except httplib2.IncompleteRead:
            print('Error while reading file %s. Retrying...' % drive_file['title'].replace('/', '_'))
            download_file(service, drive_file, dest_path, dest_mimeType)
            return False
        if resp.status == 200:
            try:
                target = open(file_location, 'wb')
            except:
                print("Could not open file %s for writing. Please check permissions." % file_location)
                return False
            target.write(content)
            target.close()
            return True
        else:
            print('An error occurred: %s' % resp)
            return False
    else:
        # The file doesn't have any content stored on Drive.
        return False


def main():
    # If the Credentials don't exist or are invalid run through the native client
    # flow. The Storage object will ensure that if successful the good
    # Credentials will get written back to a file.
    storage = Storage('drive.dat')
    credentials = storage.get()

    if credentials is None or credentials.invalid:
        credentials = run(FLOW, storage)

    # Create an httplib2.Http object to handle our HTTP requests and authorize it
    # with our good Credentials.
    http = httplib2.Http()
    http = credentials.authorize(http)

    service = build("drive", "v2", http=http)

    try:
        start_folder = service.files().get(fileId='root').execute()
        if not os.path.exists('downloaded/'):
            os.makedirs('downloaded/')
        get_folder_contents(service, http, start_folder, 'downloaded/')
    except AccessTokenRefreshError:
        print ("The credentials have been revoked or expired, please re-run"
               "the application to re-authorize")


if __name__ == '__main__':
    main()
