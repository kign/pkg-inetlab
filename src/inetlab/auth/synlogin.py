import re, uuid, json, time

import msal
from google.oauth2 import id_token
from google.auth.transport import requests

def setup_partners(google_client_id = None,
                   microsoft_client_id = None,
                   microsoft_client_secret = None) :

    GLogin.CLIENT_ID = google_client_id
    MSLogin.CLIENT_ID = microsoft_client_id
    MSLogin.CLIENT_SECRET = microsoft_client_secret

class GLogin :
    CLIENT_ID = "<CLIENT_ID>"

    @staticmethod
    def token(flsk_s, idtoken):

        user = id_token.verify_oauth2_token(idtoken, requests.Request(), GLogin.CLIENT_ID)

        if not user['iss'].endswith('accounts.google.com') :
            raise ValueError(f"Invalid iss={user['iss']}")

        if time.time() > user['exp'] :
            raise ValueError(f"Expired {time.time() - user['exp']} secs")

        flsk_s.permanent = True

        flsk_s['user'] = {
            'provider'   : "google",

            'first_name' : user['given_name'],
            'last_name'  : user['family_name'],
            'email'      : user['email'],
            'exp'        : user['exp'],
            'uid'        : user['sub'],

            # optional/google-specific
            'picture' : user['picture']
        }

        return user['email']

class MSLogin :
    CLIENT_ID = "<CLIENT_ID>"
    CLIENT_SECRET = "<CLIENT_SECRET>"
    AUTHORITY = "https://login.microsoftonline.com/consumers"
    SCOPES = ["User.ReadBasic.All", "email"]

    @staticmethod
    def build_msal_app(cache=None, authority=None):
        return msal.ConfidentialClientApplication(MSLogin.CLIENT_ID,
            authority = authority or MSLogin.AUTHORITY,
            client_credential = MSLogin.CLIENT_SECRET,
            token_cache = cache)

    @staticmethod
    def build_auth_url(authorized_url, authority=None, scopes=None, state=None):
        if scopes is None :
            scopes = MSLogin.SCOPES
        return MSLogin.build_msal_app(authority=authority) \
            .get_authorization_request_url(scopes or [],
                state = state or str(uuid.uuid4()),
                redirect_uri = authorized_url)

    @staticmethod
    def authorized(args, flsk_s, auth_url):
        if args.get('state') != flsk_s.get("state"):
            return 0  # No-OP. Goes back to Index page
        if "error" in args:  # Authentication/Authorization failure
            return args
        if args.get('code'):
            cache = MSLogin._load_cache(flsk_s)
            result = MSLogin.build_msal_app(cache=cache).acquire_token_by_authorization_code(
                args['code'],
                scopes=MSLogin.SCOPES,
                redirect_uri=auth_url)
            if "error" in result:
                return result
            user = result.get("id_token_claims")
            flsk_s.permanent = True
            flsk_s["user"] = MSLogin._make_user(user)
            MSLogin._save_cache(cache, flsk_s)
        return 1

    @staticmethod
    def _load_cache(flsk_s):
        cache = msal.SerializableTokenCache()
        if flsk_s.get("token_cache"):
            # need to turn JSON to string before passing to method
            cache.deserialize(json.dumps(flsk_s["token_cache"]))
        return cache

    @staticmethod
    def _save_cache(cache, flsk_s):
        if cache.has_state_changed:
            # we store actual JSON object (not string) for efficiency
            flsk_s["token_cache"] = json.loads(cache.serialize())

    @staticmethod
    def _get_token_from_cache(flsk_s, scope=None):
        # I don't know why I'd need this
        cache = MSLogin._load_cache(flsk_s)  # This web app maintains one cache per session
        cca = MSLogin.build_msal_app(cache=cache)
        accounts = cca.get_accounts()
        if accounts:  # So all account(s) belong to the current signed-in user
            result = cca.acquire_token_silent(scope, account=accounts[0])
            MSLogin._save_cache(cache, flsk_s)
            return result

    @staticmethod
    def _make_user(user) :
        # See documentation of user attributes
        # https://docs.microsoft.com/en-us/azure/active-directory/develop/id-tokens

        m = re.compile(r'^\s*(.+?)\s+(.*?)\s*$').match(user['name'])
        if m :
            first_name, last_name = m.group(1), m.group(2)
        else :
            first_name, last_name = user['name'], None

        return {
            'provider'   : "microsoft",

            'first_name' : first_name,
            'last_name'  : last_name,
            'email'      : user['email'],
            'exp'        : user['exp'],
            'uid'        : user['oid'],

            # optional/ms-specific
            'preferred_username' : user['preferred_username']
        }
