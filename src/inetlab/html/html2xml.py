################ FAST START ################

"""
req = urllib2.Request('http://www.ptc.com/')
res = urllib2.urlopen(req)
xdom = xml.dom.minidom.parse (html2xml.Parser (res.read(), feed_unicode = True))
res.close ()
print(re.sub ( "(\n\s*)+\n", "\n", xdom.toprettyxml("  ").encode ( "utf-8" ) ))
"""

################ FULL DETAILS ##############


# Initial implementation might look like that:

# import html2xml
#
# def my_log(self,cls,lineno,msg) :
#     raise RuntimeError("[%s:%d] %s" % (cls,lineno,msg))
# html2xml.Parser.log = my_log
#
# html_parser = html2xml.Parser (
#     open ( "ign.html"),
#     feed_unicode = True,
#     dbg_file_xml = "/tmp/debug_in.xml",
#     dbg_file_html = "/tmp/debughtml.txt" )
#
# xdom = xml.dom.minidom.parse ( html_parser )
# dbg_out = open ( "/tmp/debug_out.xml", "w" )
# dbg_out.write ( re.sub ( "(\n\s*)+\n", "\n", xdom.toprettyxml("  ").encode ( "utf-8" ) ) )
# dbg_out.write ( """
# <!-- Local """ + """Variables: -->
# <!-- coding:utf-8 -->
# <!-- End: -->
# """ )
#
# Update[June 2020]: In Python 3, all strings are Unicode.
# Therefore, feed_unicode is no longer supported.
#
# Note on Unicode[January, 2013]: there is a wide-spread confusion in
# Python 2.X regarding which library functions can work with raw data,
# Unicode, or both. There are many such examples, but HTMLParser could
# be the best one, yet. For nearly 8 years (!) I have been using it in
# 'raw' mode, and only now encountered a use case where it fails to
# properly process raw 8-bit data: namely, when TAG attribute has some
# non-ASCII characters AND entities (such as &quot; or any other). In
# this case apparently HTMLParser invokes function self.unescape(),
# which is not 8-bit safe. When same data is passed as Unicode, it seems
# to work fine.
#
# Therefore, for now I am adding an argument feed_unicode which defaults
# to False (compatibility mode). New implementation should use True; we
# may switch default value to True , but we need to make sure it does
# not bring more problems.
#
# 1. When you get unicode exception, check encoding of your input and if warranted
#    pass argument enc_in = "XXXX" to html2xml.Parser
# 2. If my_log raises exceptions, review HTML input, and if everything
#    as it should be, add filter to my_log or remove this function completely
# 3. If HTML parser fails or generated XML is bad, created derived class
#    and override fixhtmlline()
# 4. If XML parser generated errors, run xml.dom.minidom.parse("/tmp/debug_in.xml")
#    in separate python session, review errors and trace them nack to original HTML
# 5. When working with XML DOM, refer to /tmp/debug_out.xml
# 6. When everything works, remove/comment out last 2 args to html2xml.Parser() and dbg_out block
#
#    *** IMPORTANT NOTE REGARDING EMBEDDED SCRIPTS ***
#
# Properly parsing HTML files with embedded (Java)scripts is often
# challenging, especially so as these scripts often try to alter HTML
# code and so contain some row HTML text which confuses the parser.
#
# The parser as implemented here does not attempt to solve this problem
# for you; it has an option to disregard any content of "SCRIPT" tag
# (which is a default behaviour) or turn it into CDATA, but if python's
# HTMLParser chokes on your script content, there is nothing we can do
# to help.
#
# However, we provide a helper function Parser.normalize_scripts() which
# you can use on application side to address the problem. There are
# three ways it can be done.
#
# 1. If you don't need content of <script> tags at all, you can just
# strip them completely from incoming HTML text. Use 'method'
# Parser.NORM_REMOVE.
#
# 2. Few people know about that, but according to HTML standard <script>
# content might not contain any end tax syntax ( </something ), in any
# form, including inside a string; enclosing the whole script into HTML
# comments does not make the script parsable! (it used to be popular to
# avoid problems with old browsers which didn't know about <script> tag
# at all). Thus, you can use 'method' = Parser.NORM_SPLIT_ENDTAGS to
# re-write these endtags to preserve the original meaning and make
# script conformant.
#
# If you do that, make sure to set 'skip_scripts' to False
#
# 3. Or, alternatively, you can still try to treat script content as
# HTML comment. Use 'method' = Parser.NORM_WITH_COMMENTS and also
# exclude 'script' tag from HTMLParser.CDATA_CONTENT_ELEMENTS list, like
# that:
#
# self.CDATA_CONTENT_ELEMENTS = list(set(self.CDATA_CONTENT_ELEMENTS) - set(["script","SCRIPT"]))
#
# ( As of Python 2.6, <<HTMLParser.CDATA_CONTENT_ELEMENTS = ("script", "style")>> )
#
# Make sure to also set *both* 'skip_scripts' and 'skip_comments' to False
#  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *  *


