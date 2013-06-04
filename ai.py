"""
ai.py - Artificial Intelligence Module
Copyright 2009-2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
from willie.module import rule, priority, rate
import random
import time

random.seed()
limit = 3


@rule('(?i)$nickname\:\s+(bye|goodbye|seeya|cya|ttyl|g2g|gnight|goodnight)')
@rate(30)
def goodbye(bot, trigger):
    byemsg = random.choice(('Bye', 'Goodbye', 'Seeya', 'Auf Wiedersehen', 'Au revoir', 'Ttyl'))
    punctuation = random.choice(('!', ' '))
    bot.say(byemsg + ' ' + trigger.nick + punctuation)


@rule('(?i).*(thank).*(you).*(willie|$nickname).*$')
@rate(30)
@priority('high')
def ty(bot, trigger):
    human = random.uniform(0, 9)
    time.sleep(human)
    mystr = trigger.group()
    mystr = str(mystr)
    if (mystr.find(" no ") == -1) and (mystr.find("no ") == -1) and (mystr.find(" no") == -1):
        bot.reply("You're welcome.")


@rule('(?i)$nickname\:\s+(thank).*(you).*')
@rate(30)
def ty2(bot, trigger):
    ty(bot, trigger)


@rule('(?i).*(thanks).*(willie|$nickname).*')
@rate(40)
def ty4(bot, trigger):
    ty(bot, trigger)


@rule('(willie|$nickname)\:\s+(yes|no)$')
@rate(15)
def yesno(bot, trigger):
    rand = random.uniform(0, 5)
    text = trigger.group()
    text = text.split(":")
    text = text[1].split()
    time.sleep(rand)
    if text[0] == 'yes':
        bot.reply("no")
    elif text[0] == 'no':
        bot.reply("yes")


@rule('(?i)($nickname|willie)\:\s+(ping)\s*')
@rate(30)
def ping_reply(bot, trigger):
    text = trigger.group().split(":")
    text = text[1].split()
    if text[0] == 'PING' or text[0] == 'ping':
        bot.reply("PONG")


@rule('(?i)i.*love.*(willie|$nickname).*')
@rate(30)
def love(bot, trigger):
    bot.reply("I love you too.")


@rule('(?i)(willie|$nickname)\:\si.*love.*')
@rate(30)
def love2(bot, trigger):
    bot.reply("I love you too.")


@rule('(?i)(willie|$nickname)\,\si.*love.*')
@rate(30)
def love3(bot, trigger):
    bot.reply("I love you too.")


@rule('(haha!?|lol!?)$')
@priority('high')
def f_lol(bot, trigger):
    randnum = random.random()
    if 0 < randnum < limit:
        respond = ['haha', 'lol', 'rofl']
        randtime = random.uniform(0, 9)
        time.sleep(randtime)
        bot.say(random.choice(respond))


@rule('(g2g!?|bye!?)$')
@priority('high')
def f_bye(bot, trigger):
    respond = ['bye!', 'bye', 'see ya', 'see ya!']
    bot.say(random.choice(respond))


@rule('(heh!?)$')
@priority('high')
def f_heh(bot, trigger):
    randnum = random.random()
    if 0 < randnum < limit:
        respond = ['hm']
        randtime = random.uniform(0, 7)
        time.sleep(randtime)
        bot.say(random.choice(respond))


@rule('(?i)$nickname\:\s+(really!?)')
@priority('high')
def f_really(bot, trigger):
    randtime = random.uniform(10, 45)
    time.sleep(randtime)
    bot.say(str(trigger.nick) + ": " + "Yes, really.")


@rule('^(wb|welcome\sback).*$nickname\s')
def wb(bot, trigger):
    bot.reply("Thank you!")


if __name__ == '__main__':
    print __doc__.strip()
