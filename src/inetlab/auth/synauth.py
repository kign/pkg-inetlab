import os, time, logging
from flask import session as flsk_s, request, redirect, url_for, render_template

from .synlogin import MSLogin, GLogin

EP_USER = "user"
EP_HOME = "home"

def setup_endpoints(home, user) :
    global EP_USER, EP_HOME
    EP_USER = user
    EP_HOME = home

# app.add_url_rule('/auth', 'authorized', view_func=auth.authorized, methods=['GET'])
def authorized():
    """
    This is for Microsoft authentication, for now
    """

    # MSLogin.CLIENT_ID = os.environ.get('MS_CLIENT_ID')
    # MSLogin.CLIENT_SECRET = os.environ.get('MS_CLIENT_SECRET')

    # This call could return one of:
    # - dictionary with 'error' key (authentication error)
    # - 1  (login successful)
    # - 0  (inconsistent call, try again)

    res = MSLogin.authorized(request.args, flsk_s,
                    url_for("authorized", _external=True))
    try :
        res['error']
    except TypeError :
        if res == 0 :
            return redirect(url_for(EP_HOME))
        else :
            return redirect(url_for(EP_USER))

    return render_template("lib_auth_error.html", result=res)


# app.add_url_rule('/token', 'token', view_func=auth.authorized, methods=['POST'])
def token():
    """
    This is for Google authentication, for now
    """

    try:
        # GLogin.CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
        res = GLogin.token(flsk_s, request.form['idtoken'])
        logging.info("Returned %s from token()", res)
        return res
    except (ValueError, KeyError) as err:
        # Invalid token
        logging.info("token() error %s", err)

        return render_template("lib_auth_error.html", result={
            'error' : 'Google Authentication Error',
            'error_description' : str(err)
            })

# app.add_url_rule('/logout', 'logout', view_func=auth.logout, methods=['GET'])
def logout():
    provider = (flsk_s.get('user') or {}).get('provider')
    flsk_s.clear()  # Wipe out user and its token cache from session

    if provider == 'microsoft' :
        return redirect(  # Also logout from your tenant's web session
            MSLogin.AUTHORITY + "/oauth2/v2.0/logout" +
            "?post_logout_redirect_uri=" + url_for(EP_HOME, _external=True))
    else :
        return redirect(url_for(EP_HOME))
