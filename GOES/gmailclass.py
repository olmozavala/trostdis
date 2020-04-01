#!/usr/bin/env python
# coding: utf-8

import imaplib
import email

from ftplib import FTP
from os.path import join

from config_goes.MailConfig_Example import get_config
from config_goes.params import *


def get_flist(email_msg):
    paths = str(email_msg).split()
    mail = str(email_msg).split('\\r\\n')
    dserver = [x for x in paths if 'ftp.' in x] # FTP Server
    directory  = [x.split()[-1] for x in mail if 'cd ' in x] # File directory in server
    files = [x[6:] for x in mail if '001/goes13' in x and  '.nc' in x] # File names
    ftpserver = dserver + directory
    return ftpserver, sorted(files)

def get_from_ftp(ftpserver, files):
    ftp = FTP(ftpserver[0])
    ftp.login()
    for file in files:
        print('Downloading:', file)
        with open(join(local_path,file.split('/')[-1]), 'wb') as fp:
            ftp.retrbinary('RETR {}'.format(join(ftpserver[-1],file)), fp.write)
            fp.close()
    ftp.quit()

def main():
    server = imaplib.IMAP4_SSL(host=SMTP_SERVER, port=SMTP_PORT)
    server.login(FROM_EMAIL,FROM_PWD)
    server.select('inbox')
    status, data = server.search(None, '(UNSEEN)') # Access only unread mails
    #status, data = server.search(None, 'ALL') # Access all mails
    data = data[0].split()
    if len(data)==0:
        sys.sys.exit() # No new mails

    for num in data:
        status, data = server.fetch(num, '(RFC822)')
        for response in data:
            if isinstance(response, tuple):
                msg = email.message_from_bytes(response[1])
                email_subject = msg['subject']
                if 'Processing Complete' in email_subject:
                    email_msg = data[0][1]
                    ftpserver, files = get_flist(email_msg)
                    get_from_ftp(ftpserver, files)



if __name__ == "__main__":
    config = get_config()
    FROM_EMAIL = config[GMAIL.FROM_EMAIL]
    FROM_PWD = config[GMAIL.FROM_PWD]
    local_path = config[GMAIL.local_path]

# Server config
SMTP_SERVER = "imap.gmail.com"
SMTP_PORT   = 993

main()

#FROM_EMAIL  = 'rk.ecmwf@gmail.com'
#FROM_PWD    = '6$$%70Wu'
#local_path = '/home/jogzav/Documents/GOES13/SS'

#b = msg
#if b.is_multipart():
#    for payload in b.get_payload():
#        print(payload.get_payload())
#else:
#    print(b.get_payload())

