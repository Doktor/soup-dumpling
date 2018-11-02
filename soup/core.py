import contextlib
import functools
import json
import logging
import os
import traceback
from html import escape
from telegram.ext import ConversationHandler, Updater
from telegram.error import (BadRequest, ChatMigrated, NetworkError,
    TelegramError, TimedOut, Unauthorized)

from soup.database import QuoteDatabase


logging.basicConfig(
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)s | %(levelname)s @ %(name)s: %(message)s",
    level=logging.INFO
)

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# Truncate long quotes if they contain at least this many characters
TRUNCATE_LENGTH = 800

# Truncate search terms when no quotes are found
TRUNCATE_ARGS_LENGTH = 100

# Codes for direct message states
SELECT_CHAT = 1
SELECTED_CHAT = 2

DEBUG = os.path.isfile('debug')


# Load config file
CONFIG_FILENAME = 'config.json' if not DEBUG else 'config-dev.json'

with open(os.path.join('data', CONFIG_FILENAME)) as f:
    contents = f.read().strip()
    config = json.loads(contents)

username = config['username']
TOKEN = config['token']


# Global database object
FILENAME = 'test.db' if DEBUG else 'data.db'
database = QuoteDatabase(filename=FILENAME)


@contextlib.contextmanager
def session_scope():
    session = database.create_session()

    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


def session_wrapper(f):
    @functools.wraps(f)
    def with_session(*args, **kwargs):
        with session_scope() as session:
            kwargs.update(session=session)
            return f(*args, **kwargs)

    return with_session


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


def format_quote(quote, sent_by):
    """Creates the Telegram message for a quote."""
    text = quote.content_html
    name = sent_by.first_name
    date = quote.sent_at.strftime(TIME_FORMAT)

    # Truncate long quotes
    if len(text) > TRUNCATE_LENGTH:
        text = text[:TRUNCATE_LENGTH]
        return f'"{text}..." (truncated) - {name}\n<i>{date}</i>'
    else:
        return f'"{text}" - {name}\n<i>{date}</i>'


def format_users(users, total_count):
    """Creates the Telegram message with a list of users."""
    lines = []

    for user, count in users:
        name = "{} {}".format(user.first_name, user.last_name or '').rstrip()
        line = "• {0} ({1:.1%}): {2}".format(count, count / total_count, name)
        lines.append(escape(line))

    return lines


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

    quote = QuoteBot(TOKEN, handlers)
    quote.run()
