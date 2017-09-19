from html import escape

from telegram.ext import Filters, CommandHandler

from main import database, TRUNCATE_ARGS_LENGTH, format_quote

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

    result = database.get_random_quote(chat_id)

    if result is None:
        response = "no quotes in database"
    else:
        response = format_quote(*result)

    update.message.reply_text(response, parse_mode='HTML')


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
dm_handler_search = CommandHandler(
    'search', handle_search, pass_args=True, **dm_kwargs)