# Python libs
import re, html.parser, logging
from io import StringIO

from . import htmlbuilder

rescript = re.compile(r"<script\s*(.*?)>\s*(.*?)\s*</script>", re.I | re.S)
recontent = re.compile(r'^<!--\n.+//-->$', re.S)
reendtag = re.compile(r'</([a-z]+)>', re.I)
retagname = re.compile(r'^[a-z0-9_0]+$', re.I)

AUTO_CLOSE_TAG_LIST = ["link", "meta", "input", "img", "br", "area", "hr"]

class Parser(html.parser.HTMLParser) :
    # implementing push => pull gateway
    def __init__ (self, reader_in,
                  dbg_file_xml=None, dbg_file_html=None, wrappertag=None,
                  dbg_file_structure=None
                  # enc_in = "utf-8",
                  # feed_unicode = False # for compatibility; use True in new code
                  #                      # see comment above
                  ) :
        html.parser.HTMLParser.__init__ (self)
        self.stack = []

        if isinstance(reader_in, str) :
            self.reader = StringIO(reader_in)
        # if type(reader_in) == type("") :
        #     self.reader = StringIO(reader_in.encode("utf-8"))
        # elif type(reader_in) == type("") :
        #     self.reader = StringIO(reader_in)
        else :
            self.reader = reader_in

        self.buffer = []
        self.tbuffer = 0
        self.eof = False
        self.dbgxmlout = None
        self.dbglineno = 0
        # self.feed_unicode = feed_unicode
        if dbg_file_xml is not None :
            self.dbgxmlout = open ( dbg_file_xml, "w" )
        self.dbghtmlout = None
        if dbg_file_html is not None :
            self.dbghtmlout = open ( dbg_file_html, "w" )
        self.dbgstructout = None
        if dbg_file_structure is not None :
            self.dbgstructout = open ( dbg_file_structure, "w" )
            self.dbgstructout.write(";;; -*- tab-width: 3 -*-\n")

        self.enc_out = "utf-8"
        # self.enc_in = enc_in
        self.dbg_enc_out = self.enc_out

        self.old_xhtml = htmlbuilder.set_xhtml(True)

        # these are auto-closed on another tag like that or any closure </tag>
        self.p_like_tags = [ 'p', 'li' ]
        self.skip_comments = True
        self.skip_scripts = True

#        self._write ( '<?xml version="1.0" encoding="UTF-8"?>\n' )
        self._write ( '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n' )
        self.wrappertag = wrappertag
        if self.wrappertag is not None :
            self._write("<%s>" % self.wrappertag)

        self.script_content = []

#        self.CDATA_CONTENT_ELEMENTS = []

