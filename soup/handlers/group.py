from telegram.ext import CommandHandler, Filters

from soup.classes import User
from soup.core import database, username
from soup.database import QuoteDatabase

LOUDLY_CRYING_FACE = '\U0001F62D'
ANGRY_FACE = '\U0001F620'
POUTING_FACE = '\U0001F621'
SMILING_FACE_WITH_SUNGLASSES = '\U0001F60E'


def format_response(s, emoji):
    if emoji is not None:
        return f' {emoji} '.join(s.split(' '))
    return s


def handle_addquote(bot, update, word='quote', emoji=None):
    message = update.message
    quote = update.message.reply_to_message

    assert quote is not None

    # Only text messages or media captions can be quoted
    if (quote.photo is not None or quote.video is not None) and quote.caption:
        text = quote.caption
        text_html = text
    elif quote.text is not None:
        text = quote.text
        text_html = quote.text_html
    else:
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
        response = format_response(f"can't {word} soup messages", emoji)
        return update.message.reply_text(response)

    # Users can't add their own messages as quotes
    if sent_by.id == quoted_by.id:
        response = format_response(f"can't {word} your own messages", emoji)
        return update.message.reply_text(response)

    database.add_or_update_user(User.from_telegram(sent_by))
    database.add_or_update_user(User.from_telegram(quoted_by))

    result, status = database.add_quote(
        chat_id, message_id, is_forward,
        sent_at, sent_by.id, text, text_html, quoted_by.id)

    if status == database.QUOTE_ADDED:
        response = f"{word} added"
    elif status == database.QUOTE_ALREADY_EXISTS:
        response = f"{word} already exists"
    elif status == database.QUOTE_PREVIOUSLY_DELETED:
        response = format_response(f"this {word} was previously deleted", emoji)
        return update.message.reply_text(response)

    response = format_response(response, emoji)
    message = update.message.reply_text(response)

    database.add_message(message.chat_id, message.message_id, result.quote.id)


def handle_addqoute(bot, update):
    return handle_addquote(bot, update, word='qoute')


def handle_sadquote(bot, update):
    return handle_addquote(bot, update, emoji=LOUDLY_CRYING_FACE)


def handle_madquote(bot, update):
    return handle_addquote(bot, update, emoji=POUTING_FACE)


def handle_radquote(bot, update):
    return handle_addquote(bot, update, emoji=SMILING_FACE_WITH_SUNGLASSES)


handler_addquote = CommandHandler(
    'addquote', handle_addquote, filters=Filters.reply & Filters.group)

handler_addqoute = CommandHandler(
    'addqoute', handle_addqoute, filters=Filters.reply & Filters.group)

handler_sadquote = CommandHandler(
    'sadquote', handle_sadquote, filters=Filters.reply & Filters.group)

handler_madquote = CommandHandler(
    'madquote', handle_madquote, filters=Filters.reply & Filters.group)
