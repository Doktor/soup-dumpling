import functools
from datetime import datetime
from html import escape
from telegram.ext import CommandHandler, Filters

from soup.core import database, format_users, TIME_FORMAT
from soup.handlers.quotes import dm_kwargs


def parse_limit(args, default=15):
    """Parses the arguments as an integer, or return the default value
    if it's not a valid integer or if the value isn't positive."""
    if args is None:
        return default

    try:
        limit = int(''.join(args))
    except ValueError:
        return default

    return limit if limit > 0 else default


def handle_stats(bot, update,
        args=None, user_data=None, general=True, quoted=True, added=True):

    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    limit = parse_limit(args, default=5)
    response = list()

    first = database.get_first_quote(chat_id)
    last = database.get_last_quote(chat_id)

    if first is None:
        assert last is None

        response = "no quotes in database"
        update.message.reply_text(response)
        return

    total_count = database.get_quote_count(chat_id)

    if general:
        # Total quotes
        response.append("<b>Overall</b>")
        response.append("• {0} total quotes".format(total_count))

        # First and last quote
        fts = datetime.fromtimestamp(first.quote.sent_at).strftime(TIME_FORMAT)
        lts = datetime.fromtimestamp(last.quote.sent_at).strftime(TIME_FORMAT)

        response.append(
            "• First: {0} by {1}".format(fts, first.user.first_name))
        response.append(
            "• Last: {0} by {1}".format(lts, last.user.first_name))
        response.append("")

    if quoted:
        most_quoted = database.get_most_quoted(chat_id, limit=limit)

        response.append("<b>Users with the most quotes</b>")
        response.extend(format_users(most_quoted, total_count))
        response.append("")

    if added:
        added_most = database.get_most_quotes_added(chat_id, limit=limit)

        response.append("<b>Users who add the most quotes</b>")
        response.extend(format_users(added_most, total_count))

    update.message.reply_text('\n'.join(response).rstrip(), parse_mode='HTML')


handler_stats = CommandHandler(
    'stats', handle_stats, filters=Filters.group)
dm_handler_stats = CommandHandler(
    'stats', handle_stats, pass_args=True, **dm_kwargs)


handle_most_quoted = functools.partial(
    handle_stats, general=False, quoted=True, added=False)

handler_most_quoted = CommandHandler(
    'most_quoted', handle_most_quoted, filters=Filters.group)
dm_handler_most_quoted = CommandHandler(
    'most_quoted', handle_most_quoted, pass_args=True, **dm_kwargs)


handle_most_added = functools.partial(
    handle_stats, general=False, quoted=False, added=True)

handler_most_added = CommandHandler(
    'most_added', handle_most_added, filters=Filters.group)
dm_handler_most_added = CommandHandler(
    'most_added', handle_most_added, pass_args=True, **dm_kwargs)


def format_user_scores(scores):
    temp = []

    for first, last, up, score, down in scores:
        t = f"• {score} (+{up}/-{down}): {first} {last or ''}".strip()
        temp.append(escape(t))

    return temp


def handle_scores(bot, update, args=None, user_data=None, high=True, low=True):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    limit = parse_limit(args, default=5)

    response = []

    if high:
        # Highest scores
        high_scores = database.get_highest_scoring(chat_id, limit=limit)

        response.append("<b>Users with the highest scores</b>")
        response.extend(format_user_scores(high_scores))

    if high and low:
        response.append("")

    if low:
        # Lowest scores
        low_scores = database.get_lowest_scoring(chat_id, limit=limit)

        response.append("<b>Users with the lowest scores</b>")
        response.extend(format_user_scores(low_scores))

    update.message.reply_text('\n'.join(response), parse_mode='HTML')


handler_scores = CommandHandler(
    'scores', handle_scores, filters=Filters.group)
dm_handler_scores = CommandHandler(
    'scores', handle_scores, pass_args=True, **dm_kwargs)


handle_hi_scores = functools.partial(handle_scores, high=True, low=False)

handler_hi_scores = CommandHandler(
    'hi_scores', handle_hi_scores, filters=Filters.group)
dm_handler_hi_scores = CommandHandler(
    'hi_scores', handle_hi_scores, pass_args=True, **dm_kwargs)


handle_lo_scores = functools.partial(handle_scores, high=False, low=True)

handler_lo_scores = CommandHandler(
    'lo_scores', handle_lo_scores, filters=Filters.group)
dm_handler_lo_scores = CommandHandler(
    'lo_scores', handle_lo_scores, pass_args=True, **dm_kwargs)
