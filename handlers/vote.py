from html import escape
from telegram.ext import Filters, CallbackQueryHandler, CommandHandler

from main import database, username
from handlers.quotes import create_vote_buttons

kwargs = {
    'filters': Filters.reply & Filters.group,
}

dm_kwargs = {
    'filters': Filters.reply & Filters.private,
    'pass_user_data': True,
}


def handle_vote(bot, update, user_data=None):
    query = update.callback_query

    user = query.from_user
    quote_message = query.message
    direction = int(query.data)

    if direction == 0:
        return query.answer('')

    current_chat_id = query.message.chat_id

    if user_data is None:
        quote_chat_id = current_chat_id
    else:
        quote_chat_id = user_data['current']

    quote_id = database.get_quote_id_from_message(
        quote_chat_id, quote_message.message_id)

    if quote_id is None:
        return query.answer('')

    status = database.add_vote(user.id, quote_id, direction)

    if status == database.VOTE_ADDED:
        response = "vote added!"
    elif status == database.ALREADY_VOTED:
        database.add_vote(user.id, quote_id, 0)
        response = "vote removed!"
    elif status == database.QUOTE_DELETED:
        response = "vote added and quote deleted!"

    query.answer(response)

    keyboard = create_vote_buttons(user.id, quote_id)

    bot.edit_message_reply_markup(
        chat_id=current_chat_id, message_id=quote_message.message_id,
        reply_markup=keyboard)


handler_vote = CallbackQueryHandler(handle_vote, pass_user_data=True)



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
