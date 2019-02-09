from html import escape

from soup.core import MAX_CAPTION_LENGTH, MAX_MESSAGE_LENGTH, TIME_FORMAT, TRUNCATE_LENGTH


def chunks(l, size):
    """Yields chunks of items from a list."""
    for i in range(0, len(l), size):
        yield l[i:i + size]


def send_quote(update, quote, sent_by, buttons):
    if quote.message_type == 'text':
        response = format_quote(quote, sent_by, MAX_MESSAGE_LENGTH)

        return update.message.reply_text(
            response, parse_mode='HTML', reply_markup=buttons)

    elif quote.message_type == 'photo':
        caption = format_quote(quote, sent_by, MAX_CAPTION_LENGTH)

        return update.message.reply_photo(
            quote.file_id, parse_mode='HTML', caption=caption, reply_markup=buttons)


def format_quote(quote, sent_by, limit):
    """Creates the Telegram message for a quote."""
    text = quote.content_html
    name = sent_by.first_name
    date = quote.sent_at.strftime(TIME_FORMAT)

    if not text:
        assert quote.message_type == 'photo'
        return f"[no caption] - {name}\n{date}"

    if len(text) > TRUNCATE_LENGTH:
        text = text[:TRUNCATE_LENGTH]

    template = f"\"{text}\" - {name}\n<i>{date}</i>"
    length = len(template)

    if length > limit:
        # The number of characters over is length - limit
        # Then make additional room for the note
        text = text[:length - limit - len('...') - len('(snip)')]
        return f"\"{text}...\" (snip) - {name}\n<i>{date}</i>"
    else:
        return template


def format_users(users, total_count):
    """Creates the Telegram message with a list of users."""
    lines = []

    for user, count in users:
        name = "{} {}".format(user.first_name, user.last_name or '').rstrip()
        line = "• {0} ({1:.1%}): {2}".format(count, count / total_count, name)
        lines.append(escape(line))

    return lines
