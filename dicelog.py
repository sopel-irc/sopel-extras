"""
dice.py - Dice Module
Copyright 2010-2013, Dimitri "Tyrope" Molenaars, TyRope.nl
Copyright 2013     , Lior    "Eyore"  Ramati   , FireRogue517@gmail.com
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net/
"""

from willie.module import commands, priority
from random import randint, seed
import time
import os.path
from willie.modules.calc import calculate
import re

seed()


def setup(bot):
    if not bot.config.has_section('dicelog'):
        bot.config.add_section('dicelog')
    if not bot.config.has_option('dicelog', 'logdir'):
        bot.config.parser.set('dicelog', 'logdir', '.')
    if not bot.config.has_option('dicelog', 'campaigns'):
        bot.config.parser.set('dicelog', 'campaigns', '')


def configure(config):
    """ Since this module conflicts with the default dice module, this module
        will ask the user to blacklist one or the other. If dicelog is kept, it
        asks for a directory to store the logs, and also for a list of campaigns
        to recognize.
    """
    which = config.option("This module conflicts with the default dice module. Should I disable it and to allow this one to run", True)
    module = "dice" if which else "dicelog"
    print "The %s module is being added to the module blacklist." % module
    if config.has_option('core', 'exclude'):
        if module not in config.core.exclude:
            config.core.exclude = ','.join([config.core.exclude, ' module'])
    else:
        if not config.has_option('core', 'enable'):
            config.parser.set('core', 'exclude', module)
    if module == "dicelog":
        return
    config.interactive_add('dicelog', 'logdir',
                "where should the log files be stored on the harddrive?")
    config.add_list('dicelog', 'campaigns', "\
You may now type out any campaigns you wish to include by default. Commands are\
provided to edit this list on the fly. Please be aware that this identifier is\
what will be used to log rolls and also name the files.", "Campaign Identifier:")
    config.dicelog.campaigns = config.dicelog.campaigns.lower()


@commands('d', 'dice', 'roll')
@priority('medium')
def dicelog(bot, trigger):
    """
    .dice [logfile] <formula>  - Rolls dice using the XdY format, also does
    basic math and drop lowest (XdYvZ). Saves result in logfile if given.
    """
    if not trigger.group(2):
        return bot.reply('You have to specify the dice you wanna roll.')

    # extract campaign
    if trigger.group(2).startswith('['):
        campaign, rollStr = trigger.group(2)[1:].split(']')
    else:
        campaign = ''
        rollStr = trigger.group(2).strip()
    campaign = campaign.strip()
    rollStr = rollStr.strip()
    # prepare string for mathing
    arr = rollStr.lower().replace(' ', '')
    arr = arr.replace('-', ' - ').replace('+', ' + ').replace('/', ' / ')
    arr = arr.replace('*', ' * ').replace('(', ' ( ').replace(')', ' ) ')
    arr = arr.replace('^', ' ^ ').replace('()', '').split(' ')
    full_string, calc_string = '', ''

    for segment in arr:
        # check for dice
        result = re.search("([0-9]+m)?([0-9]*d[0-9]+)(v[0-9]+)?", segment)
        if result:
            # detect droplowest
            if result.group(3) is not None:
                #check for invalid droplowest
                dropLowest = int(result.group(3)[1:])
                # or makes implied 1dx to be evaluated in case of dx being typed
                if (dropLowest >= int(result.group(2).split('d')[0] or 1)):
                    bot.reply('You\'re trying to drop too many dice.')
                    return
            else:
                dropLowest = 0

            # on to rolling dice!
            value, drops = '(', ''
            # roll...
            dice = rollDice(result.group(2))
            for i in range(0, len(dice)):
                # format output
                if i < dropLowest:
                    if drops == '':
                        drops = '[+'
                    drops += str(dice[i])
                    if i < dropLowest - 1:
                        drops += '+'
                    else:
                        drops += ']'
                else:
                    value += str(dice[i])
                    if i != len(dice) - 1:
                        value += '+'
            no_dice = False
            value += drops + ')'
        else:
            value = segment
        full_string += value
    # and repeat

    # replace, split and join to exclude dropped dice from the math.
    result = calculate(''.join(
                full_string.replace('[', '#').replace(']', '#').split('#')[::2]))
    if result == 'Sorry, no result.':
        bot.reply('Calculation failed, did you try something weird?')
    elif(no_dice):
        bot.reply('For pure math, you can use .c '
                     + rollStr + ' = ' + result)
    else:
        response = 'You roll ' + rollStr + ': ' + full_string + ' = ' + result
        bot.reply(response)
        campaign = campaign.strip().lower()
        if campaign:
            if campaign in bot.config.dicelog.campaigns.split(','):
                log = open(os.path.join(bot.config.dicelog.logdir, campaign + '.log'), 'a')
                log.write("At <%s> %s rolled %s\n" % (time.ctime(), trigger.nick, response[9:]))
                log.close()
            else:
                bot.reply("Didn't log because " + campaign + " is not listed as a campaign. sorry!")


def rollDice(diceroll):
    rolls = int(diceroll.split('d')[0] or 1)
    size = int(diceroll.split('d')[1])
    result = []  # dice results.

    for i in range(1, rolls + 1):
        #roll 10 dice, pick a random dice to use, add string to result.
        result.append((randint(1, size), randint(1, size), randint(1, size),
                       randint(1, size), randint(1, size), randint(1, size),
                       randint(1, size), randint(1, size), randint(1, size),
                       randint(1, size))[randint(0, 9)])
    return sorted(result)  # returns a set of integers.


@commands('campaign', 'campaigns')
@priority('medium')
def campaign(bot, trigger):
    if trigger.group(2):
        command, campaign = trigger.group(2).partition(' ')[::2]
    else:
        return bot.say('usage: campaign (list|add|del) <args>')
    if not command in ['list', 'add', 'del']:
        return bot.say('usage: campaign (list|add|del) <args>')
    if not command == 'list':
        if not trigger.admin:
            return
        elif not campaign:
            return bot.say('usage: campaign (list|add|del) <args>')
    campaign = campaign.lower().strip()
    campaigns = bot.config.dicelog.campaigns.split(', ')
    if campaign in campaigns:
        if command == 'del':
            campaigns.remove(campaign)
            bot.say("Campagin \"%s\" has been removed!" % campaign)
        else:  # command == 'add'
            bot.say("Campaign \"%s\" already exists!" % campaign)
    else:
        if command == 'del':
            bot.say("Campagin \"%s\" doesn't exist!" % campaign)
        else:  # command == 'add'
            campaigns.append(campaign)
    if not command == 'list':
        bot.config.dicelog.campaigns = ', '.join(campaigns)
    bot.say("The current list is: " + bot.config.dicelog.campaigns)

if __name__ == '__main__':
    print __doc__.strip()
