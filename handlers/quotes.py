import datetime
import random
import re
import pytz
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, TelegramError
from telegram.ext import CallbackQueryHandler, CommandHandler, Filters

from main import database, TRUNCATE_ARGS_LENGTH, format_quote

dm_kwargs = {
    'filters': Filters.private,
    'pass_user_data': True
}


CHECK_MARK = '\u2705'
UP_ARROW = '\u2B06'
DOWN_ARROW = '\u2B07'


def create_vote_buttons(user_id, quote_id, direct=False):
    upvotes, score, downvotes = database.get_votes_by_id(quote_id)

    text_up = f'{UP_ARROW} ({upvotes})'
    text_zero = f'score {score}'
    text_down = f'{DOWN_ARROW} ({downvotes})'

    if direct:
        vote = database.get_user_vote(user_id, quote_id)

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


def handle_vote(bot, update, user_data):
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
        quote_chat_id, quote_message.message_id)

    if quote_id is None:
        return query.answer('')

    if data == 0:
        vote = database.get_user_vote(user.id, quote_id)

        if vote == 0:
            return query.answer("you haven't voted on this quote!")
        elif vote == 1:
            return query.answer(f"{UP_ARROW} you upvoted this quote")
        elif vote == -1:
            return query.answer(f"{DOWN_ARROW} you downvoted this quote")

    status = database.add_vote(user.id, quote_id, data)

    if status == database.VOTE_ADDED:
        if data == 1:
            response = "upvoted!"
        elif data == -1:
            response = "downvoted!"
    elif status == database.ALREADY_VOTED:
        database.add_vote(user.id, quote_id, 0)
        response = "vote removed!"
    elif status == database.QUOTE_DELETED:
        response = "vote added and quote deleted!"
        query.answer(response)

        for chat_id, message_id in database.get_quote_messages(quote_id):
            try:
                bot.edit_message_text(
                    chat_id=chat_id, message_id=message_id,
                    text="[quote was deleted]", reply_markup=[])
            except TelegramError as e:
                # The message is over 48 hours old and can't be edited
                pass

        return

    query.answer(response)

    keyboard = create_vote_buttons(user.id, quote_id, direct=direct)

    bot.edit_message_reply_markup(
        chat_id=current_chat_id, message_id=quote_message.message_id,
        reply_markup=keyboard)


handler_vote = CallbackQueryHandler(handle_vote, pass_user_data=True)


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

    votes = create_vote_buttons(
        user.id, result.quote.id, direct=user_data is not None)

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


class Tag:
    def __init__(self, value=None):
        self.value = value

    def sql(self, quote):
        raise NotImplementedError


class AuthorTag(Tag):
    def __init__(self, value=None):
        self.value = value.lower()

    def sql(self):
        where = """quote.sent_by IN
            (SELECT user.id FROM user
            WHERE user.first_name || COALESCE(' ' || user.last_name, '') LIKE ?
            OR user.username LIKE ?)"""
        params = [f'%{self.value}%'] * 2

        return where, params


class QuotedByTag(Tag):
    def __init__(self, value=None):
        self.value = value.lower()

    def sql(self):
        where = """quote.quoted_by IN
            (SELECT user.id FROM user
            WHERE user.first_name || COALESCE(' ' || user.last_name, '') LIKE ?
            OR user.username LIKE ?)"""

        params = [f'%{self.value}%'] * 2

        return where, params


class DateTag(Tag):
    def __init__(self, value=None):
        try:
            self.day = datetime.datetime.strptime(value, '%Y-%m-%d')
            self.next_day = self.day + datetime.timedelta(days=1)
        except ValueError as e:
            raise e

    def sql(self):
        where = "quote.sent_at >= ? AND quote.sent_at < ?"
        params = [int(self.day.timestamp()), int(self.next_day.timestamp())]

        return where, params


TAGS = {
    'author': AuthorTag,
    'quoted_by': QuotedByTag,
    'date': DateTag,
}


def create_tag(name, value):
    tag = TAGS.get(name, None)

    if tag is None:
        raise ValueError

    return tag(value=value)


PATTERN = re.compile(r'^([-\w]+):([-\w]+)$')


def handle_search(bot, update, args=list(), user_data=None):
    if user_data is None:
        chat_id = update.message.chat_id
    else:
        chat_id = user_data['current']

    if not args:
        return

    terms, clauses, params = [], [], []

    for item in args:
        match = PATTERN.search(item)

        # Tags
        if match is not None:
            try:
                filter_ = create_tag(*match.groups())
            except ValueError:
                pass
            else:
                c, p = filter_.sql()
                clauses.append(c)
                params.extend(p)
        # Search terms
        else:
            terms.append(item)

    terms = ' '.join(terms)
    result = database.search_quote(chat_id, terms, clauses, params)

    if len(args) > TRUNCATE_ARGS_LENGTH:
        args = args[:TRUNCATE_ARGS_LENGTH] + '...'

    user = update.message.from_user

    if result is None:
        response = 'no quotes found'
        update.message.reply_text(response)
    else:
        votes = create_vote_buttons(
            user.id, result.quote.id, direct=user_data is not None)

        response = format_quote(*result)
        message = update.message.reply_text(
            response, parse_mode='HTML', reply_markup=votes)

        database.add_message(chat_id, message.message_id, result.quote.id)


handler_search = CommandHandler(
    'search', handle_search, filters=Filters.group, pass_args=True)
dm_handler_search = CommandHandler(
    'search', handle_search, pass_args=True, **dm_kwargs)
