from telegram.ext import CommandHandler, Filters

from soup.core import database, username, session_wrapper


LOUDLY_CRYING_FACE = '\U0001F62D'
ANGRY_FACE = '\U0001F620'
POUTING_FACE = '\U0001F621'
SMILING_FACE_WITH_SUNGLASSES = '\U0001F60E'


def format_response(s, emoji):
    if emoji is not None:
        return f' {emoji} '.join(s.split(' '))
    return s


@session_wrapper
def handle_addquote(bot, update, word='quote', emoji=None, session=None):
    message = update.message
    quote = update.message.reply_to_message

    # Only text and photo messages can be quoted
    if quote.photo and quote.sticker is None:
        message_type = 'photo'

        # Choose the largest size
        photo = list(reversed(sorted(quote.photo, key=lambda i: i.width)))[0]

        content = quote.caption
        content_html = quote.caption_html
        file_id = photo.file_id

    elif quote.text is not None:
        message_type = 'text'

        content = quote.text
        content_html = quote.text_html
        file_id = ''

    else:
        response = format_response(f"can only {word} text and photo messages", emoji)
        return update.message.reply_text(response)

    chat_id = message.chat.id
    message_id = quote.message_id
    quoted_by = message.from_user

    # Forwarded messages
    is_forward = quote.forward_from is not None

    if is_forward:
        sent_by = quote.forward_from
        sent_at = quote.forward_date
    else:
        sent_by = quote.from_user
        sent_at = quote.date

    # Bot messages can't be added as quotes
    if sent_by.username == username.lstrip('@'):
        response = format_response(f"can't {word} soup messages", emoji)
        return update.message.reply_text(response)

    # Users can't add their own messages as quotes
    if sent_by.id == quoted_by.id:
        response = format_response(f"can't {word} your own messages", emoji)
        return update.message.reply_text(response)

    database.add_or_update_user(session, sent_by)
    database.add_or_update_user(session, quoted_by)

    quote, status = database.add_quote(
        session,
        chat_id, message_id, is_forward,
        sent_at, sent_by.id,
        message_type, content, content_html, file_id,
        quoted_by.id)

    if status == database.QUOTE_ADDED:
        response = f"{word} added"
    elif status == database.QUOTE_ALREADY_EXISTS:
        response = f"{word} already exists"
    elif status == database.QUOTE_PREVIOUSLY_DELETED:
        response = format_response(
            f"this {word} was previously deleted", emoji)
        return update.message.reply_text(response)
    else:
        raise RuntimeError

    response = format_response(response, emoji)
    message = update.message.reply_text(response)

    database.add_message(session, message.chat_id, message.message_id, quote)


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
