import json
import logging
import time
from datetime import datetime
from html import escape
from subprocess import check_output
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (CommandHandler, ConversationHandler, Filters,
    MessageHandler, Updater)

from classes import Chat, User
from database import QuoteDatabase

logging.basicConfig(
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)s | %(levelname)s @ %(name)s: %(message)s",
    level=logging.DEBUG
)

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

REPOSITORY_NAME = "Doktor/soup-dumpling"
REPOSITORY_URL = "https://github.com/Doktor/soup-dumpling"

COMMIT_HASH = check_output(['git', 'rev-parse', 'HEAD'],
    encoding='utf8').rstrip('\n')
COMMIT_URL = REPOSITORY_URL + '/commit/' + COMMIT_HASH

DATE_ARGS = ['git', 'log', COMMIT_HASH,
    '-1', '--date=iso', r'--pretty=format:%cd']
COMMIT_DATE = check_output(DATE_ARGS, encoding='utf8')[:19]

# The relative date is used for the 'about' command
DATE_ARGS[4] = '--date=relative'

VERSION = (1, 2, 0)

# Codes for direct message states
SELECT_CHAT = 1
SELECTED_CHAT = 2

# Truncate long quotes if they contain at least this many characters
TRUNCATE_LENGTH = 800

# Truncate search terms when no quotes are found
TRUNCATE_ARGS_LENGTH = 100

database = QuoteDatabase()

with open('tokens/soup.txt', 'r') as f:
    token = f.read().strip()

with open('tokens/username.txt', 'r') as f:
    username = f.read().strip()


class QuoteBot:
    def __init__(self, token, username, handlers):
        self.updater = Updater(token)
        self.dispatcher = self.updater.dispatcher

        for i, handler in enumerate(handlers):
            self.dispatcher.add_handler(handler, group=i)

    def run(self):
        self.updater.start_polling()
        self.updater.idle()


# Helper functions


def chunks(l, size):
    for i in range(0, len(l), size):
        yield l[i:i + size]


def format_quote(quote, user):
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
    ret = []
    for count, first, last in users:
        name = "{} {}".format(first, last or '').rstrip()
        line = "• {0} ({1:.1%}): {2}".format(count, count / total_count, name)
        ret.append(escape(line))
    return ret


# Groups and direct messages


def handle_about(bot, update):
    info = {
        'version': '.'.join((str(n) for n in VERSION)),
        'updated': COMMIT_DATE,
        'updated_rel': check_output(DATE_ARGS, encoding='utf8'),
        'repo_url': REPOSITORY_URL,
        'repo_name': REPOSITORY_NAME,
        'hash_url': COMMIT_URL,
        'hash': COMMIT_HASH[:7],
    }

    response = [
        '"Nice quote!" - <b>Soup Dumpling {version}</b>',
        '<i>{updated} ({updated_rel})</i>',
        '',
        'Source code at <a href="{repo_url}">{repo_name}</a>',
        'Running on commit <a href="{hash_url}">{hash}</a>',
    ]

    response = '\n'.join(response).format(**info)

    update.message.reply_text(response,
        quote=False, disable_web_page_preview=True, parse_mode='HTML')

handler_about = CommandHandler('about', handle_about)


with open('help.txt', 'r', encoding='utf8') as f:
    help_text = f.read().strip()


def handle_help(bot, update):
    kwargs = {
        'version': '.'.join((str(n) for n in VERSION)),
        'readme': REPOSITORY_URL + "/blob/master/README.md"
    }
    response = help_text.format(**kwargs)

    update.message.reply_text(response,
        disable_web_page_preview=True, quote=False, parse_mode='HTML')

handler_help = CommandHandler('help', handle_help, filters=Filters.private)


def handle_help_group(bot, update):
    kwargs = {
        'version': '.'.join((str(n) for n in VERSION)),
        'username': username,
    }

    response = [
        '"Nice help!" - <b>Soup Dumpling {version}</b>',
        '',
        '• <b>Groups</b>: /addquote',
        ('• <b>Anywhere</b>: /about, /author &lt;name&gt;, /count [term], '
        '/help, /most_added, /most_quoted, /random, /search &lt;term&gt;, '
        '/stats'),
        '• <b>Direct messages</b>: /chats or /start, /which',
        '',
        'For extended help, DM <code>/help</code> to {username}',
    ]

    response = '\n'.join(response).format(**kwargs)

    update.message.reply_text(response,
        disable_web_page_preview=True, quote=False, parse_mode='HTML')

handler_help_group = CommandHandler(
    'help', handle_help_group, filters=Filters.group)


def handle_database(bot, update):
    user = update.message.from_user
    chat = update.message.chat

    database.add_or_update_user(User.from_telegram(user))

    if user.id != chat.id:
        database.add_or_update_chat(Chat.from_telegram(chat))
        database.add_membership(user.id, chat.id)

handler_database = MessageHandler(Filters.text, handle_database)


# Groups only


def handle_addquote(bot, update):
    message = update.message
    quote = update.message.reply_to_message

    assert quote is not None

    # Only text messages can be added as quotes
    if quote.text is None:
        return

    chat_id = message.chat.id
    message_id = quote.message_id
    quoted_by = message.from_user

    # Forwarded messages
    is_forward = quote.forward_from is not None

    if is_forward:
        sent_by = quote.forward_from
        sent_at = quote.forward_date.timestamp()
    else:
        sent_by = quote.from_user
        sent_at = quote.date.timestamp()

    # Bot messages can't be added as quotes
    if sent_by.username == username.lstrip('@'):
        response = "can't quote bot messages"
        return update.message.reply_text(response)

    # Users can't add their own messages as quotes
    if sent_by.id == quoted_by.id:
        response = "can't quote own messages"
        return update.message.reply_text(response)

    database.add_or_update_user(User.from_telegram(sent_by))
    database.add_or_update_user(User.from_telegram(quoted_by))

    result = database.add_quote(
        chat_id, message_id, is_forward,
        sent_at, sent_by.id, quote.text, quote.text_html, quoted_by.id)

    if result == QuoteDatabase.QUOTE_ADDED:
        response = "quote added"
    elif result == QuoteDatabase.QUOTE_ALREADY_EXISTS:
        response = "quote already exists"

    update.message.reply_text(response)

handler_addquote = CommandHandler(
    'addquote', handle_addquote, filters=Filters.reply & Filters.group)


# Groups and direct messages (separate handlers)

dm_kwargs = {
    'filters': Filters.private,
    'pass_user_data': True
}


def handle_author(bot, update, args=list(), user_data=None):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    if not args:
        return
    else:
        args = ' '.join(args)

    result = database.get_random_quote(chat_id, name=args)

    if len(args) > TRUNCATE_ARGS_LENGTH:
        args = args[:TRUNCATE_ARGS_LENGTH] + '...'

    if result is None:
        response = 'no quotes found by author "{}"'.format(escape(args))
    else:
        response = format_quote(*result)

    update.message.reply_text(response, parse_mode='HTML')

handler_author = CommandHandler(
    'author', handle_author, filters=Filters.group, pass_args=True)
_handler_author_dm = CommandHandler(
    'author', handle_author, pass_args=True, **dm_kwargs)


def handle_count(bot, update, args=list(), user_data=None):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    args = ' '.join(args)

    if len(args) > TRUNCATE_ARGS_LENGTH:
        args = args[:TRUNCATE_ARGS_LENGTH] + '...'

    if not args:
        count = database.get_quote_count(chat_id)
        response = "{0} quotes in this chat".format(count)
    else:
        content, author = database.get_quote_count(chat_id, search=args)
        response = (
            '{0} quotes in this chat for search term "{1}"\n'
            '{2} content matches, {3} author matches'
        ).format(content + author, args, content, author)

    update.message.reply_text(response)

handler_count = CommandHandler(
    'count', handle_count, filters=Filters.group, pass_args=True)
_handler_count_dm = CommandHandler(
    'count', handle_count, pass_args=True, **dm_kwargs)


def handle_random(bot, update, user_data=None):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    result = database.get_random_quote(chat_id)

    if result is None:
        response = "no quotes in database"
    else:
        response = format_quote(*result)

    update.message.reply_text(response, parse_mode='HTML')

handler_random = CommandHandler(
    'random', handle_random, filters=Filters.group)
_handler_random_dm = CommandHandler(
    'random', handle_random, **dm_kwargs)


def handle_search(bot, update, args=list(), user_data=None):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    if not args:
        return
    else:
        args = ' '.join(args)

    result = database.search_quote(chat_id, args)

    if len(args) > TRUNCATE_ARGS_LENGTH:
        args = args[:TRUNCATE_ARGS_LENGTH] + '...'

    if result is None:
        response = 'no quotes found for search terms "{}"'.format(args)
        update.message.reply_text(response)
    else:
        response = format_quote(*result)
        update.message.reply_text(response, parse_mode='HTML')

handler_search = CommandHandler(
    'search', handle_search, filters=Filters.group, pass_args=True)
_handler_search_dm = CommandHandler(
    'search', handle_search, pass_args=True, **dm_kwargs)


def handle_most_quoted(bot, update, user_data=None):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    total_count = database.get_quote_count(chat_id)
    most_quoted = database.get_most_quoted(chat_id, limit=15)

    response = []
    response.append("<b>Users with the most quotes</b>")
    response.extend(format_users(most_quoted, total_count))

    update.message.reply_text('\n'.join(response), parse_mode='HTML')

handler_most_quoted = CommandHandler(
    'most_quoted', handle_most_quoted, filters=Filters.group)
_handler_most_quoted_dm = CommandHandler(
    'most_quoted', handle_most_quoted, **dm_kwargs)


def handle_most_added(bot, update, user_data=None):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    total_count = database.get_quote_count(chat_id)
    most_added = database.get_most_quotes_added(chat_id, limit=15)

    response = []
    response.append("<b>Users who add the most quotes</b>")
    response.extend(format_users(most_added, total_count))

    update.message.reply_text('\n'.join(response), parse_mode='HTML')

handler_most_added = CommandHandler(
    'most_added', handle_most_added, filters=Filters.group)
_handler_most_added_dm = CommandHandler(
    'most_added', handle_most_added, **dm_kwargs)


def handle_stats(bot, update, user_data=None):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    response = list()

    # Total quotes
    total_count = database.get_quote_count(chat_id)

    response.append("<b>Overall</b>")
    response.append("• {0} total quotes".format(total_count))

    # First and last quote
    first = database.get_first_quote(chat_id)
    last = database.get_last_quote(chat_id)

    if first is None:
        assert last is None

        response = "no quotes in database"
        update.message.reply_text(response)
        return

    first_ts = datetime.fromtimestamp(first.quote.sent_at).strftime(TIME_FORMAT)
    last_ts = datetime.fromtimestamp(last.quote.sent_at).strftime(TIME_FORMAT)

    response.append(
        "• First: {0} by {1}".format(first_ts, first.user.first_name))
    response.append(
        "• Last: {0} by {1}".format(last_ts, last.user.first_name))
    response.append("")

    # Users
    most_quoted = database.get_most_quoted(chat_id, limit=5)

    response.append("<b>Users with the most quotes</b>")
    response.extend(format_users(most_quoted, total_count))
    response.append("")

    added_most = database.get_most_quotes_added(chat_id, limit=5)

    response.append("<b>Users who add the most quotes</b>")
    response.extend(format_users(added_most, total_count))

    update.message.reply_text('\n'.join(response), parse_mode='HTML')

handler_stats = CommandHandler(
    'stats', handle_stats, filters=Filters.group)
_handler_stats_dm = CommandHandler(
    'stats', handle_stats, **dm_kwargs)


# Direct messages only


def handle_cancel(bot, update, user_data):
    user_data['current'] = None
    update.message.reply_text('canceled')
    return ConversationHandler.END

_handler_cancel = CommandHandler(
    'cancel', handle_cancel, **dm_kwargs)


def handle_start(bot, update, user_data):
    user_id = update.message.from_user.id

    chats = database.get_chats(user_id)

    if not chats:
        response = "<b>Chat selection</b>\nno chats found"
        update.message.reply_text(response, parse_mode='HTML')
        return ConversationHandler.END

    response = [
        "<b>Chat selection</b>",
        "Choose a chat by its number or title:",
        "",
    ]

    mapping = []
    for i, (chat_id, chat_title) in enumerate(chats):
        response.append("<b>[{0}]</b> {1}".format(i, escape(chat_title)))
        mapping.append([i, chat_id, chat_title])

    user_data['choices'] = mapping
    response = '\n'.join(response)

    if len(chats) < 6:
        # Use a reply keyboard
        titles = [chat[1] for chat in chats]
        reply_keyboard = list(chunks(titles, 2))
        markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True)

        update.message.reply_text(
            response, parse_mode='HTML', reply_markup=markup)
    else:
        # Too many choices: send the choices in a message
        update.message.reply_text(response, parse_mode='HTML')

    return SELECT_CHAT

_handler_start = CommandHandler(
    'start', handle_start, **dm_kwargs)
_handler_chats = CommandHandler(
    'chats', handle_start, **dm_kwargs)

dm_start_handlers = [_handler_start, _handler_chats]


def handle_select_chat(bot, update, user_data):
    choice = update.message.text

    try:
        i = int(choice)
        _, selected_id, title = user_data['choices'][i]
    except IndexError:
        update.message.reply_text("invalid chat number")
        return SELECT_CHAT
    except ValueError:
        try:
            _, selected_id, title = next(filter(
                lambda chat: choice.lower() in chat[2].lower(),
                user_data['choices']))
        except StopIteration:
            update.message.reply_text("no titles matched")
            return SELECT_CHAT

    user_data['current'] = selected_id

    response = 'selected chat "{0}"'.format(title)
    update.message.reply_text(response, reply_markup=ReplyKeyboardRemove())

    return SELECTED_CHAT

_handler_select_chat = MessageHandler(
    Filters.text, handle_select_chat, pass_user_data=True)


def handle_which(bot, update, user_data):
    chat = database.get_chat_by_id(user_data['current'])

    response = 'searching quotes from "{0}"'.format(escape(chat.title))
    update.message.reply_text(response)

_handler_which = CommandHandler(
    'which', handle_which, **dm_kwargs)


dm_handlers = [v for k, v in globals().items() if
    k.startswith('_handler') and k.endswith('_dm')]

handler_dm = ConversationHandler(
    entry_points=dm_start_handlers,
    states={
        SELECT_CHAT: [_handler_select_chat],
        SELECTED_CHAT: [_handler_which] + dm_handlers,
    },
    fallbacks=[_handler_cancel],
    allow_reentry=True
)


def main():
    handlers = [v for k, v in globals().items() if k.startswith('handler')]

    quote = QuoteBot(token, username, handlers)
    quote.run()


if __name__ == '__main__':
    print("[%s] running" % datetime.now())
    main()
