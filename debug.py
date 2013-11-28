# coding=utf-8
"""
debug.py - Willie Debugging Module
Copyright 2013, Dimitri "Tyrope" Molenaars, Tyrope.nl
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""

from willie.module import commands, example

@commands('privs')
@example('.privs to get the full database, or .privs #channel to get those of just the channel.')
def privileges(bot, trigger):
    """Print the privileges of a specific channel, or the entire array."""
    if trigger.group(2):
        try:
            bot.say(str(bot.privileges[trigger.group(2)]))
        except Exception:
            bot.say("Channel not found.")
    else:
        bot.say(str(bot.privileges))

