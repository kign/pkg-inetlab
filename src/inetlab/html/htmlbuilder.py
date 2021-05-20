import re

indenttext = True
usexhtml = False

def set_xhtml ( val ) :
    # brief description of XHTML is here:
    # http://www22.brinkster.com/beeandnee/techzone/articles/htmltoxhtml.asp#javascript
    global usexhtml
    old_usexhtml = usexhtml
    usexhtml = val
    return old_usexhtml

def htmlspecialchars(s):
    """Replace special characters '&', '\"', '<' and '>' by SGML entities."""
    # copied from /usr/lib/python2.3/cgi.py
    s = s.replace("&", "&amp;") # Must be done first!
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace('"', "&quot;")
    return s

def TAG ( tag, level = 0, **attrs ) :
    '''tag: HTML tag;
       level (optonal): indentation level;
       attrs: attributes passed as keyed arguments
              special attribute "_" (single underscore) serves for tag content'''

    global indenttext, usexhtml

    if False:
        print("usexhtml = " + repr(usexhtml))
        print("attrs = " + repr(attrs))
        print("level = " + repr(level))

    def rpr (p,v) :
        p = p.replace ( "_", "-" )
        if type(v) == type(True) and v \
               or type(v) == type(None) and v == None:
            if usexhtml :
                return " " + p + '="1"'
            else :
                return " " + p
        elif type(v) == type(True) and not v :
            return ""
        elif type(v) == type("") or type(v) == type(""):
            return ' %s="%s"' % (p,htmlspecialchars(v))
        elif type(v) in [type(0),type(0)] :
            return ' %s="%d"' % (p,v)
        else :
            raise Exception ("TAG(%s), attrib '%s' has type %s" %(tag,p,htmlspecialchars(repr(type(v)))))

    ret = "<" + tag + \
          "".join ([rpr (p,v) for (p,v) in attrs.items() if p[0] != "_"])

    if '_' in attrs:
        igntem= 78
        ret += ">"
        text = attrs['_']
        # text is considered "multiline" when it ends with CR;
        # however, single CR does not make a multi-line text
        # (otherwise, one could't have closing tag on the next like,
        # which is necessery, e.g., for SCRIPT tags)
        try :
            ml = text[-1:] == "\n" and text != "\n"
        except :
            raise Exception ("TAG(%s), text has type %s" %(tag,htmlspecialchars(repr(type(text)))))
        if ml :
            ret = "  " * level + ret + "\n"
        if ml and indenttext :
            text = re.compile ( "^([^ ])", re.MULTILINE ). \
                   sub ("  " * (level + 1) + "\\1", text )
        ret += text
        if ml :
            ret += "  " * level
        if '__NOENDTAG__' not in attrs :
            ret += "</" + tag + ">"
        if ml or text == "\n":
            ret += "\n"
    else :
        if usexhtml and '__NOENDTAG__' in attrs:
            if attrs['__NOENDTAG__'] == 'xml' :
                ret += "/>"
            else :
                ret += " />"
        else :
            ret += ">"
        if level > 0 :
            ret = "  " * level + ret + "\n"

    return ret

def _genTAG ( tagname, level, text, req, attrs, closetag=False ) :
    if text != None :
        attrs['_'] = text
    elif type(level) != type(1) :
        attrs['_'] = level
        level = 0
    for p,v in req.items() :
        attrs[p] = v
    if closetag and '_' not in attrs :
        attrs['__NOENDTAG__'] = True
    return TAG ( tagname, level, **attrs )

def A ( level, href, text=None, **attrs ) :
    return _genTAG ( "A", level, text, {'href': href}, attrs, False )

def IMG ( level, src, **attrs ) :
    return _genTAG ( "IMG", level, None, {'src': src}, attrs, True )

def INPUT ( level, type, name, **attrs ) :
    return _genTAG ( "INPUT", level, None, {'type': type, 'name': name}, attrs, True )

def META ( level, http_equiv, content, **attrs ) :
    return _genTAG ( "META", level, None,
                     {'http-equiv': http_equiv, 'content': content},
                     attrs, True )

def TEXTAREA ( level, name, **attrs ) :
    return TAG ( "textarea", level=level, name=name, **attrs )

def SCRIPT ( level, language, **attrs ) :
    return TAG ( "SCRIPT", level=level, language=language, **attrs )

def LINK ( level, rel, type, href, **attrs ) :
    return _genTAG ( "LINK", level, None, {'rel': rel, 'type': type, 'href': href},
                     attrs, True )

def H1 ( level, text=None, **attrs ) :
    return _genTAG ( "H1", level, text, {}, attrs, False )

def H2 ( level, text=None, **attrs ) :
    return _genTAG ( "H2", level, text, {}, attrs, False )

def H3 ( level, text=None, **attrs ) :
    return _genTAG ( "H3", level, text, {}, attrs, False )

