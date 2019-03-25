# -*- coding: utf8 -*-
"""
lart.py - Luser Attitude Readjustment Tool
Copyright 2014, Matteo Marchesotti https://www.sfwd.ws
Licensed under the Eiffel Forum License 2.

https://sopel.chat
"""

import random

from sopel import commands


@commands('lart')
def lart(bot, trigger):
    """LART (Luser Attitude Readjustment Tool). Throws a random insult to a luser! Usage: .lart <luser>"""
    try:
        collection = open('.lart.collection', 'r')
    except Exception as e:
        bot.say("No lart's collection file found. Try with .help addlart")
        print e
        return

    messages = [line.decode('utf-8') for line in collection.readlines()]
    collection.close()

    if len(messages)== 0:
        bot.say("No insult found! Type .help addlart")
        return;

    if trigger.group(2) is None:
        user = trigger.nick.strip()
    else:
        user = trigger.group(2).strip()

    message = random.choice(messages).replace('LUSER', user).encode('utf_8')

    bot.say(message)

@commands('addlart')
def addlart(bot, trigger):
    """Adds another insult to bot's collection with: .addlart <insult>. 'insult' _must_ contain 'LUSER' which will be substituted with the name of the luser."""
    try:
        lart = trigger.group(2).replace('"','\"').encode('utf_8')
        collection = open('.lart.collection', 'a')
        collection.write("%s\n"%lart)
        collection.close()
    except Exception as e:
        bot.say("Unable to write insult lart's collection file!")
        print e
        return

    bot.say("Thanks %s: Insult added!"%trigger.nick.strip())


