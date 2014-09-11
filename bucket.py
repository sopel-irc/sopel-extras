# coding=utf-8
"""
bucket.py - willie module to emulate the behavior of #xkcd's Bucket bot
Copyright 2012, Edward Powell, http://embolalia.net
Copyright © 2012-2014, Elad Alfassa <elad@fedoraproject.org>
Licensed under the Eiffel Forum License 2.

https://github.com/embolalia/willie

This module is built without using code from the original bucket, but using the same DB table format for factoids.

Things to know if you extend this module:

All inventory items are managed by the inventory class.
All runtime information is in the runtime information class

To prevent willie from outputting a "Don't Know" message when referred use the following line:

bucket_runtime_data.inhibit_reply = trigger.group(0)

and make sure the priority of your callable is medium or higher.
"""
import MySQLdb
import re
from re import sub
from random import randint, random, seed
import willie.web as web
import os
from collections import deque
from willie.tools import Ddict
from willie.module import *
import time
import warnings
seed()


def configure(config):
    """
    It is highly recommended that you run the configuration utility on this
    module, as it will handle creating an initializing your database. More
    information on this module at https://github.com/embolalia/willie-extras/wiki/The-Bucket-Module:-User-and-Bot-Owner-Documentation

    | [bucket] | example | purpose |
    | -------- | ------- | ------- |
    | db_host | example.com | The address of the MySQL server |
    | db_user | bucket | The username to log into the MySQL database |
    | db_pass | hunter2 | The password for the MySQL database |
    | db_name | bucket | The name of the database you will use |
    | literal_path | /home/willie/www/bucket | The path in which to store output of the literal command |
    | literal_baseurl | http://example.net/~willie/bucket | The base URL for literal output |
    | inv_size | 15 | The maximum amount of items that Willie can keep. |
    | fact_length | 6 | Minimum length of a factoid without being address |
    """
    if config.option('Configure Bucket factiod DB', False):
        config.interactive_add('bucket', 'db_host', "Enter the MySQL hostname", 'localhost')
        config.interactive_add('bucket', 'db_user', "Enter the MySQL username")
        config.interactive_add('bucket', 'db_pass', "Enter the user's password")
        config.interactive_add('bucket', 'db_name', "Enter the name of the database to use")
        config.interactive_add('bucket', 'literal_path', "Enter the path in which you want to store output of the literal command")
        config.interactive_add('bucket', 'literal_baseurl', "Base URL for literal output")
        config.interactive_add('bucket', 'inv_size', "Inventory size", '15')
        config.interactive_add('bucket', 'fact_length', 'Minimum length of a factoid without being address', '6')
        if config.option('do you want to generate bucket tables and populate them with some default data?', True):
            db = MySQLdb.connect(host=config.bucket.db_host,
                                 user=config.bucket.db_user,
                                 passwd=config.bucket.db_pass,
                                 db=config.bucket.db_name)
            cur = db.cursor()
            # Create facts table
            cur.execute("CREATE TABLE IF NOT EXISTS `bucket_facts` (`id` int(10) unsigned NOT NULL AUTO_INCREMENT,`fact` varchar(128) COLLATE utf8_unicode_ci NOT NULL,`tidbit` text COLLATE utf8_unicode_ci NOT NULL,`verb` varchar(16) CHARACTER SET latin1 NOT NULL DEFAULT 'is',`RE` tinyint(1) NOT NULL,`protected` tinyint(1) NOT NULL,`mood` tinyint(3) unsigned DEFAULT NULL,`chance` tinyint(3) unsigned DEFAULT NULL,PRIMARY KEY (`id`),UNIQUE KEY `fact` (`fact`,`tidbit`(200),`verb`),KEY `trigger` (`fact`),KEY `RE` (`RE`)) ENGINE=MyISAM  DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;")
            # Create inventory table
            cur.execute("CREATE TABLE IF NOT EXISTS `bucket_items` (`id` int(10) unsigned NOT NULL auto_increment,`channel` varchar(64) NOT NULL,`what` varchar(255) NOT NULL,`user` varchar(64) NOT NULL,PRIMARY KEY (`id`),UNIQUE KEY `what` (`what`),KEY `from` (`user`),KEY `where` (`channel`)) ENGINE=MyISAM DEFAULT CHARSET=latin1 ;")
            # Insert a Don't Know factiod
            cur.execute('INSERT INTO bucket_facts (`fact`, `tidbit`, `verb`, `RE`, `protected`, `mood`, `chance`) VALUES (%s, %s, %s, %s, %s, %s, %s);', ('Don\'t Know', '++?????++ Out of Cheese Error. Redo From Start.', '<reply>', False, False, None, None))
            # Insert a pickup full factiod
            cur.execute('INSERT INTO bucket_facts (`fact`, `tidbit`, `verb`, `RE`, `protected`, `mood`, `chance`) VALUES (%s, %s, %s, %s, %s, %s, %s);', ('pickup full', 'takes $item but drops $giveitem', '<action>', False, False, None, None))
            # Insert a duplicate item factiod
            cur.execute('INSERT INTO bucket_facts (`fact`, `tidbit`, `verb`, `RE`, `protected`, `mood`, `chance`) VALUES (%s, %s, %s, %s, %s, %s, %s);', ('duplicate item', 'No thanks, I\'ve already got $item', '<reply>', False, False, None, None))
            # Insert a take item factiod
            cur.execute('INSERT INTO bucket_facts (`fact`, `tidbit`, `verb`, `RE`, `protected`, `mood`, `chance`) VALUES (%s, %s, %s, %s, %s, %s, %s);', ('takes item', 'Oh, thanks, I\'ll keep this $item safe', '<reply>', False, False, None, None))
            db.commit()
            db.close()


