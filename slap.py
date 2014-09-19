"""
slap.py - Slap Module
Copyright 2009, Michael Yanovich, yanovich.net

http://willie.dftba.net
"""

import random
from willie.module import commands
from willie.tools import Nick


@commands('slap', 'slaps')
def slap(willie, trigger):
    """.slap <target> - Slaps <target>"""
    text = trigger.group().split()
    if len(text) < 2 or text[1].startswith('#'):
        return
    try:
        if Nick(text[1]) not in willie.privileges[trigger.sender.lower()]:
            willie.say("You can't slap someone who isn't here!")
            return
    except KeyError:
        pass
    if text[1] == willie.nick:
        if (trigger.nick not in willie.config.admins):
            text[1] = trigger.nick
        else:
            text[1] = 'itself'
    if text[1] in willie.config.admins:
        if (trigger.nick not in willie.config.admins):
            text[1] = trigger.nick
    verb = random.choice(('slaps', 'kicks', 'destroys', 'annihilates', 'punches', 'roundhouse kicks', 'pwns', 'owns'))
    willie.write(['PRIVMSG', trigger.sender, ' :\x01ACTION', verb, text[1], '\x01'])
