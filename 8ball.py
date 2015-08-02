"""
8ball.py - Ask the magic 8ball a question
Copyright 2013, Sander Brand http://brantje.com
Licensed under the Eiffel Forum License 2.

http://sopel.dfbta.net
"""
import sopel
import random
@sopel.module.commands('8')
def ball(bot, trigger):
    """Ask the magic 8ball a question! Usage: .8 <question>"""
    messages = ["It is certain"," It is decidedly so","Without a doubt","Yes definitely","You may rely on it","As I see it yes","Most likely","Outlook good","Yes","Signs point to yes","Reply hazy try again","Ask again later","Better not tell you now","Cannot predict now","Concentrate and ask again","Don't count on it","My reply is no","God says no","Very doubtful","Outlook not so good"]
    answer = random.randint(0,len(messages) - 1)
    bot.say(messages[answer]);


