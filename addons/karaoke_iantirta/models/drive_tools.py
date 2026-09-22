import json

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    raise ImportError("Cannot Continue as google-auth is not installed")


SCOPES = ['https://www.googleapis.com/auth/drive']
drive_flow = None


def get_creds(user_info: str | dict | None = None):
    if user_info:
        if isinstance(user_info, str):
            user_info = json.loads(user_info)
        elif isinstance(user_info, dict):
            user_info = json.load(user_info)
        creds = Credentials.from_authorized_user_info(user_info)
        refresh_creds(creds)
        return creds
    return None


def setup_create_creds(
    client_config: str | dict,
    redirect_uri: str,
    state,
) -> str:
    if isinstance(client_config, str):
        client_config = json.loads(client_config)
    elif isinstance(client_config, dict):
        client_config = json.load(client_config)

    global drive_flow
    drive_flow = InstalledAppFlow.from_client_config(
        client_config,
        SCOPES,
        redirect_uri=redirect_uri,
        #redirect_uri="urn:ietf:wg:oauth:2.0:oob",
    )
    auth_url, _ = drive_flow.authorization_url(
        access_type="offline",
        include_granted_scopes='true',
        login_hint='tirtamoto@gmail.com',
        state=state,
    )
    return auth_url


def post_create_creds(code: str) -> Credentials:
    global drive_flow
    if not drive_flow:
        raise RuntimeError("post create must be run after setup creds")
    drive_flow.fetch_token(code=code)
    creds = drive_flow.credentials
    drive_flow = None # Remove?
    return creds


def refresh_creds(creds: Credentials) -> bool:
    if creds.refresh_token:
        creds.refresh(Request())
        return True
    raise RuntimeError("Creds doesnt have refrssh token")
