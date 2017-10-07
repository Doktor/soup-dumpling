from telegram.ext import CommandHandler, Filters

from classes import User
from database import QuoteDatabase
from main import database, username


def handle_addqoute(bot, update):
    return handle_addquote(bot, update, word='qoute')


def handle_addquote(bot, update, word='quote'):
    message = update.message
    quote = update.message.reply_to_message

    assert quote is not None

    # Only text messages can be added as quotes
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
        response = f"can't {word} bot messages"
        return update.message.reply_text(response)

    # Users can't add their own messages as quotes
    if sent_by.id == quoted_by.id:
        response = f"can't {word} own messages"
        return update.message.reply_text(response)

    database.add_or_update_user(User.from_telegram(sent_by))
    database.add_or_update_user(User.from_telegram(quoted_by))

    result = database.add_quote(
        chat_id, message_id, is_forward,
        sent_at, sent_by.id, text, text_html, quoted_by.id)

    if result == QuoteDatabase.QUOTE_ADDED:
        response = f"{word} added"
    elif result == QuoteDatabase.QUOTE_ALREADY_EXISTS:
        response = f"{word} already exists"

    update.message.reply_text(response)


handler_addquote = CommandHandler(
    'addquote', handle_addquote, filters=Filters.reply & Filters.group)

handler_addqoute = CommandHandler(
    'addqoute', handle_addqoute, filters=Filters.reply & Filters.group)
