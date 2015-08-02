"""
oblique.py - Web Services Interface
Copyright 2008-9, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.

http://sopel.chat
"""

import re
import urllib
import sopel.web as web
from sopel.module import commands, example

definitions = 'https://github.com/nslater/oblique/wiki'

r_item = re.compile(r'(?i)<li>(.*?)</li>')
r_tag = re.compile(r'<[^>]+>')


def mappings(uri):
    result = {}
    bytes = web.get(uri)
    for item in r_item.findall(bytes):
        item = r_tag.sub('', item).strip(' \t\r\n')
        if not ' ' in item:
            continue

        command, template = item.split(' ', 1)
        if not command.isalnum():
            continue
        if not template.startswith('http://'):
            continue
        result[command] = template.replace('&amp;', '&')
    return result


def service(bot, trigger, command, args):
    t = o.services[command]
    template = t.replace('${args}', urllib.quote(args.encode('utf-8'), ''))
    template = template.replace('${nick}', urllib.quote(trigger.nick, ''))
    uri = template.replace('${sender}', urllib.quote(trigger.sender, ''))

    info = web.head(uri)
    if isinstance(info, list):
        info = info[0]
    if not 'text/plain' in info.get('content-type', '').lower():
        return bot.reply("Sorry, the service didn't respond in plain text.")
    bytes = web.get(uri)
    lines = bytes.splitlines()
    if not lines:
        return bot.reply("Sorry, the service didn't respond any output.")
    bot.say(lines[0][:350])


def refresh(bot):
    if hasattr(bot.config, 'services'):
        services = bot.config.services
    else:
        services = definitions

    old = o.services
    o.serviceURI = services
    o.services = mappings(o.serviceURI)
    return len(o.services), set(o.services) - set(old)


@commands('o')
@example('.o servicename arg1 arg2 arg3')
def o(bot, trigger):
    """Call a webservice."""
    if trigger.group(1) == 'urban':
        text = 'ud ' + trigger.group(2)
    else:
        text = trigger.group(2)

    if (not o.services) or (text == 'refresh'):
        length, added = refresh(bot)
        if text == 'refresh':
            msg = 'Okay, found %s services.' % length
            if added:
                msg += ' Added: ' + ', '.join(sorted(added)[:5])
                if len(added) > 5:
                    msg += ', &c.'
            return bot.reply(msg)

    if not text:
        return bot.reply('Try %s for details.' % o.serviceURI)

    if ' ' in text:
        command, args = text.split(' ', 1)
    else:
        command, args = text, ''
    command = command.lower()

    if command == 'service':
        msg = o.services.get(args, 'No such service!')
        return bot.reply(msg)

    if not command in o.services:
        return bot.reply('Service not found in %s' % o.serviceURI)

    if hasattr(bot.config, 'external'):
        default = bot.config.external.get('*')
        manifest = bot.config.external.get(trigger.sender, default)
        if manifest:
            commands = set(manifest)
            if (command not in commands) and (manifest[0] != '!'):
                return bot.reply('Sorry, %s is not whitelisted' % command)
            elif (command in commands) and (manifest[0] == '!'):
                return bot.reply('Sorry, %s is blacklisted' % command)
    service(bot, trigger, command, args)
o.services = {}
o.serviceURI = None

@commands('snippet')
def snippet(bot, trigger):
    if not o.services:
        refresh(bot)

    search = urllib.quote(trigger.group(2).encode('utf-8'))
    py = ("BeautifulSoup.BeautifulSoup(re.sub('<.*?>|(?<= ) +', '', " +
          "''.join(chr(ord(c)) for c in " +
          "eval(urllib.urlopen('http://ajax.googleapis.com/ajax/serv" +
          "ices/search/web?v=1.0&q=" + search + "').read()" +
          ".replace('null', 'None'))['responseData']['resul" +
          "ts'][0]['content'].decode('unicode-escape')).replace(" +
          "'&quot;', '\x22')), convertEntities=True)")
    service(bot, trigger, 'py', py)
