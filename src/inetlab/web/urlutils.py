import logging

def get_url(env) :
    return env.url

def get_url_OLD (req) :
    ssl = False
    try : # useful in command-line emulation mode

        # it may be that req.unparsed_uri already has full URL
        if req.unparsed_uri.find ( "http://" ) == 0 or \
           req.unparsed_uri.find ( "https://" ) == 0 :
            return req.unparsed_uri

        # first choice is the 'Host' header, second is the
        # hostname in the Apache server configuration.
        host = req.headers_in.get('host', req.server.server_hostname)

        # are we running on an unusual port?
        if not ':' in host:
            port = req.connection.local_addr[1]
            if port != 80 and not ssl:
                host = "%s:%d" % (host, req.connection.local_addr[1])

        return 'http://' + host + req.unparsed_uri

    except AttributeError:

        # returning some junk for command-line emulation...

        return "http://localhost:8000/~user/my/dir/"

def get_parent_url (env) :
    import re
    from urllib.parse import urlparse, urlunparse

    scheme, host, path, pars, query, frag = urlparse ( env.url )

    path = re.sub ( r"/([^/]*)$", "", path );

    return urlunparse ( (scheme, host, path, pars, "", "") )

def urlmodify (url, **params) :
    return urlmodifylow (url, None, **params)

def urlencode_x(query) :
    "New experimental version"
    from urllib.parse import quote_plus
    res = []
    for k,v in query :
        k = quote_plus(str(k))
        if isinstance(v,str) and not all(ord(_)<0x80 for _ in v) :
            v = "".join("%%u%04X" % ord(_) for _ in v)
        else :
            if isinstance(v,str) :
                v = str(v)
            v = quote_plus(v)
        res.append(k + '=' + v)

    return "&".join(res)

def urlmodifylow (url, re_exclude, **params) :
    from urllib.parse import urlparse, urlunparse
    from cgi import parse_qs
    from urllib.parse import urlencode

    # if url is Unicode here, rusults are funny :)
    scheme, host, path, pars, query, frag = urlparse ( str(url) )

    if query : # non-empty
        dpars = parse_qs ( query, True, True )
    else :
        dpars = {}

    #logging.info("url = %r, query = %r, dpars = %r", url, query, dpars)

    exclude_pars = []
    for p,v in dpars.items () :
        if re_exclude is not None and re_exclude.match(p) :
            exclude_pars.append ( p )
            continue
        if type(v) == type([]) and len(v) == 1 and isinstance(v[0],str) :
            dpars[p] = v[0]
        else :
            raise Exception ( "Dubios results of parsing %s: %s -> %s",
                                  url, p, v )

    for p in exclude_pars : del dpars[p]

    #logging.info("dpars = %r", dpars)

    for p,v in params.items () :
        if type(v) == type(False) :
            if v :
                dpars[p] = ""       # passed True (boolean value)
            elif p in dpars :
                del dpars[p]        # passed False
        elif type(v) == type("") :
            dpars[p] = v            # passed string
        elif type(v) == type("") :
            dpars[p] = v.encode('utf-8')  # passed Unicode string
        elif v is None :
            if p in dpars : del dpars[p]  # remove
        else :
            dpars[p] = str(v)       # none of the above

    #logging.info("dpars = %r", dpars)

    return urlunparse ( (scheme, host, path, pars,
                         urlencode ( [(p,v) for p,v in dpars.items()] ),
                                     frag) )

if __name__ == "__main__" :
    print(urlmodify ( "http://localhost:8000/~ignatiev/hebdb/?word=223%3F", vasya='durak', wword='False' ))