class Inventory():
    ''' Everything inventory related '''
    avilable_items = []
    current_items = deque([])

    def add_random(self):
        ''' Adds a random item to the inventory'''
        item = self.avilable_items[randint(0, len(self.avilable_items) - 1)].strip()
        if item in self.current_items:
            try:
                return self.add_random()
            except RuntimeError:
                #Too much recursion, this can only mean all avilable_items are in current_items. Bananas.
                self.current_items.appendleft('bananas!')
                return 'bananas!'
        self.current_items.appendleft(item)
        return item

    def add(self, item, user, channel, bot):
        ''' Adds an item to the inventory'''
        dropped = False
        item = item.strip()
        if item.lower() not in [x.lower() for x in self.avilable_items]:
            db = connect_db(bot)
            cur = db.cursor()
            try:
                cur.execute('INSERT INTO bucket_items (`channel`, `what`, `user`) VALUES (%s, %s, %s);', (channel, item.encode('utf8'), user))
            except MySQLdb.IntegrityError as e:
                bot.debug('bucket', 'IntegrityError in inventory code', 'warning')
                bot.debug('bucket', str(e), 'warning')
            db.commit()
            db.close()
            self.avilable_items.append(item)
        if item in self.current_items:
            return '%ERROR% duplicate item %ERROR%'
        if len(self.current_items) >= int(bot.config.bucket.inv_size):
            dropped = True
        self.current_items.appendleft(item)
        return dropped

    def random_item(self):
        ''' returns a random item '''
        if len(self.current_items) == 0:
            return 'bananas!'
        item = self.current_items[randint(0, len(self.current_items) - 1)]
        return item

    def populate(self, bot):
        ''' Clears the inventory and fill it with random items '''
        self.current_items = deque([])
        while (len(self.current_items) < int(bot.config.bucket.inv_size)):
            self.add_random()

    def give_item(self):
        ''' returns a random item and removes it from the inventory '''
        item = self.random_item()
        try:
            self.current_items.remove(item)
        except ValueError:
            pass
        return item

    def remove(self, item):
        ''' Remove an item from the inventory, returns False if failed '''
        try:
            self.current_items.remove(item)
            return True
        except ValueError:
            return False

    def destroy(self, item, bot):
        ''' Deletes an item from the database '''
        if item not in self.avilable_items:
            return False
        self.remove(item)  # First, remove it from the inventory if present
        self.avilable_items.remove(item)  # remove it from the cache
        db = connect_db(bot)
        cur = db.cursor()
        cur.execute('DELETE FROM bucket_items WHERE what=%s',
                    (item.encode('utf8')))
        db.close()
        return True


class bucket_runtime_data():
    what_was_that = {}  # Remembering info of last DB read, per channel.
    inhibit_reply = ''  # Used to inhibit reply of an error message after teaching a factoid
    last_teach = {}
    last_lines = Ddict(dict)  # For quotes.
    inventory = None
    shut_up = []
    special_verbs = ['<reply>',
                     '<directreply>',
                     '<directaction>',
                     '<action>',
                     '<alias>']
    factoid_search_re = re.compile('(.*).~=./(.*)/')
    question_re = re.compile('^(how|who|why|which|what|whom|where|when) (is|are) .*\?$', re.IGNORECASE)
    last_said = {}
    cached_friends = []


