"""
lart.py - Luser Attitude Readjustment Tool
Copyright 2014, Matteo Marchesotti https://www.sfwd.ws
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""
import willie
import random
@willie.module.commands('lart')
def lart(bot, trigger):
    """LART (Luser Attitude Readjustment Tool). Throws a random insult to a luser! Usage: .lart <luser>"""
    try:
        collection = open('.lart.collection', 'r')
    except Exception as e:
        bot.say("No lart's collection file found. Try with .help addlart")
        return

    messages = [line for line in collection.readlines()]
    collection.close()

    if len(messages)== 0:
        bot.say("No insult found! Type .help addlart")
        return;

    n_msg = random.randint(0,len(messages) - 1)
    message = messages[n_msg].replace('LUSER', trigger.group(2))

    bot.say(message)

@willie.module.commands('addlart')
def addlart(bot, trigger):
    """Adds another insult to bot's collection with: .addlart <insult>. 'insult' _must_ contain 'LUSER' which will be substituted with the name of the luser."""
    try:
        collection = open('.lart.collection', 'a')
        collection.write("%s\n"%trigger.group(2))
        collection.close()
    except Exception as e:
        bot.say("Unable to write insult lart's collection file!")
        return

    bot.say("Thanks %s: Insult added!"%trigger.nick)


