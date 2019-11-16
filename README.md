# Instagram Private API

An asyncio Python wrapper for the Instagram private API.

![Python 3.7, 3.8](https://img.shields.io/badge/Python-3.7%2C%203.8-3776ab.svg?maxAge=2592000)
[![Release](https://img.shields.io/github/release/Noctem/instagram_private_api.svg?colorB=ff7043)](https://github.com/Noctem/instagram_private_api/releases)
[![Docs](https://img.shields.io/badge/docs-readthedocs.io-ff4980.svg?maxAge=2592000)](https://instagram-private-api.readthedocs.io/en/latest/)
[![Build](https://img.shields.io/travis/com/Noctem/instagram_private_api.svg)](https://travis-ci.com/ping/instagram_private_api)

## Overview

I wrote this to access Instagram's API when they clamped down on developer access. Because this is meant to achieve [parity](COMPAT.md) with the [official public API](https://www.instagram.com/developer/endpoints/), methods not available in the public API will generally have lower priority.

Problems? Please check the [docs](https://instagram-private-api.readthedocs.io/en/latest/) before submitting an issue.

## Features

- Supports many functions that are only available through the official app, such as:
    * Multiple feeds, such as [user feed](https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.Client.user_feed), [location feed](https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.Client.feed_location), [tag feed](https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.Client.feed_tag), [popular feed](https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.Client.feed_popular)
    * [Like](https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.Client.post_like)/[unlike](https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.Client.delete_like) posts
    * Get [post comments](https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.Client.media_comments)
    * [Post](https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.Client.post_comment)/[delete](https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.Client.delete_comment) comments
    * [Like](https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.Client.comment_like)/[unlike](https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.Client.comment_unlike) comments
    * [Follow](https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.Client.friendships_create)/[unfollow](https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.Client.friendships_destroy) users
    * User [stories](https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.Client.user_story_feed)
    * And [more](https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.Client)!
- Compatible with functions available through the public API using the [ClientCompatPatch](https://instagram-private-api.readthedocs.io/en/latest/api.html#instagram_private_api.ClientCompatPatch) utility class

## Documentation

Documentation is available at https://instagram-private-api.readthedocs.io/en/latest/

## Install

Install with pip:

`pip install git+https://git@github.com/Noctem/instagram_private_api.git`

To update:

`pip install git+https://git@github.com/Noctem/instagram_private_api.git --upgrade`

Tested on Python 3.8.

## Usage

The [``examples/``](examples/) and [``tests/``](tests/) are a good source of detailed sample code on how to use the clients, including a simple way to save the auth cookie for reuse.

### Option 1: Use the [official app's API](instagram_private_api/)

```python
from asyncio import run

from instagram_private_api import Client, ClientCompatPatch

user_name = 'YOUR_LOGIN_USER_NAME'
password = 'YOUR_PASSWORD'

api = Client(user_name, password)
results = run(api.feed_timeline())
items = [item for item in results.get('feed_items', [])
         if item.get('media_or_ad')]
for item in items:
    # Manually patch the entity to match the public api as closely as possible, optional
    # To automatically patch entities, initialise the Client with auto_patch=True
    ClientCompatPatch.media(item['media_or_ad'])
    print(item['media_or_ad']['code'])
```

### Avoiding Re-login

You are advised to persist/cache the auth cookie details to avoid logging in every time you make an api call. Excessive logins is a surefire way to get your account flagged for removal. It's also advisable to cache the client details such as user agent, etc together with the auth details.

The saved auth cookie can be reused for up to **90 days**.

## Support

Make sure to review the [contributing documentation](CONTRIBUTING.md) before submitting an issue report or pull request.

## Legal

Disclaimer: This is not affliated, endorsed or certified by Instagram. This is an independent and unofficial API. Strictly **not for spam**. Use at your own risk.
