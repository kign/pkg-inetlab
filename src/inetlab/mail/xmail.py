import re, sys, logging
from ..html.htmlbuilder import DIV

channel_string = '[USER[:PASSWD]@]HOST[:PORT]|google|file=FILE'

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
    :param images:      List of embedded images
    :param invoke_premailer: apply Python module premailer tp HTML
    :param dry_run:     Dry run (nothing will be sent if True)
    :return: *Nothing*
    """

    kwargs = {'send_from' : send_from}
    if channel == "google" :
        kwargs['send_with_gmail_api'] = True
    elif channel.startswith('file=') :
        kwargs['save_message_to_file'] = channel[5:]
        kwargs['send_from'] = None  # inhibiting attempt to send
    else :
        m = re.compile(r'^(?:(?P<user>[^:]+)(?::(?P<pass>.+))?@)?(?P<host>[a-z0-9.-]+)(?::(?P<port>\d+))?$', re.I).match(channel)
        if not m :
            raise ValueError(f"Cannot parse {channel}")

        kwargs['smtp_port'] = m.group('port')
        kwargs['smtp_host'] = m.group('host')
        kwargs['smtp_user'] = m.group('user')
        kwargs['smtp_pass'] = m.group('pass')

    def address(s) :
        if isinstance(s, str) :
            return parse_address_string(s)
        else :
            return s

    send_email(subject, html,
               send_to=address(send_to), send_cc=address(send_cc),
               images=images, dry_run=dry_run, invoke_premailer=invoke_premailer,
               **kwargs)


def send_email(subject, html,
               images=None,
               send_to=None,
               send_cc=None,
               send_with_gmail_api = False,
               dry_run=False,

               smtp_port=None,
               smtp_ssl=None,
               send_from=None,
               save_message_to_file=None,
               smtp_host="localhost",
               smtp_user=None,
               invoke_premailer=False,
               smtp_pass=None) :
    """
    send_to is array [(name1, address1),(name2, address2),...,(nameN, addressN)]
    (any "name" could be None)
    """

    if smtp_ssl is None :
        smtp_ssl = smtp_host != "localhost"

    if invoke_premailer :
        from premailer import transform
        html = transform(html)

    if save_message_to_file :
        with open(save_message_to_file,"w") as fh :
            fh.write(DIV(1,style="font-size: large;",_=subject) + "\n" + html)
        logging.info("Saved file " + save_message_to_file)

    if send_to and send_from :
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.image import MIMEImage

        mroot = MIMEMultipart('related')
        mroot['subject'] = subject
        mroot['From'] = send_from
        mroot['To'] = make_list(send_to)
        if send_cc :
            mroot['Cc'] = make_list(send_cc)

        mroot.preamble = 'This is a multi-part message in MIME format.'

        mroot.attach(MIMEText(html,'html', 'utf-8'))

        if images :
            for iname,img in images.items() :
                msgImage = MIMEImage(img)
                msgImage.add_header('Content-ID', '<%s>' % iname)
                mroot.attach(msgImage)

        msg_content = mroot.as_string()

        dl = [email for name, email in send_to]
        if send_cc:
            dl.extend([email for name, email in send_cc])
        logging.info("Sending e-mail to %s via %s , %s chars" %
                     (", ".join(dl),
                      "GMail API" if send_with_gmail_api else smtp_host,
                      len(msg_content)))

        if send_with_gmail_api :
            from base64 import urlsafe_b64encode
            from .gmail_api import login

            service = login(['send'])

            if dry_run :
                logging.info("Dry run, not actually sending anything")

            else :
                # try :
                    # https://developers.google.com/gmail/api/guides/sending#python
                res = service.users()\
                             .messages()\
                             .send(userId="me", body={'raw': urlsafe_b64encode(msg_content.encode('utf-8')).decode('utf-8')})\
                             .execute()
                print(f"Sent, Message Id: {res['id']}")
                # except Exception as err :
                #     print("ERROR", err, file=sys.stderr)
        else :
            import smtplib
            if smtp_host is None :
                raise ValueError("Must specify smtp_host")

            try :
                if smtp_ssl :
                    smtp = smtplib.SMTP_SSL(smtp_host, smtp_port)
                else :
                    smtp = smtplib.SMTP(smtp_host, smtp_port)
                smtp.ehlo()
            except Exception as err :
                print("Failed to connect to SMTP host \"%s\", port %r, SSL : %s" % (smtp_host, smtp_port, "YES" if smtp_ssl else "no"), file=sys.stderr)
                raise err

            if smtp_user is not None and smtp_pass is not None :
                try :
                    smtp.login(smtp_user, smtp_pass)
                except Exception as err :
                    logging.error("Login with user name = %s, password = %s failed. Error message: %s", smtp_user, smtp_pass[:2] + "*"*(len(smtp_pass)-2), err)
                    if 'gmail' in smtp_host :
                        logging.info("If you are trying to use gmail, check this link: %s",
                            'https://myaccount.google.com/lesssecureapps')
                    exit(-1)
            if dry_run :
                logging.info("Dry run, not actually sending anything")
            else :
                smtp.sendmail(mroot['From'], dl, msg_content)
            smtp.quit()

def make_list(emails) :
    from email.header import Header
    return ", ".join(("{} <{}>".format(x[0] if x[0].isascii() else Header(x[0], 'utf-8').encode(), x[1]) if x[0] else x[1]) for x in emails)

def parse_address_string(s) :
    import pyparsing as pp

    host = pp.Combine(pp.delimitedList(pp.Word(pp.alphanums), '.', combine=True)).setParseAction(pp.downcaseTokens)
    email = pp.Combine(pp.Word(pp.alphanums) + "@" + host)

    name = pp.CharsNotIn(',<"') |  pp.dblQuotedString.setParseAction(pp.removeQuotes)
    recipient = pp.Group(name + "<" + email + ">" | email)
    rcp_list = pp.delimitedList(recipient, ',') + pp.StringEnd()

    try :
        return [(None,x[0]) if len(x) == 1 else (x[0], x[2]) for x in rcp_list.parseString(s)]
    except pp.ParseException as err :
        logging.error("Cannot parse %s: %s", s, err)
        return None

def test() :
    import random
    from argparse import ArgumentParser
    from ..cli.colorterm import add_coloring_to_emit_ansi

    parser = ArgumentParser(description="Testing email send (with embedded image)")
    parser.add_argument('channel', metavar=channel_string, help="Sending options")
    parser.add_argument('send_from', metavar='SEND-FROM')
    parser.add_argument('send_to', metavar='SEND-TO')
    parser.add_argument('file', metavar='IMAGE')

    args = parser.parse_args ()

    logging.basicConfig(format="%(asctime)s.%(msecs)03d %(filename)s:%(lineno)d %(message)s",
                        level=logging.DEBUG, datefmt='%H:%M:%S')
    logging.StreamHandler.emit = add_coloring_to_emit_ansi(logging.StreamHandler.emit)

    send(f"Проверочный емейл using , random ID: {random.randrange(10 ** 6, 10 ** 7)}",
            f"""\
Hi!<br />
This is a test of <code>users.messages.send</code>.<br />
Below we embed image <b>{args.file}</b>, check it out:<br />
<img src="cid:sample_file" /> <br />
Hope it worked!
""",
         args.channel,
        send_from=args.send_from,
        send_to=[("Вася Закусочник", args.send_to)],
        images={'sample_file': open(args.file, 'rb').read()})
