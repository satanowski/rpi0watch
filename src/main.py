# -*- coding: utf-8 -*-
"""
    main.py
    ~~~~~~~

    :copyright: (c) 2015-2016 by Satanowski.
    :license: GNU General Public License v3.0
"""

from datetime import datetime
import asyncio
import logging as log
import sys
import os

from aiohttp import web
from jinja2 import Template
import aiocron
import PyRSS2Gen

from shops import shops
from utils import send_email, prepare_emails, Mydeq

__OFFNAME__ = 'Raspberry Pi 0 Watch'

BOT_ENABLED = True
if BOT_ENABLED:
    import bot

log.basicConfig(
    level=log.DEBUG,
    format='%(asctime)s %(levelname)s\n%(message)s\n'
)
lock = asyncio.Lock()
last_check = None
last_notification = None
last_status = False

# how many minutes must pass since last notification to send another one
ANNOY_THRESHOLD = 15


CHECK_INTERVAL = 5  # minutes
SHOP_HANDLERS = []

availability = Mydeq(maxlen=int(24 * (60 / CHECK_INTERVAL)))

tmpl_f = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'index.html')
with open(tmpl_f, 'r') as f:
    try:
        index_template = Template(f.read())
    except IOError:
        sys.exit('Cannot open template file!')


def prepare_shop_handlers():
    """Create isinstances of shop handlers."""

    for shop_handler in shops:
        SHOP_HANDLERS.append(shop_handler())


def get_products(only_available=True):
    """Return list of observed products.
    Only these which are available if 'only_available' is set."""

    products = []
    for shop in SHOP_HANDLERS:
        for prod in shop.products:
            if not (only_available and not shop.available):
                products.append(prod)

    return products


@aiocron.crontab('*/{} * * * *'.format(CHECK_INTERVAL))
@asyncio.coroutine
def check():
    """Check availability of all observed products."""
    global last_check

    for shop in SHOP_HANDLERS:
        yield from shop.check()

    last_check = datetime.utcnow().strftime("%Y/%m/%d-%H:%M")

    if any([shop.available for shop in SHOP_HANDLERS]):
        log.info('In stock!')
        notify()
    else:
        log.info('Out of stock')
        availability.append(False)


def notify():
    """Notify about availability of observed products."""
    global last_notification

    availability.append(True)
    emails, gm, msg = prepare_emails()

    if not all([emails, gm, msg]):
        log.error('Cannot notify users! No email/message configuration!')
        return

    if (last_notification and
        (datetime.utcnow()-last_notification).min < ANNOY_THRESHOLD):

        log.info(
            'Skipping notification: Pi was available at least once for last '
            '%d minutes.', ANNOY_THRESHOLD
        )
        return

    last_notification = datetime.utcnow()
    products = get_products(only_available=True)
    a_message = msg.render(shops=products)

    if BOT_ENABLED:
        log.debug('Sending telegram mesages...')
        bot.notify(a_message)
        log.debug('Sending telegram mesages done')

    log.debug('Sending emails...(%d)', len(emails))
    for e in emails:
        send_email(gm.get('login'), gm.get('pass'), e, __OFFNAME__, a_message)
    log.debug('Sending emails done')


def chunks(l, n):
    """Divide long list of availability histogram in 1 hour groups."""

    for i in range(0, len(l), n):
        yield l[i:i + n]


@asyncio.coroutine
def rss(request):
    """Generate RSS feed."""

    items = []

    for prod in get_products(only_available=False):
        items.append(PyRSS2Gen.RSSItem(
            title=prod.name,
            link=prod.url,
            description="Current status:{}Available".format(
                " " if prod.availability else " NOT "
            )
        ))

    feed = PyRSS2Gen.RSS2(
        title="RPi0 Watch",
        link='http://rpi0.satanowski.net/rss',
        description="Current status of RPi0 availability",
        lastBuildDate=datetime.now(),
        generator='RPi0 Watch',
        docs='http://rpi0.satanowski.net/',
        items=items
    )
    return web.Response(
        body=feed.to_xml('utf-8').encode(),
        content_type='application/rss+xml'
    )


@asyncio.coroutine
def index(request):
    """Generate main page."""

    samples_per_hour = int(60 / CHECK_INTERVAL)

    page = index_template.render(
        status=get_products(only_available=False),
        timestamp=last_check,
        availability=list(chunks(list(availability), samples_per_hour)),
        samples_per_hour=samples_per_hour
    )
    return web.Response(body=page.encode('utf-8'))


@asyncio.coroutine
def init(loop):
    """Main loop."""

    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', index)
    app.router.add_route('GET', '/rss', rss)
    srv = yield from loop.create_server(app.make_handler(), '127.0.0.1', 3033)
    log.info("Server started")
    return srv


if __name__ == '__main__':
    prepare_shop_handlers()
    if BOT_ENABLED:
        bot.setup_bot()
        bot.start_bot()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
