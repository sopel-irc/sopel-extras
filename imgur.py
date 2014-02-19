#!/usr/bin/env python

import requests
import re
import os.path
from urlparse import urlparse
from willie.config import ConfigurationError
from willie import tools
from willie.module import rule

class ImgurClient(object):
    def __init__(self, client_id):
        """
        Sets the client_id (obtain yours here: https://api.imgur.com/oauth2/addclient)
        and the imgur API URL.
        """
        self.client_id = client_id
        self.api_url = "https://api.imgur.com/3/"

    def request(self, input):
        """
        Sends a request to the API. Only publicly available data is accessible.
        Returns data as pretty JSON.
        """

        headers = {'Authorization': 'Client-ID ' + self.client_id,
                   'Accept': 'application/json'}
        request = requests.get(self.api_url + input, headers=headers)
        request.raise_for_status()
        return request.json()

def configure(config):
    """
    The client ID can be obtained by registering your bot at
    https://api.imgur.com/oauth2/addclient

    |  [imgur]  |     example     |              purpose             |
    | --------- | --------------- | -------------------------------- |
    | client_id | 1b3cfe15768ba29 | Bot's ID, for Imgur's reference. |
    """

    if config.option('Configure Imgur? (You will need to register at https://api.imgur.com/oauth2/addclient)', False):
        config.interactive.add('imgur', 'client_id', 'Client ID')

def setup(bot):
    """
    Tests the validity of the client ID given in the configuration.
    If it is not, initializes willie's memory callbacks for imgur URLs,
    and uses them as the trigger for the link parsing function.
    """
    try:
        client = ImgurClient(bot.config.imgur.client_id)
        client.request('gallery.json')
    except requests.exceptions.HTTPError:
        raise ConfigurationError('Could not validate the client ID with Imgur. \
                                 Are you sure you set it up correctly?')
    imgur_regex = re.compile('(?:https?://)?(?:i\.)?imgur\.com/(.*)$')
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.WillieMemory()
    bot.memory['url_callbacks'][imgur_regex] = imgur

def album(link_id, bot):
    """
    Handles information retrieval for non-gallery albums.
    The bot will output the title, the number of images and the number of views
    of the album.
    """
    client = ImgurClient(bot.config.imgur.client_id)
    album_api_url = "album/" + link_id
    try:
        json_album_response = client.request(album_api_url)
    except requests.HTTPError:
        return bot.say('[imgur] [Album not found]')
    album = json_album_response['data']
    return bot.say('[imgur] ' + '[' + album['title'] + \
                   ' - an album with ' + str(album['images_count']) + ' images' \
                   ' and ' + str(album['views']) + ' views]')

def gallery(link_id, bot):
    """
    Handles information retrieval for gallery images and albums.
    The bot will output the title, the type (image/album/gif), the number of
    views, the number of upvotes/downvotes of the gallery resource.
    """
    client = ImgurClient(bot.config.imgur.client_id)
    gallery_api_url = "gallery/" + link_id
    try:
        json_gallery_response = client.request(gallery_api_url)
    except requests.HTTPError:
        return bot.say('[imgur] [Gallery resource not found]')
    gallery = json_gallery_response['data']
    if gallery['is_album']:
        return bot.say('[imgur] ' + '[' + gallery['title'] + \
                       ' - a gallery album with ' + str(gallery['views']) + \
                       ' views (' + str(gallery['ups']) + ' ups and ' + \
                       str(gallery['downs']) + ' downs)]')
    if gallery['type'] == 'image/gif':
        return bot.say('[imgur] ' + '[' + gallery['title'] + \
                       ' - a gallery gif with ' + str(gallery['views']) + \
                       ' views (' + str(gallery['ups']) + ' ups and ' + \
                       str(gallery['downs']) + ' downs)]')
    else:
        return bot.say('[imgur] ' + '[' + gallery['title'] + \
                       ' - a gallery image with ' + str(gallery['views']) + \
                       ' views (' + str(gallery['ups']) + ' ups and ' + \
                       str(gallery['downs']) + ' downs)]')

def user(username, bot):
    """
    Handles information retrieval for user accounts.
    The bot will output the name, and the numbers of submissions, comments and
    liked resources, of the selected user.
    """
    client = ImgurClient(bot.config.imgur.client_id)
    account_api_url = "account/" + username
    try:
        json_account_response = client.request(account_api_url)
    except requests.HTTPError:
        return bot.say('[imgur] [User not found]')
    account = json_account_response['data']
    json_account_profile_response = client.request(account_api_url + '/gallery_profile')
    profile = json_account_profile_response['data']
    return bot.say('[imgur] ' + '[' + account['url'] + \
                   ' is an imgurian with ' + str(account['reputation']) + \
                   ' points of reputation, ' + str(profile['total_gallery_submissions']) + \
                   ' gallery submissions, ' + str(profile['total_gallery_comments']) + \
                   ' comments, ' + 'and ' + str(profile['total_gallery_likes']) + \
                   ' likes]')