#        self.dbg_count = 0

    # to be overriden if need to fix HTML markup
    def fixhtmlline (self, line) :
        return line

    # to be overriden to print custom messages or raise exception
    def log(self,cls,lineno,msg) :
        pass

    def _log(self,cls,msg) :
        self.log (cls,self.dbglineno,msg)

    def _fatal(self, cls, msg) :
        raise RuntimeError("[%s:%d] %s" % ("FATAL:" + cls,self.dbglineno,msg))

    def pull(self):
        if self.eof: return
        line = self.reader.readline()
        self.dbglineno += 1
        if not line:
            self.eof = True
            self.reader.close()
            self.close()
            if self.dbghtmlout  : self.dbghtmlout.close ()
            if self.dbgstructout: self.dbgstructout.close()
            if self.wrappertag is not None :
                self._write("</%s>" % self.wrappertag)
            return

        line = self.fixhtmlline(line)

        # if self.feed_unicode :
        #     try :
        #         uline = str(line, self.enc_in)
        #     except UnicodeDecodeError as err :
        #         self._fatal("ENCODING", "encoding: %r, err: %r" % (self.enc_in, err))
        #     self.feed (uline)
        # else :
        #     self.feed (line)

        self.feed (line)

        # try :
        #     self.feed ( unicode(line, self.enc_in) )
        # except Exception, err :
        #     self._fatal ("HTMLERROR", "feed(%r): %s" % (line,err) )

    def read ( self, req = None ) :
        res = []
        tres = 0

        while not self.eof  and  (req is None or self.tbuffer < req) :
            self.pull ()

        if req is None :
            req = self.tbuffer + 1

        while tres < req and self.buffer:
            f = self.buffer[0]
            if tres + len(f) <= req :
                res.append(self.buffer.pop(0))
                self.tbuffer -= len(f)
                tres         += len(f)
            else:
                res.append(f[0:(req - tres)])
                self.buffer[0] = f[(req - tres):]
                self.tbuffer -= req - tres
                tres = req  # tres += req - tres

        if not res or not res[0]: return ""

        if self.dbgxmlout:
            self.dbgxmlout.write("".join(res))
            if self.eof and tres < req:
                self.dbgxmlout.write("""
<!-- Local """ + """Variables: -->
<!-- coding:%s -->
<!-- End: -->
""" % self.dbg_enc_out)
                self.dbgxmlout.close()

#        logging.info (repr(res))
#        self.dbg_count += 1
#        logging.info ("dbg_count = %d" % self.dbg_count)
#        logging.info (repr("".join ( res )[:200]))

#        jj = 685
#        logging.info("res[%d] = %r" % (jj,res[jj]))
#        for ii in range(len(res)) :
#            x = "".join(res[:ii])
#            logging.info("ii = %d (out of %d) OK" % (ii, len(res)))
        return "".join ( res ).encode ( self.enc_out )

    def _write(self, s):
        self.buffer.append(s)
        self.tbuffer += len(s)

    def handle_startendtag(self, tag, attrs):
        if self.dbgstructout:
            self.dbgstructout.write("\t" * len(self.stack) + "<%s/>   %d\n" % (tag, self.dbglineno))
        self.handle_starttag(tag, attrs, True)

    def handle_starttag(self, tag, attrs, closes=False):
        if not retagname.match(tag):
            self._log("ERR:BADTAGNAME", "Tag '%s' is invalid" % tag)
            return
        if not closes and self.dbgstructout :
            self.dbgstructout.write ("\t" * len(self.stack) + "<%s>   %d\n" % (tag, self.dbglineno))

        if self.dbghtmlout:
            self.dbghtmlout.write("<" + tag + ">\n")

        if tag in self.p_like_tags and tag in self.stack :
            self._log("ERR:AUTOCLOSURE",
                       "Tag '%s' was auto-closed upon encountering another <%s>" % (tag,tag) )
            self.handle_endtag(tag)

        if tag in AUTO_CLOSE_TAG_LIST:
            closes = True
        # level = len(self.stack)
        if not closes:
            self.stack += [tag]

        d_a = {}
        for p, v in attrs:
            # I haven't got a clue where this possibly comes from
            if p in ("`", '"') or '0' <= p[0] <= '9':
                continue

            d_a[p] = v
            # if type(v) == type("") :
            #     d_a[p] = str(v,self.enc_in) # unicode(v,"windows-1255")
            # else :
            #     d_a[p] = v

        if closes:
            d_a['__NOENDTAG__'] = True
        if tag.lower() == "html":
            d_a['xmlns'] = "http://www.w3.org/1999/xhtml"
        elif self.dbgxmlout: d_a['lineno'] = self.dbglineno

        if tag.lower() == "meta" and \
                "http-equiv" in [x.lower() for x in list(d_a.keys())] and \
                d_a[[x for x in list(d_a.keys()) if x.lower() == "http-equiv"][0]].lower() == "content-type":
            d_a[[x for x in list(d_a.keys()) if x.lower() == "content"][0]] = \
                "text/html; charset=%s" % self.enc_out

