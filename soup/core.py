import contextlib
import datetime
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


DEBUG = os.path.isfile('debug')

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

# Maximum message and caption length
MAX_MESSAGE_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024

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


class QuoteBot:
    def __init__(self, token, handlers):
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher
        self.dispatcher.add_error_handler(self.error_callback)

        for i, handler in enumerate(handlers):
            self.dispatcher.add_handler(handler, group=i)

    @staticmethod
    def error_callback(bot, update, error):
        try:
            raise error
        except ChatMigrated as e:
            pass
        except (NetworkError, TimedOut) as e:
            pass
        except (BadRequest, TelegramError, Unauthorized) as e:
            logging.error(traceback.format_exc())

    def run(self):
        self.updater.start_polling()
        self.updater.idle()


def main():
    from soup.handlers import handlers

    quote = QuoteBot(TOKEN, handlers)
    quote.run()


if __name__ == '__main__':
    logging.info("[%s] running" % datetime.datetime.now())
    main()