def remove_punctuation(string):
    return sub("[,\.\!\?\;\:]", '', string)


def setup(bot):
    print 'Setting up Bucket...'
    db = None
    cur = None
    try:
        db = connect_db(bot)
    except:
        print 'Error connecting to the bucket database.'
        raise
        return
    bucket_runtime_data.inventory = Inventory()
    cur = db.cursor()
    cur.execute('SELECT * FROM bucket_items')
    items = cur.fetchall()
    for item in items:
        bucket_runtime_data.inventory.avilable_items.append(item[2])

    # Create friends table if it doesn't exist
    warnings.filterwarnings('ignore')
    cur.execute("""CREATE TABLE IF NOT EXISTS bucket_friends (
                `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
                `nick` varchar(64) NOT NULL,
                `friendly` int(10) NOT NULL default 0,
                `lastseen` int(10) unsigned NOT NULL,
                UNIQUE KEY (`id`),
                UNIQUE KEY (`nick`),
                PRIMARY KEY (`id`))""")
    warnings.filterwarnings('default')
    db.close()
    print 'Done setting up Bucket!'


def add_fact(bot, trigger, fact, tidbit, verb, re, protected, mood, chance, say=True):
    db = connect_db(bot)
    cur = db.cursor()
    try:
        cur.execute('INSERT INTO bucket_facts (`fact`, `tidbit`, `verb`, `RE`, `protected`, `mood`, `chance`) VALUES (%s, %s, %s, %s, %s, %s, %s)', (fact, tidbit, verb, re, protected, mood, chance))
        db.commit()
    except MySQLdb.IntegrityError:
        bot.say("I already had it that way!")
        return False
    finally:
        db.close()
    bucket_runtime_data.last_teach[trigger.sender] = [fact, verb, tidbit]
    if say:
        bot.say("Okay, " + trigger.nick)
    return True


@rule('$nick' '(.*?) (is|are) (.*)')
@priority('high')
def teach_is_are(bot, trigger):
    """Teaches a is b and a are b"""
    fact = trigger.group(1)
    tidbit = trigger.group(3)
    verb = trigger.group(2)
    protected = False
    mood = None
    chance = None
    for word in trigger.group(0).lower().split(' '):
        if word in bucket_runtime_data.special_verbs:
            return

    question = bucket_runtime_data.question_re.match('%s %s %s' % (fact,
                                                                   verb,
                                                                   tidbit))
    if question is not None:
        return  # Don't teach, someone is asking as a question

    fact = remove_punctuation(fact)
    add_fact(bot, trigger, fact, tidbit, verb, False, protected, mood, chance)
    bucket_runtime_data.inhibit_reply = trigger
    _friend_increase(bot, trigger)


@rule('$nick' '(.*?) (<\S+>) (.*)')
@priority('high')
def teach_verb(bot, trigger):
    """Teaches verbs/ambiguous reply"""
    bucket_runtime_data.inhibit_reply = trigger
    fact = trigger.group(1)
    fact = remove_punctuation(fact)
    tidbit = trigger.group(3)
    verb = trigger.group(2)
    re = False
    protected = False
    mood = None
    chance = None

    if verb not in bucket_runtime_data.special_verbs:
        verb = verb[1:-1]

    if fact == tidbit and verb == '<alias>':
        bot.reply('You can\'t alias like this!')
        return
    say = True
    if verb == '<alias>':
        say = False
    success = add_fact(bot, trigger, fact, tidbit, verb, re, protected, mood, chance, say)
    if verb == '<alias>':
        db = connect_db(bot)
        cur = db.cursor()
        cur.execute('SELECT * FROM bucket_facts WHERE fact = %s', [tidbit])
        results = cur.fetchall()
        db.close()
        if len(results) == 0 and success:
            bot.say('Okay, %s. but, FYI, %s doesn\'t exist yet' % (trigger.nick, tidbit))
        if len(results) > 0 and success:
            bot.say('Okay, %s' % trigger.nick)
    _friend_increase(bot, trigger)


