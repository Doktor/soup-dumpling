# Soup Dumpling

Soup Dumpling is a quote bot for the Telegram chat client. It's written in Python 3 using the `python-telegram-bot` library.

Soup Dumpling requires Python 3.6.0 or later.

# Public instance

I run a public instance of Soup Dumpling with the username [@soup_dumpling_bot](https://t.me/soup_dumpling_bot). You're welcome to add it to your groups. It runs 24/7 on my server, but I make no guarantees about uptime!

To report bugs or service outages, send me a direct message on [Twitter](https://twitter.com/DoktorTheHusky) and I'll respond as soon as possible.

# Setup

1. Clone this repository: `git clone https://github.com/Doktor/soup-dumpling.git`
2. Add the bot's API key to the file `tokens/soup.txt`. To get an API key, message [@BotFather](https://telegram.me/BotFather).
3. Add the bot's username, including the preceding `@` symbol, to `tokens/username.txt`.

# Running

## Supervisor

[Supervisor](http://supervisord.org/) is the preferred way of running the bot. Requires `supervisor` 3.0+ and `virtualenvwrapper`.

1. Run the install script: `source install.sh`
2. To stop/start the bot: `supervisorctl stop/start soup-dumpling`

## Temporary

This method isn't recommended for running the bot long-term.

1. Install the required packages: `pip install -r requirements.txt`
2. Start the bot: `python3.6 quote.py`

# Commands

## Anywhere

- `/about` Displays the current version, commit hash, and a link to this repository.
- `/author <name>` Displays a random quote from a user whose name or username contains `name`.
- `/help` Displays command reference. In groups, this only sends the list of available commands to reduce chat spam.
- `/quotes [search]` Displays the number of quotes added, or the number of quotes whose text or author's name contains `search`.
- `/random` Displays a random quote.
- `/search <term>` Displays a random quote whose text contains `term`.
- `/stats` Displays three statistics: the number of quotes added, the users who are quoted the most often, and the users who add the most quotes.

## Groups

- `/addquote` Reply to any message to quote it. You can't quote messages sent by yourself or a bot, or non-text messages.

## Direct messages

You can browse the quotes of any chat you're in by sending direct messages to the bot, to reduce chat spam.

- `/chats` or `/start` Displays the list of chats you can browse.
- `/which` Displays the title of the chat you're browsing.
