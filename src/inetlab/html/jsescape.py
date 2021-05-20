# Source: http://mail.python.org/pipermail/web-sig/2005-April/001298.html
# Author: Shannon -jj Behrens
# License: Public domain

def javaScriptEscape(s):
    """Prepare ``s`` for use in a JavaScript quoted string.

    Both ``"`` and ``'`` are escaped, so you can use the return value in
    either single or double quotes.

    """
    if not isinstance(s, str):
        s = str(s)                  # Never call str on unicode.
    s = "\"'" + s                   # Force repr to use single quotes.
    s = repr(s)
    start, end = 4, -1              # Strip outer quotes and added quotes.
    if s.startswith("u"):           # JS strings are implicitly unicode.
        start += 1
    s = s[start:end]                     
    s = s.replace('"', '\\"')       # Escape double quotes too.
    return s

def javaScriptQuote(s):
    """Escape ``s`` and wrap it in single quotes."""
    return "'%s'" % javaScriptEscape(s)


# Do some testing.
if __name__ == '__main__':
    for (k, v) in [("", ""), 
                   ("a", "a"),
                   ("\t", "\\t"),
                   ("\n", "\\n"),
                   ("'", "\\'"),
                   ('"', '\\"'),
                   ("\377", "\\xff"),
                   ("\xff", "\\xff"),
                   ("\u1234", "\\u1234")]:
        escaped = javaScriptEscape(k)
        if escaped != v:
            raise AssertionError(
                "javaScriptEscape(%s) led to %s instead of %s" % 
                (repr(k), repr(escaped), repr(v)))
    assert javaScriptQuote("foo\n") == "'foo\\n'"
