import sys, logging
from ..html.htmlbuilder import DIV

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
               smtp_pass=None) :
    """
    send_to is array [(name1, address1),(name2, address2),...,(nameN, addressN)]
    (any "name" could be None)
    """

    if smtp_ssl is None :
        smtp_ssl = smtp_host != "localhost"

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


def test() :
    import re, random
    from argparse import ArgumentParser
    from ..cli.colorterm import add_coloring_to_emit_ansi

    parser = ArgumentParser(description="Testing email send")
    parser.add_argument('--gmail-api', action='store_true', help="Send with GMail API (browser authorisation required)")
    parser.add_argument('--smtp', metavar='[USER[:PASSWD]@]HOST[:PORT]', help="Send with SMTP")
    parser.add_argument('send_from', metavar='SEND-FROM')
    parser.add_argument('send_to', metavar='SEND-TO')
    parser.add_argument('file', metavar='FILE')

    args = parser.parse_args ()

    logging.basicConfig(format="%(asctime)s.%(msecs)03d %(filename)s:%(lineno)d %(message)s",
                        level=logging.DEBUG, datefmt='%H:%M:%S')
    logging.StreamHandler.emit = add_coloring_to_emit_ansi(logging.StreamHandler.emit)

    if args.gmail_api and args.smtp :
        logging.error("You can only specify one of --gmail-api or --smtp, not both")
        exit(1)

    if not args.gmail_api and not args.smtp :
        args.smtp = "localhost"

    if args.smtp :
        m = re.compile(r'^(?:(?P<user>[^:]+)(?::(?P<pass>.+))?@)?(?P<host>[a-z0-9.-]+)(?::(?P<port>\d+))?$', re.I).match(args.smtp)

        if not m :
            logging.error("Cannot parse SMTP string")
            exit(1)

        print ("SMTP config" )
        for x in ['user', 'pass', 'host', 'port'] :
            print("   ", x, "=", m.group(x))
        print("    SSL  = <default>")

    pars = {'subject' :f"Проверочный емейл using , random ID: {random.randrange(10 ** 6, 10 ** 7)}",
            'html' : f"""\
Hi!<br />
This is a test of <code>users.messages.send</code>.<br />
Below we embed image <b>{args.file}</b>, check it out:<br />
<img src="cid:sample_file" /> <br />
Hope it worked!
""",
            'send_from' : args.send_from,
            'send_to' : [("Вася Закусочник", args.send_to)],
            'images' : {'sample_file': open(args.file, 'rb').read()}
            }

    if args.gmail_api :
        pars['send_with_gmail_api'] = True
    else :
        pars['smtp_port'] = m.group('port')
        pars['smtp_host'] = m.group('host')
        pars['smtp_user'] = m.group('user')
        pars['smtp_pass'] = m.group('pass')

    send_email(** pars)


