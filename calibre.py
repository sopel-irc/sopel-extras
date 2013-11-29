"""
Name:		Calibre Search
Purpose:	Allows your IRC bot (Willie) to search a configured Calibre library
Author:	  	Kevin Laurier
Created:	14/11/2013
Copyright:	(c) Kevin Laurier 2013
Licence:	GPLv3

This module allows your Willie bot to act as an interface for a configured Calibre
server by using its REST API. You can enter search words to obtain a list of URLs
to the ebooks stored on the server. The Calibre server may be remote or on the
local machine.
"""


from base64 import b64encode
import requests
from willie.module import commands, example


class CalibreRestFacade(object):
	"""
	Connect to Calibre using its REST api
	"""
	def __init__(self, url, username, password):
		"""
		Initialize a connection to Calibre using the Requests library
		"""
		self.url = url
		self.username = username
		self.password = password
		self.auth = requests.auth.HTTPDigestAuth(username, password)

	def books(self, book_ids):
		"""
		Get all books corresponding to a list of IDs
		"""
		book_ids_csv = ','.join(str(b_id) for b_id in book_ids)
		return requests.get(self.url + '/ajax/books', 
			auth=self.auth, params={'ids': book_ids_csv}).json()

	def search(self, keywords):
		"""
		Get a list of IDs corresponding to the search results
		"""
		return requests.get(self.url + '/ajax/search', 
			auth=self.auth, params={'query': keywords}).json()


def configure(config):
	"""
	| [calibre] | example | purpose |
	| ---------- | ------- | ------- |
	| url | http://localhost:8080 | The URL to your Calibre server |
	| username | calibre | The username used to log on your calibre server (if any) |
	| password | password | The password used to log on your calibre server (if any) |
	"""
	if config.option('Configure calibre module', False):
		if not config.has_section('calibre'):
			config.add_section('calibre')
		config.interactive_add('calibre', 'url', "Enter the URL to your Calibre server (without trailing slashes)")
		
		if config.option('Configure username / password for your Calibre server?'):
			config.interactive_add('calibre', 'username', "Enter your Calibre username")
			config.interactive_add('calibre', 'password', "Enter your Calibre password", ispass=True)
		config.save()		


def setup(bot):
	c = bot.config.calibre
	bot.memory['calibre'] = CalibreRestFacade(c.url, c.username, c.password)


@commands('calibre', 'cal')
@example('.calibre gods of eden')
@example('.calibre')
def calibre(bot, trigger):
	"""
	Queries a configured Calibre library and returns one or more URLs
	corresponding to the search results. If no search words are entered,
	the URL of the Calibre server will be returned.
	"""
	search_words = trigger.group(2)
	if not search_words:
		bot.reply('The Calibre library is here: ' + bot.config.calibre.url)
		return
		
	calibre = bot.memory['calibre']
	book_ids = calibre.search(search_words)['book_ids']
	num_books = len(book_ids)

	if num_books == 1:
		book_title = calibre.books(book_ids).values()[0]['title']
		bot.reply(u'{}: {}/browse/book/{}'
			.format(book_title, calibre.url, book_ids[0]))				

	elif num_books > 1:
		results = calibre.books(book_ids)
		books = [(book_id, results[str(book_id)]) for book_id in book_ids]

		bot.reply("I'm sending you a private message of all Alexandria search results!")
		bot.msg(trigger.nick, "{} results for '{}'"
			.format(len(books), search_words))

		for book_id, book in books:
			bot.msg(trigger.nick, u'{}: {}/browse/book/{}'
				.format(book['title'], calibre.url, book_id))
	else:
		bot.say("Calibre: No results found.")


@commands('calurl')
def calinfo(bot, trigger):
	"""
	Displays the URL of your configured Calibre server
	"""
	bot.say('URL: ' + bot.config.calibre.url)
