import sys, logging, os, os.path, pickle, json
from getpass import getpass

# python3 -m pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
# GMail API
# https://developers.google.com/gmail/api/
# https://developers.google.com/gmail/api/guides
# https://developers.google.com/gmail/api/reference/rest/v1/users.messages/send
# https://developers.google.com/gmail/api/quickstart/python
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# python3 -m pip install --upgrade pycrypto
# pycripto intro
# https://www.dlitz.net/software/pycrypto/doc/#crypto-cipher-encryption-algorithms
from Crypto.Cipher import ARC4

def login(permissions) :
    ftoken = os.path.expanduser("~/.google_api_token.pickle")
    fclicoen = os.path.expanduser("~/.client_secret.json.enc")

    creds = None
    try :
        with open(ftoken, 'rb') as fh :
            tk = pickle.load(fh)
            if sorted(tk['permissions']) == sorted(permissions) :
                creds = tk['creds']
    except FileNotFoundError :
        pass

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else :
            if not os.path.exists(fclicoen) :
                print("Client config file not found\n"
                      "Please download it from \n"
                      "https://console.developers.google.com/apis/api/gmail.googleapis.com/credentials?project=pro-mgr\n"
                      " (Note: use or create credentials for Desktop app")
                fclico = input("Enter full path to downloaded file > ")
                with open(fclico, 'rb') as fh :
                    plain = fh.read()
                # print(repr(plain))
                while True :
                    p1 = getpass("Make password for client config > ")
                    p2 = getpass("Repeat ........................ > ")
                    if p1 == p2 : break
                    print("ERROR: Passwords don't match, try again")
                with open(fclicoen, "wb") as fh :
                    # print(repr(ARC4.new(p1).encrypt(plain)))
                    fh.write(ARC4.new(p1.encode("utf-8")).encrypt(plain))
                yes = input("Information encrypted and saved, remove original [Y] ? ")
                if yes.lower() not in ['n', 'no'] :
                    os.remove(fclico)

        with open(fclicoen, 'rb') as fh :
            enc = fh.read()

        try :
            passwd = getpass("Enter password for client config (Ctrl-C to quit) > ")
        except KeyboardInterrupt as err:
            print("\nCtrl-C, quiting")
            exit(0)

        try :
            clico = json.loads(ARC4.new(passwd.encode("utf8")).decrypt(enc).decode('utf-8'))
        except Exception as err:
            print("ERROR, probably password is wrong\n"
                  "(Original error: " + str(err) + ")", file=sys.stderr)
            exit(1)

        logging.debug("Client config: %s", clico)
        flow = InstalledAppFlow.from_client_config(clico,
                ['https://www.googleapis.com/auth/gmail.' + p for p in permissions])
        creds = flow.run_local_server(port=0)

        with open(ftoken, 'wb') as fh:
            pickle.dump({'creds' : creds, 'permissions' : permissions}, fh)

    # cache_discovery=False is to avoid ugly warnings, hint found at
    # https://github.com/googleapis/google-api-python-client/issues/325#issuecomment-274349841
    return build('gmail', 'v1', credentials=creds, cache_discovery=False)


if __name__ == "__main__" :
    logging.basicConfig(format="%(asctime)s.%(msecs)03d %(filename)s:%(lineno)d %(message)s",
                        level=logging.DEBUG, datefmt='%H:%M:%S')

    service = login(['readonly'])

    logging.info("Logged in successfully")
    # Call the Gmail API
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(label['name'])
