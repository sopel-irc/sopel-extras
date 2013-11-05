# -*- coding: utf8 -*-
"""
redmine.py - Willie Redmine Module
Copyright 2013, Ben Ramsey, benramsey.com
Licensed under the MIT License.

This module will respond to Redmine commands.
"""

from collections import OrderedDict
from HTMLParser import HTMLParser
from urllib import urlencode, quote
from willie import web, tools
from willie.module import rule, commands, example
import dateutil.parser
import json
import re

pattern_url = ''

def configure(config):
    """
    To property configure the bot for Redmine access, you'll need
    your Redmine base URL and API access key.

    | [redmine] | example | purpose |
    | --------- | ------- | ------- |
    | base_url  | https://example.org/redmine/ | Base URL for your Redmine installation |
    | api_access_key | 8843d7f92416211de9ebb963ff4ce28125932878 | Your Redmine API access key |
    """
    config.interactive_add('redmine', 'base_url', 'Base URL')
    config.interactive_add('redmine', 'api_access_key', 'API Access Key')


def setup(bot):
    global pattern_url
    pattern_url = bot.config.redmine.base_url
    if not pattern_url.endswith('/'):
        pattern_url = pattern_url + '/'
    pattern_url = pattern_url.replace('https://', '')
    pattern_url = pattern_url.replace('http://', '')
    redmine = re.compile(pattern_url + '(\S+)\/(\w+)')
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.WillieMemory()
    bot.memory['url_callbacks'][redmine] = redmine_url


@rule('.*' + pattern_url + '(\S+)\/(\w+).*')
def redmine_url(bot, trigger):
    funcs = {
        'issues': redmine_issue
    }
    try:
        funcs[trigger.group(1)](bot, trigger, trigger.group(2))
    except:
        bot.say('I had trouble fetching the requested Redmine resource.')


def build_url(bot, trigger, resource, resource_id, is_json=True, use_key=False, params={}):
    url = bot.config.redmine.base_url + resource + '/' + str(resource_id)
    if is_json:
        url += '.json'
    if use_key:
        params['key'] = bot.config.redmine.api_access_key
    if params:
        url += '?' + urlencode(params)
    return url


@commands('rdissue')
@example('.rdissue 23')
def redmine_issue(bot, trigger, resource_id=None):
    if not resource_id:
        resource_id = trigger.group(2)
    url = build_url(bot, trigger, 'issues', resource_id, True, True, {})
    try:
        bytes = web.get(url)
        result = json.loads(bytes)
        if 'issue' in result:
            issue = result['issue']
        else:
            raise Exception('Could not find issue.')
    except:
        bot.say('I had trouble fetching the requested Redmine issue.')
        return

    try:
        project = issue['project']['name']
    except KeyError:
        project = False

    try:
        tracker = issue['tracker']['name']
    except KeyError:
        tracker = False

    try:
        assigned_to = issue['assigned_to']['name']
    except KeyError:
        assigned_to = 'unassigned'

    try:
        author = issue['author']['name']
    except KeyError:
        author = 'no author'

    try:
        status = issue['status']['name']
    except KeyError:
        status = 'n/a'

    try:
        priority = issue['priority']['name']
    except KeyError:
        priority = 'n/a'

    try:
        milestone = issue['fixed_version']['name']
    except KeyError:
        milestone = 'no milestone'

    try:
        created = dateutil.parser.parse(issue['created_on'])
        created = created.strftime('%Y-%m-%d')
    except:
        created = 'n/a'

    try:
        updated = dateutil.parser.parse(issue['updated_on'])
        updated = updated.strftime('%Y-%m-%d')
    except:
        updated = 'n/a'


    message = '[Redmine]'

    if project:
        message += '[' + project + ']'

    if tracker:
        message += '[' + tracker + ']'

    message += ' #' + str(issue['id']) + \
            ' ' + issue['subject'] + \
            ' | Assigned to: ' + assigned_to + \
            ' | Author: ' + author + \
            ' | Status: ' + status + \
            ' | Priority: ' + priority + \
            ' | Created: ' + created + \
            ' | Updated: ' + updated + \
            ' | Milestone: ' + milestone + \
            ' | Done: ' + str(issue['done_ratio']) + '%' + \
            ' | Estimated: ' + str(issue['estimated_hours']) + ' hrs' + \
            ' | Spent: ' + str(issue['spent_hours']) + ' hrs' + \
            ' <' + build_url(bot, trigger, 'issues', issue['id'], False, False, {}) + '>'

    bot.say(HTMLParser().unescape(message))

