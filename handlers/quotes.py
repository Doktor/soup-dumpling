from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, CommandHandler

from main import database, TRUNCATE_ARGS_LENGTH, format_quote

dm_kwargs = {
    'filters': Filters.private,
    'pass_user_data': True
}


CHECK_MARK = '\u2705'
UP_ARROW = '\u2B06'
DOWN_ARROW = '\u2B07'


def create_vote_buttons(user_id, quote_id):
    upvotes, score, downvotes = database.get_votes_by_id(quote_id)
    vote = database.get_user_vote(user_id, quote_id)

    text_up = f'{UP_ARROW} ({upvotes})'
    text_zero = f'score {score}'
    text_down = f'{DOWN_ARROW} ({downvotes})'

    if vote == 0:
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


def handle_author(bot, update, args=list(), user_data=None):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    if not args:
        return
    else:
        args = ' '.join(args)

    user = update.message.from_user
    result = database.get_random_quote(chat_id, name=args)

    if len(args) > TRUNCATE_ARGS_LENGTH:
        args = args[:TRUNCATE_ARGS_LENGTH] + '...'

    if result is None:
        response = 'no quotes found by author "{}"'.format(escape(args))
        update.message.reply_text(response)
    else:
        votes = create_vote_buttons(user.id, result.quote.id)

        response = format_quote(*result)
        message = update.message.reply_text(
            response, parse_mode='HTML', reply_markup=votes)

        database.add_message(chat_id, message.message_id, result.quote.id)


handler_author = CommandHandler(
    'author', handle_author, filters=Filters.group, pass_args=True)
dm_handler_author = CommandHandler(
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
dm_handler_count = CommandHandler(
    'count', handle_count, pass_args=True, **dm_kwargs)


def handle_random(bot, update, user_data=None):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    user = update.message.from_user
    result = database.get_random_quote(chat_id)

    votes = create_vote_buttons(user.id, result.quote.id)

    if result is None:
        response = "no quotes in database"
        update.message.reply_text(response, reply_markup=votes)
    else:
        response = format_quote(*result)
        message = update.message.reply_text(
            response, parse_mode='HTML', reply_markup=votes)

        database.add_message(chat_id, message.message_id, result.quote.id)


handler_random = CommandHandler('random', handle_random, filters=Filters.group)
dm_handler_random = CommandHandler('random', handle_random, **dm_kwargs)


def handle_search(bot, update, args=list(), user_data=None):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    if not args:
        return
    else:
        args = ' '.join(args)

    user = update.message.from_user
    result = database.search_quote(chat_id, args)

    if len(args) > TRUNCATE_ARGS_LENGTH:
        args = args[:TRUNCATE_ARGS_LENGTH] + '...'

    if result is None:
        response = 'no quotes found for search terms "{}"'.format(args)
        update.message.reply_text(response)
    else:
        votes = create_vote_buttons(user.id, result.quote.id)

        response = format_quote(*result)
        message = update.message.reply_text(
            response, parse_mode='HTML', reply_markup=votes)

        database.add_message(chat_id, message.message_id, result.quote.id)


handler_search = CommandHandler(
    'search', handle_search, filters=Filters.group, pass_args=True)
dm_handler_search = CommandHandler(
    'search', handle_search, pass_args=True, **dm_kwargs)
