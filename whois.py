"""
whois.py - Sopel Whois module
Copyright 2014, Ellis Percival (Flyte) sopel@failcode.co.uk
Licensed under the Eiffel Forum License 2.

http://sopel.chat

A module to enable Sopel to perform WHOIS lookups on nicknames.
This can either be to have Sopel perform lookups on behalf of
other people, or can be imported and used by other modules.
"""

from sopel.module import commands, event, rule
from time import sleep
from datetime import datetime, timedelta

AGE_THRESHOLD = timedelta(days=1)

class Whois(object):
	def __init__(self, data):
		to, self.nick, self.ident, self.host, star, self.name = data
		self.datetime = datetime.now()

	def __repr__(self):
		return "%s(nick=%r, ident=%r, host=%r, name=%r, datetime=%r)" % (
			self.__class__.__name__,
			self.nick,
			self.ident,
			self.host,
			self.name,
			self.datetime
		)

	def __str__(self):
		return "%s!%s@%s * %s" % (
			self.nick, self.ident, self.host, self.name)


class WhoisFailed(Exception):
	pass


def setup(bot):
	bot.memory["whois"] = {}

def _clear_old_entries(bot):
	"""
	Removes entries from the bot's memory which are older
	than AGE_THRESHOLD.
	"""
	to_del = []
	for nick, whois in bot.memory["whois"].items():
		if whois.datetime < datetime.now() - AGE_THRESHOLD:
			to_del.append(nick)
	for nick in to_del:
		try:
			del bot.memory["whois"][nick]
		except KeyError:
			pass

def send_whois(bot, nick):
	"""
	Sends the WHOIS command to the server for the
	specified nick.
	"""
	bot.write(["WHOIS", nick])

def get_whois(bot, nick):
	"""
	Waits for the response to be put into the bot's
	memory by the receiving thread.
	"""
	i = 0
	while nick not in bot.memory["whois"] and i < 10:
		i += 1
		sleep(1)
	
	if nick not in bot.memory["whois"]:
		raise WhoisFailed("No reply from server")
	elif bot.memory["whois"][nick] is None:
		try:
			del bot.memory["whois"][nick]
		except KeyError:
			pass
		raise WhoisFailed("No such nickname")

	# A little housekeeping
	_clear_old_entries(bot)

	return bot.memory["whois"][nick]

def whois(bot, nick):
	"""
	Sends the WHOIS command to the server then waits for
	the response to be put into the bot's memory by the
	receiving thread.
	"""
	# Remove entry first so that we get the latest
	try:
		del bot.memory["whois"][nick]
	except KeyError:
		pass
	send_whois(bot, nick)
	return get_whois(bot, nick)

@rule(r".*")
@event("311")
def whois_found_reply(bot, trigger):
	"""
	Listens for successful WHOIS responses and saves
	them to the bot's memory.
	"""
	nick = trigger.args[1]
	bot.memory["whois"][nick] = Whois(trigger.args)

@rule(r".*")
@event("401")
def whois_not_found_reply(bot, trigger):
	"""
	Listens for unsuccessful WHOIS responses and saves
	None to the bot's memory so that the initial
	whois function is aware that the lookup failed.
	"""
	nick = trigger.args[1]
	bot.memory["whois"][nick] = None

	# Give the initiating whois function time to see
	# that the lookup has failed, then remove the None.
	sleep(5)
	try:
		del bot.memory["whois"][nick]
	except KeyError:
		pass