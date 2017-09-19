from datetime import datetime
from telegram.ext import CommandHandler, Filters

from handlers.quotes import dm_kwargs
from main import database, format_users, TIME_FORMAT


def handle_most_quoted(bot, update, user_data=None):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    total_count = database.get_quote_count(chat_id)
    most_quoted = database.get_most_quoted(chat_id, limit=15)

    response = ["<b>Users with the most quotes</b>"]
    response.extend(format_users(most_quoted, total_count))

    update.message.reply_text('\n'.join(response), parse_mode='HTML')


handler_most_quoted = CommandHandler(
    'most_quoted', handle_most_quoted, filters=Filters.group)
dm_handler_most_quoted = CommandHandler(
    'most_quoted', handle_most_quoted, **dm_kwargs)


def handle_most_added(bot, update, user_data=None):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    total_count = database.get_quote_count(chat_id)
    most_added = database.get_most_quotes_added(chat_id, limit=15)

    response = ["<b>Users who add the most quotes</b>"]
    response.extend(format_users(most_added, total_count))

    update.message.reply_text('\n'.join(response), parse_mode='HTML')


handler_most_added = CommandHandler(
    'most_added', handle_most_added, filters=Filters.group)
dm_handler_most_added = CommandHandler(
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


handler_stats = CommandHandler('stats', handle_stats, filters=Filters.group)
dm_handler_stats = CommandHandler('stats', handle_stats, **dm_kwargs)
