"""
8ball.py - Ask the magic 8ball a question
Copyright 2013, Sander Brand http://brantje.com
Licensed under the Eiffel Forum License 2.

http://willie.dfbta.net
"""
import willie
import random
@willie.module.commands('lart')
def lart(bot, trigger):
    """Lart a user! Usage: .lart <user>"""
    messages = ["Versa dell'acqua sulla tastiera di ", "Stacca la spina al computer di "]
    answer = random.randint(0,len(messages) - 1)
    message = "%s %s"%(messages[answer],trigger.group(2))

    bot.say(message);

    