def H4 ( level, text=None, **attrs ) :
    return _genTAG ( "H4", level, text, {}, attrs, False )

# def HR ( level, **attrs ) :
#    return TAG ( "HR", level=level, **attrs )

def HR ( level=0, **attrs ) :
    return _genTAG ( "HR", level, None, {}, attrs, True )

def BLOCKQUOTE ( level, **attrs ) :
    return TAG ( "BLOCKQUOTE", level=level, **attrs )

def B ( level, text=None, **attrs ) :
    return _genTAG ( "B", level, text, {}, attrs, False )

def I ( level, text=None, **attrs ) :
    return _genTAG ( "I", level, text, {}, attrs, False )

def OL ( level, **attrs ) :
    return TAG ( "OL", level=level, **attrs )

def LI ( level=0, text=None, **attrs ) :
    return _genTAG ( "LI", level, text, {}, attrs, True )

# def LI ( level, **attrs ) :
#    return TAG ( "LI", level=level, **attrs )

def UL ( level=0, text=None, **attrs ) :
    return _genTAG ( "UL", level, text, {}, attrs )


# def UL ( level, **attrs ) :
#    return TAG ( "UL", level=level, **attrs )



def DIV ( level, text=None, **attrs ) :
    return _genTAG ( "DIV", level, text, {}, attrs, False )

def SPAN ( level, style, text=None, **attrs ) :
    return _genTAG ( "SPAN", level, text, {'style': style}, attrs, False )

def P ( level=0, text=None, **attrs ) :
    return _genTAG ( "P", level, text, {}, attrs )

def BR ( level=0, text=None, **attrs ) :
    return _genTAG ( "BR", level, text, {}, attrs, True )

def HEAD ( level=0, text=None, **attrs ) :
    return _genTAG ( "HEAD", level, text, {}, attrs )

def TITLE ( level=0, text=None, **attrs ) :
    return _genTAG ( "TITLE", level, text, {}, attrs )

def FONT ( level, **attrs ) :
    return TAG ( "FONT", level=level, **attrs )

def TABLE ( level, **attrs ) :
    return TAG ( "TABLE", level=level, **attrs )

def TR ( level, text=None, **attrs ) :
    return _genTAG ( "TR", level, text, {}, attrs )

def TD ( level, text=None, **attrs ) :
    return _genTAG ( "TD", level, text, {}, attrs )

def TBODY ( level, text=None, **attrs ) :
    return _genTAG ( "TBODY", level, text, {}, attrs )

def TH ( level, text=None, **attrs ) :
    return _genTAG ( "TH", level, text, {}, attrs )

def BODY ( level=0, text=None, **attrs ) :
    return _genTAG ( "BODY", level, text, {}, attrs )

def HTML ( level=0, **attrs ) :
    return TAG ( "HTML", level=level, **attrs )

def FORM ( level, name, method="get", action="", text=None, **attrs ) :
    return _genTAG ( "FORM", level, text,
                     {'name': name, 'method': method, 'action': action},
                     attrs, False )

def LABEL ( level, for_, text, **attrs ) :
    return _genTAG ("LABEL", level, text, {'for': for_}, attrs, False)

# def FORM ( level, name, method, action, **attrs ) :
#    return TAG ( "FORM", level=level, name=name, method=method, action=action, **attrs )

def JAVASCRIPT ( text ) :
    global indenttext

    old_it = indenttext
    indenttext = False

    if text[-1:] != "\n" : text += "\n"
    if text[0] == "\n"   : text = text[1:]
    if usexhtml :
#       text =  "<!--\n<![CDATA[\n" + text +  "]]>\n//-->\n"
        text =  "<!--\n" + text +  "//-->\n"
    res = TAG ( "SCRIPT", 0, type='text/javascript', _=text )

    indenttext = old_it
    return res

if __name__ == "__main__" :
    errno, errstr = 100, "error '100'"
    p = P ( _="Error %d: text<br>\n" % (100,) )
    print(P ( style="font-weight: bold; color: red;",
        _="Error %d: %s<br>\n" % ( errno, errstr ) ) + "\n")
    print(P ( "Seems like you have to create the " +
               "database or set up the permissions" ) + "\n")

    print(INPUT ( 3, "button", "&word", size="50", enabled=True,
            _= """Split string by the occurrences of pattern. If capturing parentheses
are used in pattern, then the text of all groups in the pattern are
also returned as part of the resulting list. If maxsplit is nonzero,
at most maxsplit splits occur, and the remainder of the string is
returned as the final element of the list. (Incompatibility note: in
the original Python 1.5 release, maxsplit was ignored. This has been
fixed in later releases
"""
            ))

    print(HEAD (
        TAG ( "META",
              http_equiv="Content-Type",
              content="text/html; CHARSET=UTF-8" ) + "\n" +
        TITLE ( "HEBDB interface: first step" )  + "\n" ))

