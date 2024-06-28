import os
from settings import settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# If modifying these SCOPES, delete token.json.
SCOPES = settings.SCOPES

# Path to your OAuth 2.0 Client Credentials JSON file
CLIENT_SECRET_FILE = settings.CLIENT_SECRET_FILE

# Folder ID of the Google Drive folder you want to scrape
FOLDER_ID = settings.FOLDER_ID


def authenticate():
    """Authenticate the user and return the Google Drive service."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('drive', 'v3', credentials=creds)
    return service


def list_all_files(service, folder_id):
    results = service.files().list(
        q=f"'{folder_id}' in parents",
        pageSize=100,
        fields="files(id, name)"
    ).execute()
    items = results.get('files', [])
    return items


def download_file(service, file_id, file_name, output_dir='downloads'):
    request = service.files().get_media(fileId=file_id)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    with open(os.path.join(output_dir, file_name), 'wb') as f:
        downloader = MediaIoBaseDownload(f, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}%.")


def main():
    service = authenticate()
    files = list_all_files(service, FOLDER_ID)
    for file in files:
        print(f"Downloading {file['name']} ({file['id']})...")
        download_file(service, file['id'], file['name'])


if __name__ == '__main__':
    main()