@rule('$nick' 'remember (.*?) (.*)')
@priority('high')
def save_quote(bot, trigger):
    """Saves a quote"""
    bucket_runtime_data.inhibit_reply = trigger
    quotee = trigger.group(1).lower()
    word = trigger.group(2).strip()
    fact = quotee + ' quotes'
    verb = '<reply>'
    re = False
    protected = False
    mood = None
    chance = None
    try:
        memory = bucket_runtime_data.last_lines[trigger.sender][quotee]
    except KeyError:
        bot.say("Sorry, I don't remember what %s said about %s" % (quotee, word))
        return
    for line in memory:
        if remove_punctuation(word.lower()) in remove_punctuation(line[0].lower()):
            quotee = line[1]
            line = line[0]
            if line.startswith('\001ACTION'):
                line = line[len('\001ACTION '):-1]
                tidbit = '* %s %s' % (quotee, line)
            else:
                tidbit = '<%s> %s' % (quotee, line)
            result = add_fact(bot, trigger, fact, tidbit, verb, re, protected, mood, chance)
            if result:
                bot.reply("Remembered that %s <reply> %s" % (fact, tidbit))
            return
    bot.say("Sorry, I don't remember what %s said about %s" % (quotee, word))
    _friend_increase(bot, trigger)


@rule('$nick' 'delete #(.*)')
@priority('high')
def delete_factoid(bot, trigger):
    """Deletes a factoid"""
    bucket_runtime_data.inhibit_reply = trigger
    was = bucket_runtime_data.what_was_that
    if not trigger.admin:
        was[trigger.sender] = dont_know(bot, trigger)
        return
    db = None
    cur = None
    db = connect_db(bot)
    cur = db.cursor()
    try:
        cur.execute('SELECT * FROM bucket_facts WHERE ID = %s', (int(trigger.group(1))))
        results = cur.fetchall()
        if len(results) > 1:
            bot.debug('bucket', 'More than one factoid with the same ID?', 'warning')
            bot.debug('bucket', str(results), 'warning')
            bot.say('More than one factoid with the same ID. I refuse to continue.')
            return
        elif len(results) == 0:
            bot.reply('No such factoid')
            return
        cur.execute('DELETE FROM bucket_facts WHERE ID = %s', (int(trigger.group(1))))
        db.commit()
    except:
        bot.say("Delete failed! are you sure this is a valid factoid ID?")
        return
    finally:
        db.close()
    line = results[0]
    fact, tidbit, verb = parse_factoid(line)
    bot.say("Okay, %s, forgot that %s %s %s" % (trigger.nick, fact, verb, tidbit))


@rule('$nick' 'annihilate item (.*)')
def destroy_item(bot, trigger):
    bucket_runtime_data.inhibit_reply = trigger
    if not trigger.admin:
        return
    if bucket_runtime_data.inventory.destroy(trigger.group(1), bot):
        bot.reply('Okay, %s, destroyed %s' % (trigger.nick, trigger.group(1)))
    else:
        bot.reply('I don\'t know what that item is')


@rule('$nick' 'undo last')
@priority('high')
def undo_teach(bot, trigger):
    """Undo teaching factoid"""
    was = bucket_runtime_data.what_was_that
    bucket_runtime_data.inhibit_reply = trigger
    if not trigger.admin:
        was[trigger.sender] = dont_know(bot, trigger)
        return
    last_teach = bucket_runtime_data.last_teach
    fact = ''
    verb = ''
    tidbit = ''
    try:
        fact = last_teach[trigger.sender][0]
        verb = last_teach[trigger.sender][1]
        tidbit = last_teach[trigger.sender][2]
    except KeyError:
        bot.reply('Nothing to undo!')
        return
    db = None
    cur = None
    db = connect_db(bot)
    cur = db.cursor()
    try:
        cur.execute('DELETE FROM bucket_facts WHERE fact= %s AND verb=%s AND tidbit=%s', (fact, verb, tidbit))
        db.commit()
    except:
        bot.say("Undo failed, this shouldn't have happened!")
        return
    finally:
        db.close()
    bot.say("Okay, %s. Forgot that %s %s %s" % (trigger.nick, fact, verb, tidbit))
    del last_teach[trigger.sender]


