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

### inputnums.py

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

## inetlab.html

Everything related to HTML :smiley:






