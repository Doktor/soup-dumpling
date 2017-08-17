# Soup Dumpling

Soup Dumpling is a simple quote bot for the Telegram chat client. It's written in Python 3 using the `python-telegram-bot` library.

# Setup

1. Clone this repository: `git clone https://github.com/Doktor/soup-dumpling.git`
2. Add your API key to the file `tokens/soup.txt`. To get an API key, message [@BotFather](https://telegram.me/BotFather).
3. Add the bot's username, including the preceding `@` symbol, to `tokens/username.txt`.

# Running

## Supervisor

[Supervisor](http://supervisord.org/) is the preferred way of running the bot. Requires `supervisor` 3.0+ and `virtualenvwrapper`.

1. Run the install script: `source install.sh`
2. To stop/start the bot: `supervisorctl stop/start soup-dumpling`

## Temporary

1. Install the required packages: `pip install -r requirements.txt`
2. Start the bot: `python3 quote.py`.

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