@rule('((^\001ACTION (gives|hands|throws|serves) $nickname)|^$nickname..(take|have) (this|my|your|.*)) (.*)')
@rule('^\001ACTION puts (.*) in $nickname')
@rule('^\001ACTION (?:gives|hands|serves) (.*) to $nickname')
@priority('medium')
def inv_give(bot, trigger):
    ''' Called when someone gives us an item '''
    bucket_runtime_data.inhibit_reply = trigger
    was = bucket_runtime_data.what_was_that
    inventory = bucket_runtime_data.inventory
    groups = len(trigger.groups())
    if groups > 1:
        item = trigger.group(6)
    else:
        item = trigger.group(1)
    if item.endswith('\001'):
        item = item[:-1]
    item = item.strip()

    if groups > 1:
        if trigger.group(5) == 'my':
            item = '%s\'s %s' % (trigger.nick, item)
        elif trigger.group(5) == 'your':
            item = '%s\'s %s' % (bot.nick, item)
        elif trigger.group(5) != 'this' and trigger.group(5) is not None:
            item = '%s %s' % (trigger.group(5), item)
            item = re.sub(r'^me ', trigger.nick + ' ', item, re.IGNORECASE)
    if groups == 1 or trigger.group(3) != '':
        item = re.sub(r'^(his|her|its|their) ', '%s\'s ' % trigger.nick, item, re.IGNORECASE)

    item = item.strip()
    friendly = _get_friendly(bot, trigger.nick)
    if friendly is not None:
        friendly = friendly[0]
    else:
        friendly = 0
    db = connect_db(bot)
    cur = db.cursor()
    search_term = ''
    if friendly < -3 and randint(0, 2) > 0:
        search_term = 'refuse to take item'
    else:
        dropped = inventory.add(item.strip(), trigger.nick, trigger.sender, bot)
        if not dropped:
            # Query for 'takes item'
            search_term = 'takes item'
        elif dropped == '%ERROR% duplicate item %ERROR%':
            # Query for 'duplicate item'
            search_term = 'duplicate item'
        else:
            # Query for 'pickup full'
            search_term = 'pickup full'
    cur.execute('SELECT * FROM bucket_facts WHERE fact = %s', [search_term])
    results = cur.fetchall()
    db.close()
    result = pick_result(results, bot)
    fact, tidbit, verb = parse_factoid(result)
    tidbit = tidbit.replace('$item', item)
    tidbit = tidbit_vars(tidbit, trigger, False)

    say_factoid(bot, fact, verb, tidbit, True)
    was = result
    if search_term != 'refuse to take item':
        _friend_increase(bot, trigger)
    return


@rule('^\001ACTION (steals|takes) $nickname\'s (.*)')
@rule('^\001ACTION (steals|takes) (.*) from $nickname')
@priority('medium')
def inv_steal(bot, trigger):
    inventory = bucket_runtime_data.inventory
    item = trigger.group(2)
    bucket_runtime_data.inhibit_reply = trigger
    if item.endswith('\001'):
        item = item[:-1]
    if (inventory.remove(item)):
        bot.say('Hey! Give it back, it\'s mine!')
    else:
        bot.say('But I don\'t have any %s' % item)
    _friend_decrease(bot, trigger)


@rule('$nick' 'you need new things(.*|)')
@priority('medium')
def inv_populate(bot, trigger):
    bucket_runtime_data.inhibit_reply = trigger
    inventory = bucket_runtime_data.inventory
    bot.action('drops all his inventory and picks up random things instead')
    inventory.populate(bot)


