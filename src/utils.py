# -*- coding: utf-8 -*-
"""
    utils.py
    ~~~~~~~~

    :copyright: (c) 2015-2016 by Satanowski.
    :license: GNU General Public License v3.0
"""

import logging as log
import smtplib
import asyncio
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template
from ssl import SSLError

import aiohttp

log.basicConfig(
    level=log.DEBUG,
    format='%(asctime)s %(levelname)s\n%(message)s\n'
)


@asyncio.coroutine
def get_page(url):
    """Retrieve content of page of given URL."""

    log.debug('Retrievieng url: %s', url)
    try:
        with aiohttp.Timeout(3):
            response = yield from aiohttp.request('GET', url)
            return (yield from response.read_and_close(decode=False))
    except (asyncio.TimeoutError, aiohttp.errors.ClientOSError, SSLError):
        log.warning('Cannot retrieve %s', url)
        return None


def send_email(user_name, passwd, recipient, subject, body):
    '''Handles sending emails via GMail'''

    TO = recipient if isinstance(recipient, list) else [recipient]
    message = MIMEMultipart()
    message["Subject"] = subject
    message["To"] = ','.join(TO)
    message.attach(MIMEText(body))
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(user_name, passwd)
        server.sendmail(user_name, TO, message.as_string())
        server.close()
        log.debug('Sent email [%s]', ','.join(TO))
        return True
    except:
        return False


def prepare_emails():
    """Load list od recipients, GMail configuration and a template of
    message."""

    try:
        with open('maillist.json', 'r') as f:
            emails = json.load(f)
        with open('gmail.json', 'r') as f:
            gm = json.load(f)
        with open('message.txt', 'r') as f:
            msg = Template(f.read())
    except (ValueError, IOError):
        log.error("Cannot load email list, gmail configuration"
                  " or message template!")
        return None, None, None

    return emails, gm, msg
