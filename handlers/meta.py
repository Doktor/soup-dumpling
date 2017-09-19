from subprocess import check_output
from telegram.ext import CommandHandler, Filters, MessageHandler

from classes import User, Chat
from main import database, username, VERSION


REPOSITORY_NAME = "Doktor/soup-dumpling"
REPOSITORY_URL = "https://github.com/Doktor/soup-dumpling"

COMMIT_HASH = check_output(['git', 'rev-parse', 'HEAD'],
    encoding='utf8').rstrip('\n')
COMMIT_URL = REPOSITORY_URL + '/commit/' + COMMIT_HASH

DATE_ARGS = ['git', 'log', COMMIT_HASH,
    '-1', '--date=iso', r'--pretty=format:%cd']
COMMIT_DATE = check_output(DATE_ARGS, encoding='utf8')[:19]

# The relative date is used for the 'about' command
DATE_ARGS[4] = '--date=relative'


def handle_about(bot, update):
    info = {
        'version': '.'.join((str(n) for n in VERSION)),
        'updated': COMMIT_DATE,
        'updated_rel': check_output(DATE_ARGS, encoding='utf8'),
        'repo_url': REPOSITORY_URL,
        'repo_name': REPOSITORY_NAME,
        'hash_url': COMMIT_URL,
        'hash': COMMIT_HASH[:7],
    }

    response = [
        '"Nice quote!" - <b>Soup Dumpling {version}</b>',
        '<i>{updated} ({updated_rel})</i>',
        '',
        'Source code at <a href="{repo_url}">{repo_name}</a>',
        'Running on commit <a href="{hash_url}">{hash}</a>',
    ]

    response = '\n'.join(response).format(**info)

    update.message.reply_text(response,
        quote=False, disable_web_page_preview=True, parse_mode='HTML')


handler_about = CommandHandler('about', handle_about)


with open('help.txt', 'r', encoding='utf8') as f:
    raw = f.read().strip()
    kwargs = {
        'version': '.'.join((str(n) for n in VERSION)),
        'readme': REPOSITORY_URL + "/blob/master/README.md"
    }
    help_text = raw.format(**kwargs)


def handle_help(bot, update):
    update.message.reply_text(help_text,
        disable_web_page_preview=True, quote=False, parse_mode='HTML')


handler_help = CommandHandler('help', handle_help, filters=Filters.private)


def handle_help_group(bot, update):
    kwargs = {
        'version': '.'.join((str(n) for n in VERSION)),
        'username': username,
    }

    response = [
        '"Nice help!" - <b>Soup Dumpling {version}</b>',
        '',
        '• <b>Groups</b>: /addquote',
        ('• <b>Anywhere</b>: /about, /author &lt;name&gt;, /count [term], '
        '/help, /most_added, /most_quoted, /random, /search &lt;term&gt;, '
        '/stats'),
        '• <b>Direct messages</b>: /chats or /start, /which',
        '',
        'For extended help, DM <code>/help</code> to {username}',
    ]

    response = '\n'.join(response).format(**kwargs)

    update.message.reply_text(response,
        disable_web_page_preview=True, quote=False, parse_mode='HTML')


handler_help_group = CommandHandler(
    'help', handle_help_group, filters=Filters.group)


def handle_database(bot, update):
    user = update.message.from_user
    chat = update.message.chat

    database.add_or_update_user(User.from_telegram(user))

    if user.id != chat.id:
        database.add_or_update_chat(Chat.from_telegram(chat))
        database.add_membership(user.id, chat.id)


handler_database = MessageHandler(
    Filters.text | Filters.command, handle_database)
