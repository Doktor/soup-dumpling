import functools
from html import escape
from telegram.ext import CommandHandler, Filters

from soup.core import database, TIME_FORMAT, session_wrapper
from soup.utils import format_users
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


@session_wrapper
def handle_stats(bot, update, args=None, user_data=None, general=True,
        quoted=True, added=True, session=None):

    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    limit = parse_limit(args, default=5)
    response = list()

    total_count = database.get_quote_count(session, chat_id)

    if not total_count:
        return update.message.reply_text("no quotes in database")

    if general:
        # Total quotes
        response.append("<b>Overall</b>")
        response.append("• {0} total quotes".format(total_count))

    if quoted:
        most_quoted = database.get_most_quoted(session, chat_id, limit=limit)

        response.append("<b>Users with the most quotes</b>")
        response.extend(format_users(most_quoted, total_count))
        response.append("")

    if added:
        most_added = database.get_most_quotes_added(
            session, chat_id, limit=limit)

        response.append("<b>Users who add the most quotes</b>")
        response.extend(format_users(most_added, total_count))

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

    for user, up, score, down in scores:
        t = (f"• {score} (+{up}/-{down}): "
             f"{user.first_name} {user.last_name or ''}".strip())
        temp.append(escape(t))

    return temp


@session_wrapper
def handle_scores(bot, update, args=None, user_data=None, high=True, low=True,
        session=None):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    limit = parse_limit(args, default=5)
    response = []

    if high:
        high_scores = database.get_highest_scoring(
            session, chat_id, limit=limit)

        response.append("<b>Users with the highest scores</b>")
        response.extend(format_user_scores(high_scores))

    if high and low:
        response.append("")

    if low:
        low_scores = database.get_lowest_scoring(
            session, chat_id, limit=limit)

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
