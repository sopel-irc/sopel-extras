"""
ai.py - Artificial Intelligence Module
Copyright 2009-2011, Michael Yanovich, yanovich.net
Licensed under the Eiffel Forum License 2.

http://willie.dftba.net
"""
from willie.module import rule, priority, rate
import random
import time


def configure(config):
    """
    | [ai] | example | purpose |
    | ---------- | ------- | ------- |
    | frequency | 3 | How often Willie participates in the conversation (0-10) |
    """
    if config.option('Configure ai module', False):
            if not config.has_section('ai'):
                    config.add_section('ai')
            config.interactive_add('ai', 'frequency', 
                                   "How often do you want Willie to participate in the conversation? (0-10)",
                                   3)
            config.save()     
        
        
def setup(bot):
    # Set value to 3 if not configured
    if bot.config.ai and bot.config.ai.frequency:
        bot.memory['frequency'] = bot.config.ai.frequency
    else:
        bot.memory['frequency'] = 3
        
    random.seed()
        
        
def decide(bot):
    return 0 < random.random() < float(bot.memory['frequency']) / 10


@rule('(?i)$nickname\:\s+(bye|goodbye|gtg|seeya|cya|ttyl|g2g|gnight|goodnight)')
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


@rule('(?i)((willie|$nickname)\[,:]\s*i.*love|i.*love.*(willie|$nickname).*)')
@rate(30)
def love(bot, trigger):
    bot.reply("I love you too.")


@rule('(haha!?|lol!?)$')
@priority('high')
def f_lol(bot, trigger):
    if decide(bot):
        respond = ['haha', 'lol', 'rofl', 'hm', 'hmmmm...']
        randtime = random.uniform(0, 9)
        time.sleep(randtime)
        bot.say(random.choice(respond))


@rule('^\s*(([Bb]+([Yy]+[Ee]+(\s*[Bb]+[Yy]+[Ee]+)?)|[Ss]+[Ee]{2,}\s*[Yy]+[Aa]+|[Oo]+[Uu]+)|cya|ttyl|[Gg](2[Gg]|[Tt][Gg]|([Oo]{2,}[Dd]+\s*([Bb]+[Yy]+[Ee]+|[Nn]+[Ii]+[Gg]+[Hh]+[Tt]+)))\s*(!|~|.)*)$')
@priority('high')
def f_bye(bot, trigger):
    set1 = ['bye', 'byebye', 'see you', 'see ya', 'Good bye', 'have a nice day']
    set2 = ['~', '~~~', '!', ' :)', ':D', '(Y)', '(y)', ':P', ':-D', ';)', '(wave)', '(flee)']
    respond = [ str1 + ' ' + str2 for str1 in set1 for str2 in set2]
    bot.say(random.choice(respond))

@rule('^\s*(([Hh]+([AaEe]+[Ll]+[Oo]+|[Ii]+)+\s*(all)?)|[Yy]+[Oo]+|[Aa]+[Ll]+)\s*(!+|\?+|~+|.+|[:;][)DPp]+)*$')
@priority('high')
def f_hello(bot, trigger):
    randtime = random.uniform(0, 7)
    time.sleep(randtime)
    set1 = ['yo', 'hey', 'hi', 'Hi', 'hello', 'Hello', 'Welcome', 'How do you do']
    set2 = ['~', '~~~', '!', '?', ' :)', ':D', 'xD', '(Y)', '(y)', ':P', ':-D', ';)']
    respond = [ str1 + ' ' + str2 for str1 in set1 for str2 in set2]
    bot.say(random.choice(respond))


@rule('(heh!?)$')
@priority('high')
def f_heh(bot, trigger):
    if decide(bot):
        respond = ['hm', 'hmmmmmm...', 'heh?']
        randtime = random.uniform(0, 7)
        time.sleep(randtime)
        bot.say(random.choice(respond))


@rule('(?i)$nickname\:\s+(really!?)')
@priority('high')
def f_really(bot, trigger):
    randtime = random.uniform(10, 45)
    time.sleep(randtime)
    bot.say(str(trigger.nick) + ": " + "Yes, really.")


@rule('^\s*[Ww]([Bb]|elcome\s*back)[\s:,].*$nickname')
def wb(bot, trigger):
    str1 = ['Thank you', 'thanks']
    str2 = ['!', ':)', ':D']
    respond = [ str1 + ' ' + str2 for str1 in set1 for str2 in set2]
    randtime = random.uniform(0, 7)
    time.sleep(randtime)
    bot.reply(random.choice(respond))


if __name__ == '__main__':
    print __doc__.strip()