@rule('(.*)')
@priority('low')
def say_fact(bot, trigger):
    """Response, if needed"""
    query = trigger.group(0)
    was = bucket_runtime_data.what_was_that
    db = None
    cur = None
    results = None

    if query.startswith('\001ACTION'):
        query = query[len('\001ACTION '):]

    addressed = query.lower().startswith(bot.nick.lower())  # Check if our nick was mentioned
    search_term = query.lower().strip()

    if addressed:
        search_term = search_term[(len(bot.nick) + 1):].strip()  # Remove our nickname from the search term
    search_term = remove_punctuation(search_term).strip()

    fact_length = bot.config.bucket.fact_length or 6
    if len(query) < int(fact_length) and not addressed:
        return  # Ignore factoids shorter than configured or default 6 chars when not addresed
    if addressed and len(search_term) is 0:
        return  # Ignore 0 length queries when addressed
    if search_term == 'don\'t know' and not addressed:
        return  # Ignore "don't know" when not addressed
    if not addressed and trigger.sender in bucket_runtime_data.shut_up:
        return  # Don't say anything if not addressed and shutting up
    if search_term == 'shut up' and addressed:
        bot.reply('Okay...')
        bucket_runtime_data.shut_up.append(trigger.sender)
        _friend_decrease(bot, trigger)
        return
    elif search_term in ['come back', 'unshutup', 'get your sorry ass back here'] and addressed:
        if trigger.sender in bucket_runtime_data.shut_up:
            bucket_runtime_data.shut_up.remove(trigger.sender)
            bot.reply('I\'m back!')
        else:
            bot.reply('Uhm, what? I was here all the time!')
        return
    literal = False
    inhibit = bucket_runtime_data.inhibit_reply
    if search_term.startswith('literal '):
        literal = True
        search_term = search_term[len('literal '):]
    elif search_term == 'what was that' and addressed:
        try:
            factoid_id = was[trigger.sender][0]
            factoid_fact = was[trigger.sender][1]
            factoid_tidbit = was[trigger.sender][2]
            factoid_verb = was[trigger.sender][3]
            bot.say('That was #%s - %s %s %s' % (factoid_id, factoid_fact, factoid_verb, factoid_tidbit))
        except KeyError:
            bot.say('I have no idea')
        return
    elif search_term.startswith('reload') or search_term.startswith('update') or inhibit == trigger:
        # ignore commands such as reload or update, don't show 'Don't Know'
        # responses for these
        return

    db = connect_db(bot)
    cur = db.cursor()
    factoid_search = None
    if addressed:
        factoid_search = bucket_runtime_data.factoid_search_re.search(search_term)
        _friend_increase(bot, trigger)
    try:
        if search_term == 'random quote':
            cur.execute('SELECT * FROM bucket_facts WHERE fact LIKE "% quotes" ORDER BY id ASC')
        elif factoid_search is not None:
            cur.execute('SELECT * FROM bucket_facts WHERE fact = %s AND tidbit LIKE %s ORDER BY id ASC', (factoid_search.group(1), '%' + factoid_search.group(2) + '%'))
        else:
            cur.execute('SELECT * FROM bucket_facts WHERE fact = %s ORDER BY id ASC', [search_term])
        results = cur.fetchall()
    except UnicodeEncodeError, e:
        bot.debug('bucket', 'Warning, database encoding error', 'warning')
        bot.debug('bucket', e, 'warning')
    finally:
        db.close()
    if results is None:
        return
    result = pick_result(results, bot)
    if addressed and result is None and factoid_search is None:
        was[trigger.sender] = dont_know(bot, trigger)
        return
    elif factoid_search is not None and result is None:
        bot.reply('Sorry, I could\'t find anything matching your query')
        return
    elif result is None:
        return

    fact, tidbit, verb = parse_factoid(result)
    tidbit = tidbit_vars(tidbit, trigger)

    if literal:
        if len(results) == 1:
            result = results[0]
            number = int(result[0])
            fact, tidbit, verb = parse_factoid(result)
            bot.say("#%d - %s %s %s" % (number, fact, verb, tidbit))
        else:
            bot.reply('just a second, I\'ll make the list!')
            bucket_literal_path = bot.config.bucket.literal_path
            bucket_literal_baseurl = bot.config.bucket.literal_baseurl
            if not bucket_literal_baseurl.endswith('/'):
                bucket_literal_baseurl = bucket_literal_baseurl + '/'
            if not os.path.isdir(bucket_literal_path):
                try:
                    os.makedirs(bucket_literal_path)
                except Exception as e:
                    bot.say("Can't create directory to store literal, sorry!")
                    bot.say(e)
                    return
            if search_term == 'random quote':
                filename = 'quotes'
            else:
                filename = fact.lower()
            f = open(os.path.join(bucket_literal_path, filename + '.txt'), 'w')
            for result in results:
                number = int(result[0])
                fact, tidbit, verb = parse_factoid(result)
                literal_line = "#%d - %s %s %s" % (number, fact, verb, tidbit)
                f.write(literal_line.encode('utf8') + '\n')
            f.close()
            link = bucket_literal_baseurl + web.quote(filename + '.txt')
            bot.reply('Here you go! %s (%d factoids)' % (link, len(results)))
        result = 'Me giving you a literal link'
    else:
        say_factoid(bot, fact, verb, tidbit, addressed)
    was[trigger.sender] = result


