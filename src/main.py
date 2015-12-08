# -*- coding: utf-8 -*-
"""
    main.py
    ~~~~~~~

    :copyright: (c) 2015 by Satanowski.
    :license: GNU General Public License v3.0
"""

from collections import deque
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import asyncio
import json
import logging as log
import smtplib
import sys
import time

from aiohttp import web
from jinja2 import Template
from pyquery import PyQuery as pq
import aiocron
import aiohttp


log.basicConfig(
    level=log.DEBUG,
    format='%(asctime)s %(levelname)s\n%(message)s\n'
)
lock = asyncio.Lock()
last_stat = False
last_check = 0

CHECK_INTERVAL = 5  # minutes
SHOPS = {}
STATUS = {}
availability = deque(maxlen=int(24 * (60 / CHECK_INTERVAL)))

try:
    log.debug('Loading config files')
    with open('shops.json', 'r') as f:
        SHOPS = json.load(f)

except (IOError, ValueError):
    log.error('Cannot load config!')
    sys.exit(1)


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


@asyncio.coroutine
def get_page(url):
    log.debug('Retrievieng url: {}'.format(url))
    response = yield from aiohttp.request('GET', url)
    return (yield from response.read_and_close(decode=False))


def pihut(q):
    x = q('#iStock-wrapper')
    return x and ('sold out' not in x[0].text_content() and
                  'Out Of Stock' not in x[0].text_content())


def pimoroni(q):
    forms = q('form')
    return 'in-stock' in ''.join([f.attrib.get('class') for f in forms
                                  if f.attrib.get('action') == '/cart/add'])


def element14(q):
    for span in q('table.jiveBorder span'):
        if span.text_content().strip() == 'Raspberry Pi Zero  SOLD OUT':
            return False
    return True


def adafruit(q):
    return (
        'OUT OF STOCK' not in
        [x.text_content() for x in q('#prod-stock .oos-header')]
    )


shop_mapping = {
    'element14': element14,
    'pihut': pihut,
    'pimoroni': pimoroni,
    'adafruit': adafruit,
    'adafruit-BudgetPack': adafruit,
    'adafruit-StarterPack': adafruit
}


@asyncio.coroutine
def _check_site(shop_key):
    log.debug('Cheking site [{}] ...'.format(shop_key))
    html = yield from get_page(SHOPS[shop_key])
    result = shop_mapping[shop_key](pq(html))
    yield from lock
    try:
        STATUS[shop_key] = result
    finally:
        lock.release()


@aiocron.crontab('*/{} * * * *'.format(CHECK_INTERVAL))
@asyncio.coroutine
def check():
    global last_stat, last_check
    for shop in SHOPS:
        yield from _check_site(shop)
    last_check = datetime.utcnow().strftime("%Y/%m/%d-%H:%M")
    if True in STATUS.values():  # Bingo!
        log.info('In stock!')
        gm = None
        emails = None
        msg = None
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
            return

        if not (gm and emails and msg):
            return

        if not last_stat:  # Do not repeat yourself
            shops = [k for k in STATUS if STATUS[k]]
            shops.sort()
            shop_list = [(k, SHOPS[k]) for k in shops]

            for e in emails:
                send_email(
                    gm.get('login'), gm.get('pass'),
                    e, 'Raspberry Pi 0 Watch', msg.render(shops=shop_list)
                )
        last_stat = True
    else:
        log.info('Out of stock')
        last_stat = False

    availability.append(last_stat)


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


@asyncio.coroutine
def handle(request):
    page = ''
    with open('index.html', 'r') as f:
        template = Template(f.read())
        shops = list(STATUS.keys())
        shops.sort()
        samples_per_hour = int(60 / CHECK_INTERVAL)
        page = template.render(
            status=[(s, STATUS[s], SHOPS[s]) for s in shops],
            timestamp=last_check,
            availability=list(
                chunks(list(availability), samples_per_hour)
            ),
            samples_per_hour=samples_per_hour
        )
    return web.Response(body=page.encode('utf-8'))


@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', handle)
    srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 3033)
    log.info("Server started")
    return srv


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
