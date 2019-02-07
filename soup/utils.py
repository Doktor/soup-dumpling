from html import escape

from soup.core import TIME_FORMAT, TRUNCATE_LENGTH


def chunks(l, size):
    """Yields chunks of items from a list."""
    for i in range(0, len(l), size):
        yield l[i:i + size]


def format_quote(quote, sent_by):
    """Creates the Telegram message for a quote."""
    text = quote.content_html
    name = sent_by.first_name
    date = quote.sent_at.strftime(TIME_FORMAT)

    # Truncate long quotes
    if len(text) > TRUNCATE_LENGTH:
        text = text[:TRUNCATE_LENGTH]
        return f'"{text}..." (truncated) - {name}\n<i>{date}</i>'
    else:
        return f'"{text}" - {name}\n<i>{date}</i>'


def format_users(users, total_count):
    """Creates the Telegram message with a list of users."""
    lines = []

    for user, count in users:
        name = "{} {}".format(user.first_name, user.last_name or '').rstrip()
        line = "• {0} ({1:.1%}): {2}".format(count, count / total_count, name)
        lines.append(escape(line))

    return lines