#        self._write ("  "*level + TAG ( tag, 0, ** d_a ) + "\n")
        self._write (htmlbuilder.TAG(tag, 0, ** d_a))

    def handle_endtag(self, tag):
        if not retagname.match(tag):
            self._log("ERR:BADTAGNAME", "Tag '%s' is invalid" % tag)
            return

        if self.dbgstructout:
            self.dbgstructout.write("\t" * (len(self.stack) - 1) + "</%s>   %d\n"
                                    % (tag, self.dbglineno))

        # Fixing problem#1: attempt to close never opened tag
        if tag not in self.stack :
            self._log ("ERR:NOTOPENED", "Tag '%s' was never opened" % tag )
            return

        if tag == "script" and self.script_content :
#            self._write ( "<![CDATA[" + unicode("".join(self.script_content), self.enc_out) + "]]>" )
            self._write ( "<![CDATA[" + "".join(self.script_content) + "]]>" )
            self.script_content = []


        # fixing problem #4: have to close all unclosed tags
        iter = 0
        while True:
            iter += 1
            st_tag = self.stack.pop ()
#            self._write ("  "*len(self.stack) + "</" + st_tag + ">" + "\n")
#           if self.dbgxmlout : self._write ( "<!-- lineno: %d, iter = %d, tag = %s, st_tag = %s -->" %
#                                              (self.dbglineno, iter, tag, st_tag) )
            self._write ( "</" + st_tag + ">" )
            if tag == st_tag :
                break
            elif st_tag in self.p_like_tags :
                self._log ("ERR:AUTOCLOSURE",
                           "'P-like' Tag '%s' was auto-closed upon encountering '</%s>'" % (st_tag,tag) )
            else :
                self._log ("ERR:NOTCLOSEDINT", "Closing tag %s before processing close tag %s" %
                              (st_tag, tag))

    def handle_data  ( self, data ) :
        # E.g. blank line in the beginning of the file
        if self.dbghtmlout :
            #self.dbghtmlout.write ( data.encode ( self.enc_in ) + "\n" )
            self.dbghtmlout.write ( data + "\n" )

        if self.stack and self.stack[-1] == "script":
            if not self.skip_scripts :
                self.script_content.append(data)
        else :
            self._write (htmlbuilder.htmlspecialchars(data))
            # if type(data) == type("") :
            #     self._write (htmlbuilder.htmlspecialchars(data))
            # else :
            #     self._write (str ( htmlbuilder.htmlspecialchars(data), self.enc_in ))

    def handle_charref (self, num) :
        if num[0] == 'x' :
            val = int(num[1:], 16)
        else :
            val = int(num)

        # http://www.w3.org/TR/REC-xml/#charsets
        # #x9 | #xA | #xD | [#x20-#xD7FF] | [#xE000-#xFFFD] | [#x10000-#x10FFFF]

        ok = val == 0x9                 or\
             val == 0xA                 or\
             val == 0xD                 or\
             0x20    <= val <= 0xD7FF   or\
             0xE000  <= val <= 0xFFFD   or\
             0x10000 <= val <= 0x10FFFF

        if ok :
            self._write ( "&#" + num + ";" )
            if self.dbghtmlout :
                self.dbghtmlout.write ( "&#" + num + ";"  + "\n" )
        else :
            self._write ( "&#" + "xFFFD" + ";" )
            if self.dbghtmlout :
                self.dbghtmlout.write ( "&#" + num + ";"  + " [invalid]\n" )


    def handle_entityref (self, name) :
        self._write ( "&" + name + ";" )
        if self.dbghtmlout :
            self.dbghtmlout.write ( "&" + name + ";" + "\n" )

    def handle_comment(self,data) :
        if not self.skip_comments :
            self._write ( "<!--" + str(data,self.enc_out) + "-->" )

    def handle_decl(self,decl) :
