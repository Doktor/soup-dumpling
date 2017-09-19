import logging
from datetime import datetime
from telegram.ext import Updater

from database import QuoteDatabase
from handlers import *


logging.basicConfig(
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)s | %(levelname)s @ %(name)s: %(message)s",
    level=logging.INFO
)

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

VERSION = (2, 0, 0)

# Truncate long quotes if they contain at least this many characters
TRUNCATE_LENGTH = 800

# Truncate search terms when no quotes are found
TRUNCATE_ARGS_LENGTH = 100

# Codes for direct message states
SELECT_CHAT = 1
SELECTED_CHAT = 2

# The bot's Telegram username
with open('tokens/username.txt', 'r') as f:
    username = f.read().strip()

# Global database object
database = QuoteDatabase()


class QuoteBot:
    def __init__(self, token, handlers):
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher

        for i, handler in enumerate(handlers):
            self.dispatcher.add_handler(handler, group=i)

    def run(self):
        self.updater.start_polling()
        self.updater.idle()


def chunks(l, size):
    """Yields chunks of items from a list."""
    for i in range(0, len(l), size):
        yield l[i:i + size]


def format_quote(quote, user):
    """Creates the Telegram message for a quote."""
    text = quote.content_html
    date = datetime.fromtimestamp(quote.sent_at).strftime(TIME_FORMAT)

    # Truncate long quotes
    if len(text) > TRUNCATE_LENGTH:
        text = text[:TRUNCATE_LENGTH]
        template = '"{text}..." (truncated) - {name}\n<i>{date}</i>'
    else:
        template = '"{text}" - {name}\n<i>{date}</i>'

    message = template.format(text=text, name=user.first_name, date=date)
    return message


def format_users(users, total_count):
    """Creates the Telegram message with a list of users."""
    ret = []
    for count, first, last in users:
        name = "{} {}".format(first, last or '').rstrip()
        line = "• {0} ({1:.1%}): {2}".format(count, count / total_count, name)
        ret.append(escape(line))
    return ret


def main():
    ns = globals()

    dm_handlers = [v for k, v in ns.items() if k.startswith('dm_handler')]

    handler_dm = ConversationHandler(
        entry_points=start_handlers,
        states={
            SELECT_CHAT: [dm_only_handler_select],
            SELECTED_CHAT: [dm_only_handler_which] + dm_handlers,
        },
        fallbacks=[dm_only_handler_cancel],
        allow_reentry=True
    )

    handlers = [v for k, v in ns.items() if k.startswith('handler')]
    handlers += [handler_dm]

    with open('tokens/soup.txt', 'r') as f:
        token = f.read().strip()

    quote = QuoteBot(token, handlers)
    quote.run()


if __name__ == '__main__':
    print("[%s] running" % datetime.now())
    main()
