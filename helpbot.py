"""
help.py - HelpBot Module
Copyright 2013, Dimitri "Tyrope" Molenaars, TyRope.nl
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""
from __future__ import print_function
from willie.module import rule, event, commands
from collections import deque

helpees = deque()

def configure(config):
    """
    To use the helpbot module, you have to set your help channel.

    | [helpbot] | example | purpose |
    | -------- | ------- | ------- |
    | channel | #help | Enter the channel HelpBot should moderate |
    """
    config.interactive_add('helpbot', 'channel', "Enter the channel HelpBot should moderate", None)

def setup(bot):
    if not bot.config.helpbot.channel:
        raise ConfigurationError('Helpbot module not configured')

@event('JOIN')
@rule(r'.*')
def addNewHelpee(bot, trigger):
    """Adds somebody who joins the channel to the helpee list."""
    if trigger.admin or trigger.nick == bot.nick or trigger.sender != bot.config.helpbot.channel:
        return
    if trigger.isop:
        willie.say('An operator has joined the help channel: ' + trigger.nick)
        return
    helpees.append({'nick': trigger.nick, 'request': None, 'active': False, 'skipped': False})
    try:
        bot.reply('Welcome to '+trigger.sender+'. Please PM '+bot.nick+' with your help request, prefixed with \'.request\' (Example: /msg '+bot.nick+' .request I lost my password.) Don\'t include any private information with your question (passwords etc), as the question will be posted in this channel')
    except AttributeError:
        bot.debug('Help','You\'re running a module requiring configuration, without having configured it.','warning')
        return

@event('NICK')
@rule(r'.*')
def helpeeRename(bot, trigger):
    """ Update the list when somebody changes nickname. """
    for h in helpees:
        if h['nick'] == trigger.nick:
            h['nick'] = trigger.args[0]
            return

@event('QUIT')
@rule(r'.*')
def helpeeQuit(bot, trigger):
    """Dispatch for removing somebody from the helpee list on-quit."""
    removeHelpee(bot, trigger)

@event('PART')
@rule(r'.*')
def helpeePart(bot, trigger):
    """Dispatch for removing somebode from the helpee list when they leave the channel."""
    if trigger.sender != bot.config.helpbot.channel:
        return
    else:
        removeHelpee(bot, trigger)

def removeHelpee(bot, trigger):
    """Removes somebody from the helpee list."""
    for i in range(len(helpees)):
        if trigger.nick == helpees[i]['nick']:
            try:
                helpees.remove(helpees[i])
                return bot.msg(bot.config.helpbot.channel, trigger.nick+' removed from waiting list.')
            except ValueError as e:
                bot.debug('Help', str(e), 'warning')
                return bot.msg(bot.config.helpbot.channel, 'Error removing %s from helpees list.' % (trigger.nick,))

@commands('request')
def request(bot, trigger):
    """Allows a helpee to add a message to their help request, and activates said request."""
    if trigger.sender.startswith("#"): return
    found = None
    for helpee in helpees:
        if trigger.nick == helpee['nick']:
            found = helpee
    if not found:
        return bot.say('You\'re not found in the list of people in the channel, are you sure you\'re in the channel?')
    else:
        if not trigger.groups()[1]:
            return bot.say('You forgot to actually state your question, example: .request Who the eff is Hank?')
        if not helpee['active']:
            helpee['active'] = True
            helpee['request'] = trigger.groups()[1].encode('UTF-8')
            bot.say('Your help request is now marked active. Your question is:')
            bot.say(helpee['request'])
            bot.say('If you have anything more to add, please use the .request command again. Please note that when you leave the channel your request will be deleted.')
            bot.msg(bot.config.helpbot.channel,trigger.nick+' just added a question to their help request.')
        else:
            helpee['request'] += ' '+trigger.groups()[1].encode('UTF-8')
            bot.say('You already had a question, I\'ve added this to what you\'ve asked previously. Your new question is:')
            bot.say(helpee['request'])

@commands('next')
def next(bot, trigger):
    """Allows a channel operator to get the next person in the waiting list, if said person didn't activate his or her help request, it reminds them and puts them at the end of the queue."""
    if not trigger.isop: return bot.reply('You\'re not a channel operator.')
    try:
        helpee = helpees.popleft()
    except:
        return bot.reply('Nobody waiting.')
    if not helpee['active']:
        if not helpee['skipped']:
            helpee['skipped'] = True
            helpees.append(helpee)
            bot.reply('Tried assigning '+helpee['nick']+' but they didn\'t set a help request, if they\'re the only person waiting for help please give them some time to set one.')
            bot.msg(helpee['nick'], 'An operator just tried to help you but you didn\'t tell me what you need help with. I\'m putting you back at the end of the queue, please use the .request command.')
        else:
            bot.msg(helpee['nick'], 'An operator just tried to help you again. Since you seem to be inactive I\'m going to remove you from the channel. Please use the .request command after you join again.')
            bot.write(['KICK', bot.config.helpbot.channel, helpee['nick'], 'Didn\'t set a help request before being assigned an operator, twice.'])
            bot.reply('Attempted to kick '+helpee['nick']+', due to being called twice without sending a request.')
    else:
        bot.reply('assigned '+helpee['nick']+' to you. Their question: '+helpee['request'])
        bot.write(['MODE', bot.config.helpbot.channel, '+v', helpee['nick']])

if __name__ == '__main__':
    print(__doc__.strip())
