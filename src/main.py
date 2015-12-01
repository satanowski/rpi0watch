import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
import json
import sys

from aiohttp import web
from pyquery import PyQuery as pq
import aiocron
import aiohttp
from jinja2 import Template


lock = asyncio.Lock()
last_stat = False
CHECK_INTERVAL = 5  # minutes
STATUS = {}
SHOPS = {}
EMAILS = []
MSG = Template("""
At this moment the Raspberry Pi Zero is available in the following shops:
{% for s, u in shops %}
   - {{s.capitalize()}} ({{u}})
{% endfor %}

Regards,
Satanowski
""")

try:
    with open('shops.json', 'r') as f:
        SHOPS = json.load(f)

    with open('maillist.json', 'r') as f:
        EMAILS = json.load(f)
except IOError:
    print('Cannot load config!')
    sys.exit(1)


class GMailer():
    def __init__(self, user_name, passwd):
        self.user_name = user_name
        self.passwd = passwd

    def send_email(self, recipient, subject, body):
        TO = recipient if type(recipient) is list else [recipient]
        message = MIMEMultipart()
        message["Subject"] = subject
        message["To"] = ','.join(TO)
        message.attach(MIMEText(body))
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.ehlo()
            server.starttls()
            server.login(self.user_name, self.passwd)
            server.sendmail(self.user_name, TO, message.as_string())
            server.close()
            return True
        except:
            return False


@asyncio.coroutine
def get_page(url):
    response = yield from aiohttp.request('GET', url)
    return (yield from response.read_and_close(decode=False))


def pihut(q):
    x = q('#iStock-wrapper')
    return x and (not ('sold out' in x[0].text_content()))


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
    return not ('OUT OF STOCK' in
                [x.text_content() for x in q('#prod-stock .oos-header')])


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
    global last_stat
    for shop in SHOPS:
        yield from _check_site(shop)

    print(time.strftime("%H:%M:%S"))
    if True in STATUS.values():  # Bingo!
        print('In stock!')
        with open('gmail.json', 'r') as f:
            o = json.load(f)
            if not o:
                return
            if not last_stat:  # Do not repeat yourself
                gm = GMailer(o.get('login'), o.get('pass'))
                shops = [k for k in STATUS if STATUS[k]]
                shops.sort()
                shop_list = [(k, SHOPS[k]) for k in shops]

                for e in EMAILS:
                    sent = gm.send_email(
                        e, 'Raspberry Pi 0 Watch', MSG.render(shops=shop_list)
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
        shops = list(STATUS.keys())
        shops.sort()
        page = template.render(
            status=[(s, STATUS[s], SHOPS[s]) for s in shops]
        )
    return web.Response(body=page.encode('utf-8'))


@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', handle)
    srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 3033)
    print("Server started")
    return srv


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
