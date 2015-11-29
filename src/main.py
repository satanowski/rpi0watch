import asyncio
import smtplib
import time
import json

from aiohttp import web
from pyquery import PyQuery as pq
import aiocron
import aiohttp
from jinja2 import Template


lock = asyncio.Lock()
last_stat = False
STATUS = {}
EMAILS = []

with open('maillist.json', 'r') as f:
    o = json.load(f)
    EMAILS = o.get('emails')

class GMailer():
    def __init__(self, user_name, passwd):
        self.user_name = user_name
        self.passwd = passwd

    def send_email(self, recipient, subject, body):
        TO = recipient if type(recipient) is list else [recipient]

        message = """From: {}\nTo: {}\nSubject: {}\n\n{}\n""".format(
            self.user_name, 
            ", ".join(TO), 
            subject,
            body
        )

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.ehlo()
            server.starttls()
            server.login(self.user_name, self.passwd)
            server.sendmail(self.user_name, TO, message)
            server.close()
            return True
        except:
            return False

@asyncio.coroutine
def get_page(url):
    response = yield from aiohttp.request('GET', url)
    return (yield from response.read_and_close(decode=False))


@asyncio.coroutine
def pimoroni():
    url = 'https://shop.pimoroni.com/products/raspberry-pi-zero'
    html = yield from get_page(url)
    q = pq(html)
    forms = q('form')
    yield from lock
    try:
        STATUS['pimoroni'] = 'in-stock' in ''.join(
                [f.attrib.get('class') for f in forms 
                    if f.attrib.get('action')=='/cart/add'])
    finally:
        lock.release()

@asyncio.coroutine
def element14():
    url = 'http://www.element14.com/community/docs/DOC-79263?ICID=hp-pizero-ban'
    html = yield from get_page(url)
    q = pq(html)
    res = True
    for span in q('table.jiveBorder span'):
        if span.text_content().strip() == 'Raspberry Pi Zero  SOLD OUT':
            res = False
            break
    
    yield from lock
    try:
        STATUS['element14'] = res
    finally:
        lock.release()


@aiocron.crontab('*/1 * * * *')
@asyncio.coroutine
def check():
    yield from pimoroni()
    yield from element14()
    print(time.strftime("%H:%M:%S"))
    if True in STATUS.values():  # Bingo!
        print('In stock!')
        with open('gmail.json', 'r') as f:
            o = json.load(f)
            if not o:
                return
            if not last_stat:  # Do not repeat yourself
                gm = GMailer(o.get('login'), o.get('pass'))
                shops = ', '.join([k for k in STATUS if STATUS[k]])
                for e in EMAILS:
                    gm.send_email(
                        e,
                        'Raspberry Pi 0 Watch',
                        'W tej chwili Raspberry Pi 0 można kupić w sklepach: '\
                        '{}'.format(shops)
                    )
        last_stat = True
    else:
        print('Out of stock')
        last_stat = False

@asyncio.coroutine
def handle(request):
    page = ''
    with open('index.html', 'r') as f:
        template = Template(f.read())
        page = template.render(status=STATUS)
    return web.Response(body=page.encode('utf-8'))


@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', handle)
    srv = yield from loop.create_server(
        app.make_handler(),
        '127.0.0.1',
        3033
    )
    print("Server started")
    return srv


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
