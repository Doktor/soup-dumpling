from telegram import InlineKeyboardButton, InlineKeyboardMarkup, TelegramError
from telegram.ext import CallbackQueryHandler, CommandHandler, Filters

from soup.core import (
    database, TRUNCATE_ARGS_LENGTH, session_wrapper)
from soup.utils import format_quote
from soup.handlers.search_tags import create_tag, PATTERN

dm_kwargs = {
    'filters': Filters.private,
    'pass_user_data': True
}


CHECK_MARK = '\u2705'
UP_ARROW = '\u2B06'
DOWN_ARROW = '\u2B07'


def create_vote_buttons(user_id, quote_id, direct=False, session=None):
    upvotes, score, downvotes = database.get_votes_by_id(session, quote_id)

    text_up = f'{UP_ARROW} ({upvotes})'
    text_zero = f'score {score}'
    text_down = f'{DOWN_ARROW} ({downvotes})'

    if direct:
        vote = database.get_user_vote(session, user_id, quote_id)

        if vote == 0 or vote is None:
            pass
        elif vote == 1:
            text_up = CHECK_MARK + text_up
        elif vote == -1:
            text_down = CHECK_MARK + text_down

    up = InlineKeyboardButton(text_up, callback_data='1')
    zero = InlineKeyboardButton(text_zero, callback_data='0')
    down = InlineKeyboardButton(text_down, callback_data='-1')

    options = [up, zero, down]
    keyboard = InlineKeyboardMarkup([options])

    return keyboard


@session_wrapper
def handle_vote(bot, update, user_data, session=None):
    query = update.callback_query

    user = query.from_user
    quote_message = query.message
    data = int(query.data)

    current_chat_id = query.message.chat_id

    # Check if the query originated from a direct message:
    # callback query handlers don't accept filters
    direct = current_chat_id == user.id

    if direct:
        quote_chat_id = user_data['current']
    else:
        quote_chat_id = current_chat_id

    quote_id = database.get_quote_id_from_message(
        session, quote_chat_id, quote_message.message_id)

    if quote_id is None:
        return query.answer('')

    if data == 0:
        vote = database.get_user_vote(session, user.id, quote_id).direction

        if vote == 0:
            return query.answer("you haven't voted on this quote!")
        elif vote == 1:
            return query.answer(f"{UP_ARROW} you upvoted this quote")
        elif vote == -1:
            return query.answer(f"{DOWN_ARROW} you downvoted this quote")

    status = database.add_vote(session, user.id, quote_id, data)

    if status == database.VOTE_ADDED:
        if data == 1:
            response = "upvoted!"
        elif data == -1:
            response = "downvoted!"
    elif status == database.ALREADY_VOTED:
        database.add_vote(session, user.id, quote_id, 0)
        response = "vote removed!"
    elif status == database.QUOTE_DELETED:
        response = "vote added and quote deleted!"
        query.answer(response)

        for qm in database.get_quote_messages(session, quote_id):
            try:
                bot.edit_message_text(
                    chat_id=qm.chat_id, message_id=qm.message_id,
                    text="[quote was deleted]", reply_markup=[])
            except TelegramError:
                # The message is over 48 hours old and can't be edited
                pass

        return

    query.answer(response)

    keyboard = create_vote_buttons(
        user.id, quote_id, direct=direct, session=session)

    bot.edit_message_reply_markup(
        chat_id=current_chat_id, message_id=quote_message.message_id,
        reply_markup=keyboard)


handler_vote = CallbackQueryHandler(handle_vote, pass_user_data=True)


@session_wrapper
def handle_random(bot, update, user_data=None, session=None):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    quote, sent_by = database.get_random_quote(session, chat_id)

    if quote is None:
        update.message.reply_text("no quotes in database")
    else:
        user = update.message.from_user
        votes = create_vote_buttons(
            user.id, quote.id, direct=user_data is not None, session=session)

        response = format_quote(quote, sent_by)
        message = update.message.reply_text(
            response, parse_mode='HTML', reply_markup=votes)

        database.add_message(session, chat_id, message.message_id, quote)


handler_random = CommandHandler('random', handle_random, filters=Filters.group)
dm_handler_random = CommandHandler('random', handle_random, **dm_kwargs)


@session_wrapper
def handle_search(bot, update, args=list(), user_data=None, session=None):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    if not args:
        return

    terms, tags = [], []

    for item in args:
        match = PATTERN.search(item)

        # Tags
        if match is not None:
            groups = match.groups()

            if len(groups) == 2:
                name, value = groups
                cmp = None
            elif len(groups) == 3:
                name, cmp, value = groups

            tag = create_tag(name, value, cmp=cmp)
            tags.append(tag)
        # Search terms
        else:
            terms.append(item)

    terms = ' '.join(terms)
    quote, user = database.search_quote(session, chat_id, terms, tags)

    if len(args) > TRUNCATE_ARGS_LENGTH:
        args = args[:TRUNCATE_ARGS_LENGTH] + '...'

    from_user = update.message.from_user

    if quote is None:
        update.message.reply_text("no quotes found")
    else:
        votes = create_vote_buttons(
            from_user.id, quote.id, direct=user_data is not None,
            session=session)

        response = format_quote(quote, user)
        message = update.message.reply_text(
            response, parse_mode='HTML', reply_markup=votes)

        database.add_message(session, chat_id, message.message_id, quote)


handler_search = CommandHandler(
    'search', handle_search, filters=Filters.group, pass_args=True)
dm_handler_search = CommandHandler(
    'search', handle_search, pass_args=True, **dm_kwargs)
