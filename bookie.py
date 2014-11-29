# coding=utf8
"""
bookie.py - Willie URL storage into bookie
"""
from __future__ import unicode_literals

from willie import web, tools
from willie.module import commands, rule, example
from willie.modules.url import get_hostname, url_finder, exclusion_char, title_tag_data, quoted_title, re_dcc
from willie.config import ConfigurationError

from datetime import datetime
import getpass
import json
try:
    import pytz
except:
    pytz = None
import re
import sys

# we match all URLs to override the builtin url.py module
regex = re.compile('.*')


def configure(config):
    """
    | [url] | example | purpose |
    | ---- | ------- | ------- |
    """
    if config.option('Configure Bookie?', False):
        if not config.has_section('bookie'):
            config.add_section('bookie')
        config.interactive_add(
            'bookie',
            'api_url',
            'URL of the Bookie API',
            'https://bookie.io/api/v1')
        config.interactive_add(
            'bookie',
            'api_user',
            'Username on the Bookie site',
            getpass.getuser())
        config.interactive_add(
            'bookie',
            'api_key',
            'API key on the Bookie site',
            None)

def setup(bot):
    global url_finder, exclusion_char

    if not bot.config.bookie.api_user or not bot.config.bookie.api_key:
        raise ConfigurationError('Bookie module not configured')
     
    if bot.config.has_option('url', 'exclusion_char'):
        exclusion_char = bot.config.url.exclusion_char

    url_finder = re.compile(r'(?u)(%s?(?:http|https|ftp)(?:://\S+))' %
                            (exclusion_char))
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.WillieMemory()
    bot.memory['url_callbacks'][regex] = bmark

    

def shutdown(bot):
    del bot.memory['url_callbacks'][regex]

@commands('bmark')
@example('.bmark http://example.com', '[ Example ] - example.com')
def bmark(bot, trigger):
    if not trigger.group(2):
        if trigger.sender not in bot.memory['last_seen_url']:
            return
        matched = check_callbacks(bot, trigger,
                                  bot.memory['last_seen_url'][trigger.sender],
                                  True)
        if matched:
            return
        else:
            urls = [bot.memory['last_seen_url'][trigger.sender]]
    else:
        urls = re.findall(url_finder, trigger)
    process_urls(bot, trigger, urls)

    
@rule('(?u).*(https?://\S+).*')
def title_auto(bot, trigger):
    """Automatically show titles for URLs. For shortened URLs/redirects, find
    where the URL redirects to and show the title for that (or call a function
    from another module to give more information).

    Unfortunate copy of modules.url.title_auto because I couldn't hook
    into it.

    """
    if re.match(bot.config.core.prefix + 'bmark', trigger):
        return

    # Avoid fetching known malicious links
    if 'safety_cache' in bot.memory and trigger in bot.memory['safety_cache']:
        if bot.memory['safety_cache'][trigger]['positives'] > 1:
            return

    urls = re.findall(url_finder, trigger)
    results = process_urls(bot, trigger, urls)

def process_urls(bot, trigger, urls):
    for url in urls:
        if not url.startswith(exclusion_char):
            # Magic stuff to account for international domain names
            try:
                url = willie.web.iri_to_uri(url)
            except:
                pass
            bot.memory['last_seen_url'][trigger.sender] = url
            (title, domain, resp) = api_bmark(bot, url)
            try:
                # assumes that bookie's times are UTC
                timestamp = datetime.strptime(json.loads(resp)['bmark']['stored'], '%Y-%m-%d %H:%M:%S')
                if pytz:
                    tz = tools.get_timezone(bot.db, bot.config,
                                            trigger.nick, trigger.sender)
                    timestamp = tools.format_time(bot.db, bot.config, tz, trigger.nick,
                                                  trigger.sender, timestamp)
                else:
                    timestamp += 'Z'
                status = timestamp
            except KeyError:
                status = 'no timestamp in %s' % json.loads(resp)
            except ValueError as e:
                if 'JSON' in str(e):
                    status = u'cannot parse JSON response: %s' % resp.decode('utf-8', 'ignore')
                else:
                    raise
            message = '[ %s ] - %s (%s)' % (title, domain, status)
            # Guard against responding to other instances of this bot.
            if message != trigger:
                bot.say(message)

def api_bmark(bot, trigger, found_match=None):
    match = trigger or found_match
    bytes = web.get(match)
    # XXX: needs a patch to the URL module
    title = find_title(content=bytes)
    api = '%s/%s/bmark?api_key=%s' % ( bot.config.bookie.api_url,
                                       bot.config.bookie.api_user,
                                       bot.config.bookie.api_key )
    if title:
        bot.debug('bookie', 'submitting %s with title %s to %s' % (match.encode('utf-8'),
                                                                   repr(title),
                                                                   api), 'warning')
        result = web.post(api, {u'url': match,
                                u'is_private': False,
                                u'description': title.encode('utf-8')})
        return (title, get_hostname(match), result)
    else:
        bot.debug('bookie', 'no title found in %s' % match, 'warning')

def find_title(url=None, content=None):
    """Return the title for the given URL.

    Copy of find_title that allows for avoiding duplicate requests."""
    if (not content and not url) or (content and url):
        raise ValueError('url *or* content needs to be provided to find_title')
    if url:
        try:
            content, headers = web.get(url, return_headers=True, limit_bytes=max_bytes)
        except UnicodeDecodeError:
            return # Fail silently when data can't be decoded
    assert content

    # Some cleanup that I don't really grok, but was in the original, so
    # we'll keep it (with the compiled regexes made global) for now.
    content = title_tag_data.sub(r'<\1title>', content)
    content = quoted_title.sub('', content)

    start = content.find('<title>')
    end = content.find('</title>')
    if start == -1 or end == -1:
        return
    title = web.decode(content[start + 7:end])
    title = title.strip()[:200]

    title = ' '.join(title.split())  # cleanly remove multiple spaces

    # More cryptic regex substitutions. This one looks to be myano's invention.
    title = re_dcc.sub('', title)

    return title or None


if __name__ == "__main__":
    from willie.test_tools import run_example_tests
    run_example_tests(__file__)
