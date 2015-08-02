"""
roulette.py - Sopel Roulette Game Module
Copyright 2010, Kenneth Sham
Licensed under the Eiffel Forum License 2.

http://sopel.chat
"""

from __future__ import print_function
from sopel.module import commands, priority
import random
from datetime import datetime, timedelta
random.seed()

# edit this setting for roulette counter. Larger, the number, the harder the game.
ROULETTE_SETTINGS = {
    # the bigger the MAX_RANGE, the harder/longer the game will be
    'MAX_RANGE': 5,

    # game timeout in minutes (default is 1 minute)
    'INACTIVE_TIMEOUT': 1,
}

# edit this setting for text displays
ROULETTE_STRINGS = {
    'TICK': '*TICK*',
    'KICK_REASON': '*SNIPED! YOU LOSE!*',
    'GAME_END': 'Game stopped.',
    'GAME_END_FAIL': "%s: Please wait %s seconds to stop Roulette.",
}

## do not edit below this line unless you know what you're doing
ROULETTE_TMP = {
    'LAST-PLAYER': None,
    'NUMBER': None,
    'TIMEOUT': timedelta(minutes=ROULETTE_SETTINGS['INACTIVE_TIMEOUT']),
    'LAST-ACTIVITY': None,
}


@commands('roulette')
@priority('low')
def roulette(bot, trigger):
    """Play a game of Russian Roulette"""
    global ROULETTE_SETTINGS, ROULETTE_STRINGS, ROULETTE_TMP
    if ROULETTE_TMP['NUMBER'] is None:
        ROULETTE_TMP['NUMBER'] = random.randint(0, ROULETTE_SETTINGS['MAX_RANGE'])
        ROULETTE_TMP['LAST-PLAYER'] = trigger.nick
        ROULETTE_TMP['LAST-ACTIVITY'] = datetime.now()
        bot.say(ROULETTE_STRINGS['TICK'])
        return
    if ROULETTE_TMP['LAST-PLAYER'] == trigger.nick:
        return
    ROULETTE_TMP['LAST-ACTIVITY'] = datetime.now()
    ROULETTE_TMP['LAST-PLAYER'] = trigger.nick
    if ROULETTE_TMP['NUMBER'] == random.randint(0, ROULETTE_SETTINGS['MAX_RANGE']):
        bot.write(['KICK', '%s %s :%s' % (trigger.sender, trigger.nick, ROULETTE_STRINGS['KICK_REASON'])])
        ROULETTE_TMP['LAST-PLAYER'] = None
        ROULETTE_TMP['NUMBER'] = None
        ROULETTE_TMP['LAST-ACTIVITY'] = None
    else:
        bot.say(ROULETTE_STRINGS['TICK'])


@commands('roulette-stop')
@priority('low')
def rouletteStop(bot, trigger):
    """Reset a game of Russian Roulette"""
    global ROULETTE_TMP, ROULETTE_STRINGS
    if ROULETTE_TMP['LAST-PLAYER'] is None:
        return
    if datetime.now() - ROULETTE_TMP['LAST-ACTIVITY'] > ROULETTE_TMP['TIMEOUT']:
        bot.say(ROULETTE_STRINGS['GAME_END'])
        ROULETTE_TMP['LAST-ACTIVITY'] = None
        ROULETTE_TMP['LAST-PLAYER'] = None
        ROULETTE_TMP['NUMBER'] = None
    else:
        bot.say(ROULETTE_STRINGS['GAME_END_FAIL'] % (trigger.nick, ROULETTE_TMP['TIMEOUT'].seconds - (datetime.now() - ROULETTE_TMP['LAST-ACTIVITY']).seconds))


if __name__ == '__main__':
    print(__doc__.strip())
