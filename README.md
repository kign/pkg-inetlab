# pkg-inetlab
Python helper libraries for Web/GAE/Flask, HTML manipulation and command line tools

This package combines many Python utilities I accumulated over the years and used in some of my projects. 
Some are outdated or serve some narrow purpose, other not quite complete. Use at your own risk!

Below if a brief description of the nodules included

* [pkg-inetlab](#pkg-inetlab)
   * [inetlab.auth](#inetlabauth)
   * [inetlab.cli](#inetlabcli)
      * [colorterm](#colorterm)
      * [genformatter](#genformatter)
      * [inputnums.py](#inputnumspy)
   * [inetlab.html](#inetlabhtml)

## inetlab.auth

Utilities to be used in a `flask` project to implement syndicated login (at this time, Microsoft and Google logins are supported).

There is a working usage example [available here](https://github.com/kign/url-shortener). Briefly, follow these steps:

1. Setup environment:

```python
from inetlab.auth import synauth, synlogin

synauth.setup_endpoints('home', 'user')
synlogin.setup_partners(google_client_id=os.getenv('GOOGLE_CLIENT_ID'),
                        microsoft_client_id=os.getenv('MS_CLIENT_ID'),
                        microsoft_client_secret=os.getenv('MS_CLIENT_SECRET'))

```

2. Create at least two main and three service URL endpoints

```
/home: <your home page>
/user: <landing page after authentication>
...............................
/auth: synauth.authoriz
/token: synauth.token
/logout: synauth.logout
```

3. On "log in" button click, redirect to a template ([like this](https://github.com/kign/url-shortener/blob/main/external/login.html)) with these parameters:

```python
from flask import session, url_for, render_template

state = str(uuid.uuid4())
sesson['state'] = state

render_template('home.html',
   ms_auth_url=synlogin.MSLogin.build_auth_url(
       authorized_url=url_for("authorized", _external=True),
       state=state),
   redirect_succ=url_for('home'),
   google_client_id=synlogin.GLogin.CLIENT_ID)
```

## inetlab.cli

Some utilities commonly used in command line Python scripts

### colorterm

This module provides (1) a convenient wrapper for `Terminal` class from [blessings](https://pypi.org/project/blessings/) module, 
and (2) a `blessings`-independent utility `add_coloring_to_emit_ansi` to use in conjunction with `logging`, like this:

```python
import logging
from inetlab.cli.colorterm import add_coloring_to_emit_ansi

logging.basicConfig(format="%(asctime)s.%(msecs)03d %(filename)s:%(lineno)d %(message)s",
                    level=logging.DEBUG, datefmt='%H:%M:%S')
logging.StreamHandler.emit = add_coloring_to_emit_ansi(logging.StreamHandler.emit)
```

### genformatter

Output tabular-formatted text, e.g.

```python
from inetlab.cli.genformatter import GenericFormatter
out = GenericFormatter("aligned,width=30")
out.writeheader(["x", "x^2", "x^3"])
for x in range(1,10) :
    out.writerow([x, x**2, x**3])
out.close ()
```

### inputnums

`input_numbers` allows one to make multiple selection from number of given choices, allowing for intervals (possible overlapping) 
and "except <...>" syntax.

```python
def input_numbers(prompt, n, flat: bool, extend=None) :
    """User can input any number or ranges between 1 and n, e.g.: 1,5,8-11

    It is also possible to use "except ..." syntax, e.g. "except 10, 15"

    Parameters:

        - flat (bool, default=False)   return flat list of numbers, not list of intervals

        - extend(array of strings, default=[])  provide additional list of valid entries, in addition to
            o numbers and intervalis
            o 'quit', 'all' or 'none' (case insensitive and could be shortened to 1-st letter)
    """
```

## inetlab.mail.xmail

General functionality for sending emails. Supports embedded images and sending via SMTP or GMail API.

```python
def send(subject, html, channel,
         send_from=None,
         send_to=None,
         send_cc=None,
         images=None,
         invoke_premailer=False,
         dry_run=None):
    """
    :param subject:     Email subject
    :param html:        Email content
    :param channel:     Email delivery channel, or save to file option (file=...)
    :param send_from:   Sender's email
    :param send_to:     Recipients' email(s). Could be array (see below) or string. If string, module pyparsing required
    :param send_cc:     CC email(s), comment above for send_to applies
    :param images:      Lost of embedded images
    :param invoke_premailer: apply Python module premailer tp HTML
    :param dry_run:     Dry run (nothing will be sent if True)
    :return: *Nothing*
    """
```
Usage example:

```python
from inetlab.mail.xmail import send
import random

send(f"Testing email using inetlab.mail, random ID: {random.randrange(10 ** 6, 10 ** 7)}",
            f"""\
Hi!<br />
This is a test of <code>users.messages.send</code>.<br />
Below we embed image <b>{sample_file}</b>, check it out:<br />
<img src="cid:sample_file" /> <br />
Hope it worked!
""",
        '<username>:<password>>@smtp.some.server.com:465',
        send_from='my_email@example.com',
        send_to='John Doe <john.doe@example.org>',
        images={'sample_file': open(sample_file, 'rb').read()})
```

NOTES:

 * We don't support attachments (not that it's difficult to add), only embedded images. 
 * If you want to send emails from your GMail account, you have two options: (1) using SMTP which requires you to explicitly go to [this page](https://myaccount.google.com/lesssecureapps) allow access to "less secure" apps (and then it'll periodically revert to default, so once you see your SMTP authentication failing you'll need to do it again); or (2) use official GMail API, which requires you to register your "app" with Google's [GCloud](https://console.cloud.google.com/) and to authenticate your account in browser more or less every time you'll need to use it (thus preventing any background use).
 * You can specify addressees as an array `[(name1, address1),(name2, address2),...,(nameN, addressN)]` (any `name` could be `None`), or as comma-separated string `name1 <address1>, name2 <address2>,...` (name could have commans if quoted). If using later option, we'll use [pyparsing](https://pypi.org/project/pyparsing/) to parse.

## inetlab.html

Mostly outdated utilities for parsing and generating HTML. 

### html2xml

My preferred tool for parsing badly formatted HTML pages by translating them to proper XML fixing 
parsing issues as they occur. By no means universal or bullet-proof, but helps to quickly make a 
customized parser for a specific site.

### htmlbuilder

In the old days, used this handy library to easily generate HTML tags in Python code.
No longer useful.

### htmladdons

Similarly to `htmlbuilder`, generating more advanced HTML code. No longer useful.

### inputlib

Similarly to `htmlbuilder`, generating HTML forms. No longer useful.

### jsescape

Old utility for escaping strings in JavaScript code generated in Python. No longer useful.







