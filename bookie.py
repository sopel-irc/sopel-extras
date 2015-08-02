# coding=utf8
"""bookie.py - sopel URL storage into bookie
Copyright 2014, Antoine Beaupré <anarcat@debian.org>
Licensed under the Eiffel Forum License 2.

This will store links found on an IRC channel into a Bookie
instance. It needs to be configured with a username/key to be
functional, per-channel configs are possible.

Bookie is an open-source bookmarking application that is hosted on
http://bookie.io/ and can also be self-hosted. It is similar in
functionality to the http://del.icio.us/ commercial service.

Bookie can be useful to store a cached copy of links mentionned on
IRC. It will also generate an RSS feed of those links automatically,
and more! The author, for example, turns those RSS feeds into ePUB
e-books that are then transfered on his e-book reader so in effect,
Bookie and this plugin create a way to read links mentionned on IRC on
his ebook reader, offline.

This plugin uses only a tiny part of the Bookie API, we could expand
functionalities here significantly:

https://github.com/bookieio/Bookie/blob/develop/docs/api/user.rst

"""
from __future__ import unicode_literals

from sopel import web, tools
from sopel.module import commands, rule, example
from sopel.modules.url import get_hostname, url_finder, exclusion_char, title_tag_data, quoted_title, re_dcc
from sopel.config import ConfigurationError

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
    import urllib
    urlparse = urllib.parse.urlparse


# an HTML tag. cargo-culted from etymology.py
r_tag = re.compile(r'<[^>]+>')
r_whitespace = re.compile(r'[\t\r\n ]+')

api_url = None
api_user = None
api_key = None
api_suffix = '/api/v1/'
api_private = None

def text(html):
    '''html to text dumb converter

    cargo-culted from etymology.py'''
    html = r_tag.sub('', html)
    html = r_whitespace.sub(' ', html)
    return web.decode(html.strip())

def configure(config):
    """
    | [url] | example | purpose |
    | ---- | ------- | ------- |
    | api_url | https://bookie.io/api/v1/admin/account?api_key=XXXXXX | template URL for the bookie instance |
    | private | True | if bookmarks are private by default |
    | url_per_channel | #channel:admin:XXXXXX:True | per-channel configuration |
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
        config.interactive_add(
            'bookie',
            'auto',
            'Automatically parse bookmarks',
            False)

        if config.option('Would you like to configure individual accounts per channel?', False):
            c = 'Enter the API URL as #channel:account:key:private'
            config.add_list('bookie', 'url_per_channel', c, 'Channel:')

def validate_private(private):
    '''convert the private setting to a real bool

    this is necessary because it could be the "true" string...

    we consider every string but lower(true) to be false
    '''
    # deal with non-configured private setting
    if private is None:
        private = True
    if (type(private) == str):
        private = True if private.lower() == 'true' else False
    return private

def setup(bot):
    global url_finder, exclusion_char, api_url, api_key, api_user, api_private

    if bot.config.bookie.api_url:
        try:
            # say we have "https://example.com/prefix/api/v1/admin/account?api_key=XXXXXX"
            p = urlparse(bot.config.bookie.api_url)
            # "https://example.com"
            api_url = p.scheme + '://' + p.netloc
            # "/prefix"
            prefix = p.path.split(api_suffix)[0]
            if prefix:
                api_url += prefix
            # "/api/v1/"
            api_url += api_suffix
            # the path element after api_suffix
            # that is, "admin"
            api_user = p.path.split(api_suffix)[1].split('/')[0]
            # "XXXXXX"
            api_key = p.query.split('=')[1]
        except Exception as e:
            raise ConfigurationError('Bookie api_url badly formatted: %s' % str(e))
    else:
        raise ConfigurationError('Bookie module not configured')

    api_private = validate_private( bot.config.bookie.private)
    if bot.config.has_option('url', 'exclusion_char'):
        exclusion_char = bot.config.url.exclusion_char

    url_finder = re.compile(r'(?u)(.*?)\s*(%s?(?:http|https|ftp)(?:://\S+)\s*(.*?))' %
                            (exclusion_char))
    if bot.config.bookie.auto:
        if not bot.memory.contains('url_callbacks'):
            bot.memory['url_callbacks'] = tools.SopelMemory()
        bot.memory['url_callbacks'][re.compile('.*')] = bmark


def shutdown(bot):
    if bot.config.bookie.auto:
        del bot.memory['url_callbacks'][re.compile('.*')]

@commands('bmark')
@example('.bmark #tag description http://example.com', '[ Example ] - example.com')
def bmark(bot, trigger):
    # cargo-culted from url.py
    if not trigger.group(2):
        # this bookmarks the last URL seen by url.py or this module
        if trigger.sender not in bot.memory['last_seen_url']:
            return
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
    for pre, url, post in urls:
        if not url.startswith(exclusion_char):
            # Magic stuff to account for international domain names
            try:
                url = sopel.web.iri_to_uri(url)
            except:
                pass
            bot.memory['last_seen_url'][trigger.sender] = url
            # post the bookmark to the Bookie API
            (title, domain, resp, headers) = api_bmark(bot, trigger, url, pre+post)
            if headers['_http_status'] != 200:
                status = 'error from bookie API: %s' % text(resp.decode('utf-8', 'ignore'))
            else:
                # try to show the user when the bookmark was posted,
                # so they can tell if it's new
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
                    # the 'stored' field is not in the response?
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

def api(bot, trigger, func, data=None):
    global api_url, api_user, api_key
    user = api_user
    key = api_key
    if (trigger.sender and not trigger.sender.is_nick() and
        bot.config.has_option('bookie', 'url_per_channel')):
        match = re.search(trigger.sender + ':(\w+):(\w+)(?::(\w+))?',
                          bot.config.bookie.url_per_channel)
        if match is not None:
            user = match.group(1)
            key = match.group(2)
            data['is_private'] = int(validate_private(match.group(3)))
    api = '%s%s/bmark?api_key=%s' % ( api_url, user, key )
    bot.debug('bookie', 'submitting to %s data %s' % (api, data), 'verbose')
    # we use requests instead of web.post because Bookie expects
    # JSON-encoded submissions, which web.post doesn't support
    r = requests.post(api, data)
    r.headers['_http_status'] = r.status_code
    bot.debug('bookie', 'response: %s (headers: %s, body: %s)' % (r, r.text, r.headers), 'verbose')
    return (r.text, r.headers)

def api_bmark(bot, trigger, found_match=None, extra=None):
    url = found_match or trigger
    bytes = web.get(url)
    # XXX: needs a patch to the URL module
    title = find_title(content=bytes)
    if title is None:
        title = '[untitled]'
    data = {u'url': url,
            u'is_private': int(api_private),
            u'description': title.encode('utf-8'),
            u'content': bytes}
    if extra is not None:
        # extract #tags, uniquely
        # copied from http://stackoverflow.com/a/6331688/1174784
        tags = {tag.strip("#") for tag in extra.split() if tag.startswith("#")}
        if tags:
            data['tags'] = ' '.join(tags)
        # strip tags from message and see what's left
        message = re.sub(r'#\w+', '', extra).strip()
        if message != '':
            # something more than hashtags was provided
            data['extended'] = extra
    return [title, get_hostname(url)] + list(api(bot, trigger, 'bmark', data))

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
    from sopel.test_tools import run_example_tests
    run_example_tests(__file__)