def image(link_id, bot):
    """
    Handles information retrieval for non-gallery images.
    The bot will output the title, the type (image/gif) and the number of views
    of the selected image.
    """
    client = ImgurClient(bot.config.imgur.client_id)
    image_api_url = "image/" + link_id
    try:
        json_image_response = client.request(image_api_url)
    except requests.HTTPError:
        return bot.say('[imgur] [Image not found]')
    img = json_image_response['data']
    if img['title']:
        title = img['title']
    if not img['title'] and img['description']:
        title = img['description']
    if not img['title'] and not img['description']:
        title = 'untitled'
    if img['animated']:
        return bot.say('[imgur] ' + '[' + title + \
                       ' - a gif with ' + str(img['views']) + ' views]')
    else:
        return bot.say('[imgur] ' + '[' + title + \
                       ' - an image with ' + str(img['views']) + ' views]')

@rule('(?:https?://)?(?:i\.)?imgur\.com/(.*)$')
def imgur(bot, trigger):
    """
    Parses the input URL and calls the appropriate function for the resource
    (an image or an album).

    imgur has two types of resources: non-gallery and gallery resources.
    Non-gallery resources are images and albums that have not been uploaded
    to the imgur gallery (imgur.com/gallery), whilst gallery resources have
    been.

    * imgur.com/id can refer to two distinct resources (i.e. a non-gallery image
    and a gallery resource, e.g. imgur.com/VlmfH and imgur.com/gallery/VlmfH)

    * i.imgur.com/id refers by default to the same non-gallery resource as
      imgur.com/id, if there are two distinct resources for this ID.
      It refers to the gallery resource if only the gallery resource exists.

    * imgur.com/gallery/id refers solely to a gallery resource.

    * imgur.com/a/id refers solely to an album. Non-gallery data is returned,
      even if it is in the gallery.

    * imgur.com/user/username refers solely to an imgur user account.

    The regex rule above will capture either an ID to a gallery or non-gallery
    image or album, or a path to a certain imgur resource (e.g. gallery/id,
    user/username, and so forth).

    It is more foul-proof to only demand gallery data from the imgur API
    if we get a link that is of the form imgur.com/gallery/id, because
    imgur IDs are not unique (see above) and we can trigger an error if
    we request inexistant gallery data.
    """

    #urlparse does not support URLs without a scheme.
    #Add 'https' scheme to an URL if it has no scheme.
    if not urlparse(trigger).scheme:
        trigger = "https://" + trigger

    """Handle i.imgur.com links first.
    They can link to non-gallery images, so we do not request gallery data,
    but simply image data."""
    if urlparse(trigger).netloc == 'i.imgur.com':
        image_id = os.path.splitext(os.path.basename(urlparse(trigger).path))[0] # get the ID from the img
        return image(image_id, bot)

    """Handle imgur.com/* links."""
    #Get the path to the requested resource, from the URL (id, gallery/id, user/username, a/id)
    resource_path = urlparse(trigger).path.lstrip('/')
    #The following API endpoints require user authentication, which we do not support.
    unauthorized = ['settings', 'notifications', 'message', 'stats']
    if any(item in resource_path for item in unauthorized):
        return bot.reply("[imgur] Unauthorized action.")
    #Separate the URL path into an ordered list of the form ['gallery', 'id']
    resource_path_parts = filter(None, resource_path.split('/'))
    #Handle a simple link to imgur.com: no ID is given, meaning that the length of the above list is null
    if len(resource_path_parts) == 0:
        return
    #Handle a link with a path that has more than two components
    if len(resource_path_parts) > 2:
        return bot.reply("[imgur] Invalid link.")
    #Handle a link to an ID: imgur.com/id
    if len(resource_path_parts) == 1:
        return image(resource_path_parts[0], bot)
    #Handle a link to a gallery image/album: imgur.com/gallery/id
    if resource_path_parts[0] == 'gallery':
        return gallery(resource_path_parts[1], bot)
    #Handle a link to an user account/profile: imgur.com/user/username
    if resource_path_parts[0] == 'user':
        return user(resource_path_parts[1], bot)
    #Handle a link to an album: imgur.com/a/id
    if resource_path_parts[0] == 'a':
        return album(resource_path_parts[1], bot)
