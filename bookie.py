# coding=utf8
"""bookie.py - Willie URL storage into bookie

Missing:
* add tags, extended descriptions options to .bmark
* parse #tags on the auto url parser

The above is annoyingly hard with regexes... but i've had good success
with "non-hungry" patterns:

>>> re.findall(r'(?u)(.*?)(!?(?:http|https|ftp)(?:://\S+))(.*?)', 'cool url: http://example.com and another http://example.org')
[('cool url: ', 'http://example.com', ''), (' and another ', 'http://example.org', '')]
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
import requests
import sys

if sys.version_info.major < 3:
    import urlparse
    urlparse = urlparse.urlparse
else:
    import urllibe
    urlparse = urllib.parse.urlparse


# we match all URLs to override the builtin url.py module
regex = re.compile('.*')

# an HTML tag. cargo-culted from etymology.py
r_tag = re.compile(r'<[^>]+>')
r_whitespace = re.compile(r'[\t\r\n ]+')

api_url = None
api_user = None
api_key = None
api_suffix = '/api/v1/'
api_private = None

def text(html):
    html = r_tag.sub('', html)
    html = r_whitespace.sub(' ', html)
    return web.decode(html.strip())

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
            'https://bookie.io/api/v1/admin/account?api_key=XXXXXX')
        config.interactive_add(
            'bookie',
            'private',
            'Mark bookmarks as private',
            True)

        if config.option('Would you like to configure individual accounts per channel?', False):
            c = 'Enter the API URL as #channel:account:key:private'
            config.add_list('bookie', 'url_per_channel', c, 'Channel:')

def validate_private(private):
    # deal with non-configured private setting
    if private is None:
        private = True
    if (type(private) == str):
        private = True if private == 'True' else False
    return private

def setup(bot):
    global url_finder, exclusion_char, api_url, api_key, api_user, api_private

    if bot.config.bookie.api_url:
        try:
            p = urlparse(bot.config.bookie.api_url)
            # https
            api_url = p.scheme + '://' + p.netloc
            prefix = p.path.split(api_suffix)[0]
            if prefix:
                api_url += prefix
            api_url += api_suffix
            # the path element after api_suffix
            api_user = p.path.split(api_suffix)[1].split('/')[0]
            api_key = p.query.split('=')[1]
        except Exception as e:
            raise ConfigurationError('Bookie api_url badly formatted: %s' % str(e))
    else:
        raise ConfigurationError('Bookie module not configured')

    api_private = validate_private( bot.config.bookie.private)
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
            (title, domain, resp, headers) = api_bmark(bot, trigger, url)
            if headers['_http_status'] != 200:
                status = 'error from bookie API: %s' % text(resp.decode('utf-8', 'ignore'))
            else:
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
                    status = 'posted on ' + timestamp
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
    global api_url, api_user, api_key
    url = found_match or trigger
    bytes = web.get(url)
    # XXX: needs a patch to the URL module
    title = find_title(content=bytes)
    user = api_user
    key = api_key
    private = api_private
    if (trigger.sender and not trigger.sender.is_nick() and
        bot.config.has_option('bookie', 'url_per_channel')):
        match = re.search(trigger.sender + ':(\w+):(\w+)(?::(\w+))?',
                          bot.config.bookie.url_per_channel)
        if match is not None:
            user = match.group(1)
            key = match.group(2)
            private = validate_private(match.group(3))
    api = '%s%s/bmark?api_key=%s' % ( api_url, user, key )
    if title:
        data = {u'url': url,
                u'is_private': int(private),
                u'description': title.encode('utf-8'),
                u'content': bytes}
        bot.debug('bookie', 'submitting %s with title %s to %s with data %s' % (url,
                                                                                repr(title),
                                                                                api, data), 'warning')
        r = requests.post(api, data)
        r.headers['_http_status'] = r.status_code
        return (title, get_hostname(url), r.text, r.headers)
    else:
        bot.debug('bookie', 'no title found in %s' % url, 'warning')

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
