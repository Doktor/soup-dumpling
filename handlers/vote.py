from html import escape
from telegram.ext import Filters, CommandHandler

from main import database, username

kwargs = {
    'filters': Filters.reply & Filters.group,
}

dm_kwargs = {
    'filters': Filters.reply & Filters.private,
    'pass_user_data': True,
}


def handle_up(bot, update, user_data=None):
    return _handle_vote(bot, update, user_data=user_data, direction=1)


def handle_down(bot, update, user_data=None):
    return _handle_vote(bot, update, user_data=user_data, direction=-1)


def _handle_vote(bot, update, user_data=None, direction=-1):
    message = update.message

    quote = message.reply_to_message
    user = message.from_user

    # Users can only vote on quote messages sent by the bot
    if quote.from_user.username != username.lstrip('@'):
        return

    # Forwarded bot messages can't be tracked
    if quote.forward_from is not None:
        return

    if user_data is None:
        chat_id = message.chat_id
    else:
        chat_id = user_data['current']

    quote_id = database.get_quote_id_from_message(chat_id, quote.message_id)

    if quote_id is None:
        return

    status = database.add_vote(user.id, quote_id, direction)

    if status == database.VOTE_ADDED:
        response = "vote added, "
    elif status == database.ALREADY_VOTED:
        response = "already voted, "
    elif status == database.QUOTE_DELETED:
        response = "vote added and quote deleted, "

    up, score, down = database.get_votes_by_id(quote_id)

    response += f"current status: {score} points (+{up} / -{down})"
    message.reply_text(response)


handler_up = CommandHandler('up', handle_up, **kwargs)
dm_handler_up = CommandHandler('up', handle_up, **dm_kwargs)

handler_down = CommandHandler('down', handle_down, **kwargs)
dm_handler_down = CommandHandler('down', handle_down, **dm_kwargs)


def handle_votes(bot, update, user_data=None):
    message = update.message
    quote = message.reply_to_message

    # Votes are only counted on quote messages sent by the bot
    if quote.from_user.username != username.lstrip('@'):
        return

    # Forwarded bot messages can't be tracked
    if quote.forward_from is not None:
        return

    if user_data is None:
        chat_id = message.chat_id
    else:
        chat_id = user_data['current']

    up, score, down = database.get_votes(chat_id, quote.message_id)

    response = f"{score} points (+{up} / -{down})"
    message.reply_text(response)


handler_votes = CommandHandler('votes', handle_votes, **kwargs)
dm_handler_votes = CommandHandler('votes', handle_votes, **dm_kwargs)
