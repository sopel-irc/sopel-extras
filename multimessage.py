"""
multimessage.py - Send the same message to multiple users
Copyright 2013, Syfaro Warraw http://syfaro.net
Licensed under the Eiffel Forum License 2.
"""

from willie.module import commands, example


@commands('mm', 'multimessage')
@example('.mm nick1,nick2,nick3 my amazing message')
def multimessage(bot, trigger):
    """
    .mm <users> <message>  - Sends the same message to multiple users
    """
    if not trigger.isop:
        return
    parts = trigger.group(2).split(' ', 1)
    nicks = parts[0].split(',')
    for nick in nicks:
        bot.msg(nick, parts[1])
    bot.reply('All messages sent!')