def pick_result(results, bot):
    search_term = ''
    try:
        if len(results) == 1:
            result = results[0]
        elif len(results) > 1:
            result = results[randint(0, len(results) - 1)]
        elif len(results) == 0:
            return None
        if result[3] == '<alias>':
            # Handle alias, recursive!
            db = connect_db(bot)
            cur = db.cursor()
            search_term = result[2].strip()
            try:
                cur.execute('SELECT * FROM bucket_facts WHERE fact = %s',
                            (search_term))
                results = cur.fetchall()
            except UnicodeEncodeError, e:
                bot.debug('bucket', 'Warning, database encoding error',
                          'warning')
                bot.debug('bucket', e, 'warning')
            finally:
                db.close()
            result = pick_result(results, bot)
        return result
    except RuntimeError, e:
        bot.debug('bucket', 'RutimeError in pick_result', 'warning')
        bot.debug('bucket', e, 'warning')
        bot.debug('bucket', 'search term was: %s' % search_term, 'warning')
        return None


@rule('$nick' 'inventory')
@priority('medium')
def get_inventory(bot, trigger):
    ''' get a human readable list of the bucket inventory '''

    bucket_runtime_data.inhibit_reply = trigger

    inventory = bucket_runtime_data.inventory

    if len(inventory.current_items) == 0:
        return bot.action('is carrying nothing')

    readable_item_list = ', '.join(inventory.current_items)

    bot.action('is carrying ' + readable_item_list)


def connect_db(bot):
    return MySQLdb.connect(host=bot.config.bucket.db_host,
                           user=bot.config.bucket.db_user,
                           passwd=bot.config.bucket.db_pass,
                           db=bot.config.bucket.db_name,
                           charset="utf8",
                           use_unicode=True)


def tidbit_vars(tidbit, trigger, random_item=True):
    ''' Parse in-tidbit vars '''
    # Special in-tidbit vars:
    inventory = bucket_runtime_data.inventory
    try:
        nick = trigger.nick
    except AttributeError:
        nick = trigger
    tidbit = tidbit.replace('$who', nick)
    finaltidbit = ''
    for word in tidbit.split(' '):
        if '$giveitem' in word.lower():
            # we have to use replace here in case of punctuation
            word = word.replace('$giveitem', inventory.give_item())
        elif '$newitem' in word.lower():
            word = word.replace('$newitem', inventory.add_random())
        elif '$item' in word.lower() and random_item:
            word = word.replace('$item', inventory.random_item())
        if (len(finaltidbit) > 0):
            word = ' ' + word
        finaltidbit = finaltidbit + word
    return finaltidbit


def dont_know(bot, trigger):
    ''' Get a Don't Know reply from the cache '''
    db = connect_db(bot)
    cur = db.cursor()
    cur.execute('SELECT * FROM bucket_facts WHERE fact = "Don\'t Know"')
    results = cur.fetchall()
    db.close()
    reply = results[randint(0, len(results) - 1)]
    fact, tidbit, verb = parse_factoid(reply)
    tidbit = tidbit_vars(tidbit, trigger, True)
    say_factoid(bot, fact, verb, tidbit, True)
    return reply


def say_factoid(bot, fact, verb, tidbit, addressed):
    if verb not in bucket_runtime_data.special_verbs:
        bot.say("%s %s %s" % (fact, verb, tidbit))
    elif verb == '<reply>':
        bot.say(tidbit)
    elif verb == '<action>':
        bot.action(tidbit)
    elif verb == '<directreply>' and addressed:
        bot.say(tidbit)
    elif verb == '<directaction>' and addressed:
        bot.action(tidbit)


def say_factiod_to_channel(bot, fact, verb, tidbit, target):
    if verb not in bucket_runtime_data.special_verbs:
        bot.msg(target, "%s %s %s" % (fact, verb, tidbit))
    elif verb == '<reply>':
        bot.msg(target, tidbit)
    elif verb == '<action>':
        bot.msg(target, '\001ACTION %s\001' % tidbit)


@rule('(.*)')
@priority('medium')
def remember(bot, trigger):
    ''' Remember last 15 lines of each user, to use in the quote function '''
    memory = bucket_runtime_data.last_lines
    nick = trigger.nick.lower()
    if nick not in memory[trigger.sender]:
        memory[trigger.sender][nick] = []
    fifo = deque(memory[trigger.sender][nick])
    if len(fifo) == 15:
        fifo.pop()
    fifo.appendleft([trigger.group(0), trigger.nick])
    memory[trigger.sender][trigger.nick.lower()] = fifo
    if not trigger.sender.is_nick():
        bucket_runtime_data.last_said[trigger.sender] = time.time()
    _add_friend(bot, trigger)


