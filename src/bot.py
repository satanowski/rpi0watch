# -*- coding: utf-8 -*-
"""
    bot.py
    ~~~~~~

    :copyright: (c) 2016 by Satanowski.
    :license: GNU General Public License v3.0
"""

from telegram import Updater, Emoji
from telegram.dispatcher import run_async
from array import array
from os import path
import logging as log


CUR_DIR = path.dirname(path.realpath(__file__))
CHAT_IDS = array('q')
CHAT_ID_FILE_PATH = path.join(CUR_DIR, 'bot_ids.bin')
token = None

try:
    with open(path.join(CUR_DIR, 'token'), 'r') as fp:
        token = fp.read()
except IOError:
    import sys
    sys.exit('Cannot read token file!')

updater = Updater(token=token.strip())
dispatcher = updater.dispatcher

log.basicConfig(
    level=log.DEBUG,
    format='%(asctime)s %(levelname)s\n%(message)s\n'
)

def read_chat_ids():
    """Read IDs of registered users that should be notified by BOT"""

    global CHAT_IDS
    try:
        fp = open(CHAT_ID_FILE_PATH, 'rb')
    except IOError:
        log.error("Cannot open file '%s' for reading!", CHAT_ID_FILE_PATH)
        return

    if fp:
        all_read = False
        while not all_read:
            try:
                CHAT_IDS.fromfile(fp, 1024)
            except EOFError:
                all_read = True
        fp.close()

def write_chat_ids():
    """Write down current list of user's IDs"""

    global CHAT_IDS
    try:
        fp = open(CHAT_ID_FILE_PATH, 'wb')
    except IOError:
        log.error("Cannot open file '%s' for writing!", CHAT_ID_FILE_PATH)
        return

    if fp:
        CHAT_IDS.tofile(fp)
        fp.close()

def help(bot, update):
    """BOT command: help"""
    msg = "Hey {name}! I'm a RPi∅ Watch Bot and I understand the following " \
          "commands:\n" \
          " * /start - I will add you to my list and notify you when RPi0 ava" \
          "ilability changes\n * /stop - I will remove you from my list and w" \
          "ill not bother again\n * /help - I will display this message {grin}"

    bot.sendMessage(
        chat_id=update.message.chat_id,
        text=msg.format(
            grin=Emoji.SMILING_FACE_WITH_OPEN_MOUTH,
            name=update.message.from_user['first_name']
        )
    )

def start(bot, update):
    """BOT command: sign user in"""
    global CHAT_IDS

    if update.message.chat_id in CHAT_IDS:
        msg = "You are allready signed in {grin}"
    else:
        msg = "From now You will be notified if RPi0 availability changes."
        CHAT_IDS.append(update.message.chat_id)
        write_chat_ids()

    bot.sendMessage(
        chat_id=update.message.chat_id,
        text=msg.format(grin=Emoji.SMILING_FACE_WITH_OPEN_MOUTH)
    )


def stop(bot, update):
    """BOT command: sign user off"""
    global CHAT_IDS

    if update.message.chat_id in CHAT_IDS:
        msg = "From now you will not be notified {grin}"
        CHAT_IDS.remove(update.message.chat_id)
        write_chat_ids()
    else:
        msg = "You're not on the list, so I cannot sign you off more {grin}"

    bot.sendMessage(
        chat_id=update.message.chat_id,
        text=msg.format(grin=Emoji.SMILING_FACE_WITH_OPEN_MOUTH)
    )

def unknown(bot, update):
    """BOT unknown command handler"""

    sorry = "Sorry, I didn't understand that command {face}"
    bot.sendMessage(
        chat_id=update.message.chat_id,
        text=sorry.format(face=Emoji.CONFOUNDED_FACE)
    )

def setup_bot():
    """Prepare bot to work"""
    read_chat_ids()
    dispatcher.addUnknownTelegramCommandHandler(unknown)
    dispatcher.addTelegramCommandHandler('start', start)
    dispatcher.addTelegramCommandHandler('stop', stop)
    dispatcher.addTelegramCommandHandler('help', help)

def start_bot():
    updater.start_polling()

def notify(message):
    """Send Notification to all registered users"""

    global CHAT_IDS

    for chid in CHAT_IDS:
        updater.bot.sendMessage(chat_id=chid, text=message)
