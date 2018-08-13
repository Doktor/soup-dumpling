# Soup Dumpling

Soup Dumpling is a bot for the Telegram chat client. It lets you record people's posts ("quotes"), retrieve and search for quotes, and vote on quotes. It's written in Python 3 using the `python-telegram-bot` library.

Soup Dumpling requires Python 3.6.0 or later.

# Installation

1. Clone this repository: `git clone https://github.com/Doktor/soup-dumpling.git`
2. Add the bot's API key to the file `tokens/soup.txt`. To get an API key, message [@BotFather](https://telegram.me/BotFather).
3. Add the bot's username, including the preceding `@` symbol, to `tokens/username.txt`.
4. Install: `python setup.py install`.

The bot's entry point is named `soup`. You can use `systemd` or a similar system to run the bot as a service.

# Commands

## Anywhere

- `/about` Displays the current version, commit hash, and a link to this repository.
- `/count` Displays the number of quotes.
- `/help` Displays command reference. In groups, this only sends the list of available commands to reduce chat spam.
- `/most_added [n]` Displays the users who add the most quotes.
- `/most_quoted [n]` Displays the users with the most quotes.
- `/random` Displays a random quote.
- `/search <term>` Displays a random quote whose text contains `term`.
- `/stats` Displays three statistics: the number of quotes added, the users who are quoted the most often, and the users who add the most quotes.

## Groups

- `/addquote` Reply to any message to quote it. You can't quote messages sent by yourself or the bot itself, or non-text messages.

## Direct messages

You can browse the quotes of any chat you're in by sending direct messages to the bot, to reduce chat spam.

- `/chats`, `/start` Displays the list of chats you can browse.
- `/which` Displays the title of the chat you're browsing.
