import logging
from datetime import datetime
from html import escape
from telegram.ext import Updater
from telegram.error import (BadRequest, ChatMigrated, NetworkError,
    TelegramError, TimedOut, Unauthorized)

from soup.database import QuoteDatabase


logging.basicConfig(
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)s | %(levelname)s @ %(name)s: %(message)s",
    level=logging.ERROR
)

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

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


def error_callback(bot, update, error):
    try:
        raise error
    except ChatMigrated as e:
        pass
    except (NetworkError, TimedOut) as e:
        pass
    except (BadRequest, TelegramError, Unauthorized) as e:
        logging.error(traceback.format_exc())


class QuoteBot:
    def __init__(self, token, handlers):
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher
        self.dispatcher.add_error_handler(error_callback)

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


from soup.handlers import *


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