#       <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN" >
        if self.dbghtmlout :
            self.dbghtmlout.write ( decl + "\n" )
        return
        self._write ( decl )

    def handle_pi (self, pi ) :
        pass

    def close (self) :
        if ( self.stack != [] ) :
            self._log ( "ERR:NOTCLOSEDEND",
                        "Input exhausted, but %d tag(s) remain to be closed: [%s]" %
                       (len(self.stack), ";".join(self.stack)) )
            for ii in range(len(self.stack)-1,-1,-1) :
                self.handle_endtag ( self.stack[ii] )

        htmlbuilder.set_xhtml(self.old_xhtml)


    NORM_WITH_COMMENTS = "NORM_WITH_COMMENTS"
    NORM_SPLIT_ENDTAGS = "NORM_SPLIT_ENDTAGS"
    NORM_REMOVE        = "NORM_REMOVE"

    @staticmethod
    def normalize_scripts(html_in, method) :
        """This is an auxiliary utility to "normalize" <script>'s in HTML text
        It is needed because scripts with embedded HTML could break Python HTML parser.
        Obviously, this solution is very crude and may yield bad results, but
        in all normal circumstances it works and "properly" escapes scripts so that
        page becomes "valid" (from the point of view of Python parser, of course)
        and is equivalent to the original.

        Notes: 1. Obviously, it is a lot easier to just strip all scripts :

        html_out = re.compile(r"<script.+?</script>?", re.I | re.S).sub('',html_in)

        Current solution however allows to *preserve* scripts in case they are needed.

        2. Since HTML parser sees "normalized" scripts as HTML comments, in order to
           preserve them it is necessary to set self.skip_comments to False
           (True by default)

        3. In order to use this utility, one must retrieve *complete* input stream,
           transform it and then pass to parser.
        """

        assert method in [Parser.NORM_WITH_COMMENTS,
                          Parser.NORM_SPLIT_ENDTAGS,
                          Parser.NORM_REMOVE]

        def script_replace(m):
            if method == Parser.NORM_REMOVE:
                return ""

            pars = m.group(1)
            if pars: pars = " " + pars
            content = m.group(2)

            if method == Parser.NORM_SPLIT_ENDTAGS:
                if content == "" or not reendtag.search(content):
                    return m.group(0)
                content = reendtag.sub(r"<' + '/\1>", content)
                return '<script%s>%s</script>' % (pars, content)

            elif method == Parser.NORM_WITH_COMMENTS:
                if content == "" or recontent.match(content):
                    return m.group(0)
                content = content.replace(' -->', ' ==>').replace('<!--', '<!==')
                return '<script%s><!--\n%s\n//-->\n</script>' % (pars, content)

#            return "<script%s><!--\n<![CDATA[\n%s]]>\n//-->\n</script>" % (pars, content)
#            return '\n<!--\n%s\n//-->\n' % (content,)
#            return ""
#            return '<script%s>\n<!--\n%s\n//-->\n</script>' % (pars, content)

        return rescript.sub(script_replace, html_in)