def parse_factoid(result):
    return result[1], result[2], result[3]


@willie.module.rule('.*')
@willie.module.event('JOIN')
def handle_join(bot, trigger):
    if trigger.nick == bot.nick:
        return
    ret = _get_friendly(bot, trigger.nick)
    if ret is None:
        return _add_friend(bot, trigger)
    friendly, lastseen = ret
    if time.time() > lastseen + (15*60):
        greet = 25+(((friendly*5)/25)**3)
        time.sleep(randint(1, 5) + random())  # Jitter to appear human
        if randint(0, 100) < greet:
            db = connect_db(bot)
            cur = db.cursor()
            cur.execute('SELECT * FROM bucket_facts WHERE fact = "greet on join"')
            results = cur.fetchall()
            db.close()
            result = pick_result(results, bot)
            fact, tidbit, verb = parse_factoid(result)
            tidbit = tidbit_vars(tidbit, trigger)
            say_factoid(bot, fact, verb, tidbit, True)
            was = result
    _add_friend(bot, trigger)


@willie.module.rule('.*')
@willie.module.event('PART')
def handle_part(bot, trigger):
    if trigger.nick != bot.nick:
        _add_friend(bot, trigger)


def _add_friend(bot, trigger):
    ''' Add a new "friend" to the db or updates their lastseen  time '''
    friend = trigger.nick.lower()
    db = connect_db(bot)
    cursor = db.cursor()
    if friend not in bucket_runtime_data.cached_friends:
        # New person
        try:
            cursor.execute('INSERT INTO bucket_friends (`nick`, `lastseen`) VALUES (%s, %s)', (friend, int(time.time())))
        except MySQLdb.IntegrityError:
            pass  # nick already in db
        bucket_runtime_data.cached_friends.append(friend)
    cursor.execute('UPDATE bucket_friends SET lastseen=%s WHERE nick=%s', (int(time.time()), friend))
    db.commit()
    db.close()


def _friend_modify(bot, trigger, increment):
    friend = trigger.nick.lower()
    if friend not in bucket_runtime_data.cached_friends:
        _add_friend(bot, trigger)
    db = connect_db(bot)
    cursor = db.cursor()
    cursor.execute('SELECT friendly FROM bucket_friends WHERE nick=%s', (friend))
    friendly = cursor.fetchone()
    friendly = friendly[0] + increment
    # Guard against mysql maxint errors
    if friendly < 2147483647 and friendly > -2147483648:
        cursor.execute('UPDATE bucket_friends SET friendly=%s WHERE nick=%s', (int(friendly), friend))
    db.commit()
    db.close()


def _friend_decrease(bot, trigger):
    _friend_modify(bot, trigger, -1)


def _friend_increase(bot, trigger):
    _friend_modify(bot, trigger, 1)


def _get_friendly(bot, nick):
    nick = nick.lower()
    db = connect_db(bot)
    cursor = db.cursor()
    cursor.execute('SELECT friendly, lastseen FROM bucket_friends WHERE nick=%s', (nick))
    friendly = cursor.fetchone()
    db.close()
    return friendly


@interval(30*60)
def too_quiet(bot):
    ''' Say something if nobody said anything for four hours '''
    # Add jitter
    time.sleep(randint(25, 123))
    for channel, last_time in bucket_runtime_data.last_said.iteritems():
        shut_up = bucket_runtime_data.shut_up
        if time.time() > last_time + (4 * 60 * 60) and channel not in shut_up:
            if randint(0, 2) == 1:
                continue
            db = connect_db(bot)
            try:
                cur = db.cursor()
                cur.execute('SELECT * FROM bucket_facts WHERE fact NOT LIKE' +
                            '"%quotes%" ORDER BY RAND() LIMIT 1')
                results = cur.fetchall()
                result = pick_result(results, bot)
                was[trigger.sender] = result
                fact, tidbit, verb = parse_factoid(result)
                tidbit = tidbit_vars(tidbit, 'god of time')
                say_factiod_to_channel(bot, fact, verb, tidbit, channel)
                bucket_runtime_data.last_said[channel] = time.time()
            finally:
                db.close()
            # more jitter, so we don't send messages to all channels at the
            # same time:
            time.sleep(randint(2, 11))

if __name__ == '__main__':
    print __doc__.strip()
