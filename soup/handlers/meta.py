import shlex
from subprocess import check_output
from telegram.ext import CommandHandler, Filters, MessageHandler

from soup.__version__ import VERSION_STRING
from soup.core import database, DEBUG, username, session_wrapper


REPOSITORY_NAME = "Doktor/soup-dumpling"
REPOSITORY_URL = "https://github.com/Doktor/soup-dumpling"

COMMIT_HASH = check_output(['/usr/bin/git', 'rev-parse', 'HEAD'],
    encoding='utf8').rstrip('\n')
COMMIT_URL = REPOSITORY_URL + '/commit/' + COMMIT_HASH

DATE_ARGS = ['/usr/bin/git', 'log', COMMIT_HASH,
    '-1', '--date=iso', r'--pretty=format:%cd']
COMMIT_DATE = check_output(DATE_ARGS, encoding='utf8')[:19]

# Commits that don't exist on the remote branch
ORIGIN_DIFF = check_output(
    shlex.split("/usr/bin/git log origin/master..master --pretty=oneline"),
    encoding='utf8')

PUSHED = COMMIT_HASH not in ORIGIN_DIFF

# The relative date is used for the 'about' command
DATE_ARGS[4] = '--date=relative'


def handle_about(bot, update):
    updated_relative = check_output(DATE_ARGS, encoding='utf8')

    # Add a GitHub link if the current commit exists there
    if PUSHED:
        commit = f'<a href="{COMMIT_URL}">{COMMIT_HASH[:7]}</a>'
    else:
        commit = f'{COMMIT_HASH[:7]}'

    mode = 'debug' if DEBUG else 'production'

    response = [
        f'"Nice quote!" - <b>Soup Dumpling {VERSION_STRING}</b>',
        f'<i>{COMMIT_DATE} ({updated_relative})</i>',
        '',
        f'Source code at <a href="{REPOSITORY_URL}">{REPOSITORY_NAME}</a>',
        f'Running on commit {commit}',
        f'Running in {mode} mode',
    ]

    response = '\n'.join(response)

    update.message.reply_text(response,
        quote=False, disable_web_page_preview=True, parse_mode='HTML')


handler_about = CommandHandler('about', handle_about)


with open('help.txt', 'r', encoding='utf8') as f:
    raw = f.read().strip()
    kwargs = {
        'version': VERSION_STRING,
        'readme': REPOSITORY_URL + "/blob/master/README.md"
    }
    help_text = raw.format(**kwargs)


def handle_help(bot, update):
    update.message.reply_text(help_text,
        disable_web_page_preview=True, quote=False, parse_mode='HTML')


handler_help = CommandHandler('help', handle_help, filters=Filters.private)


def handle_help_group(bot, update):
    response = [
        f'"Nice help!" - <b>Soup Dumpling {VERSION_STRING}</b>',
        '',
        '• <b>Groups</b>: /addquote',
        ('• <b>Anywhere</b>: /about, /author &lt;name&gt;, /count [term], '
        '/help, /most_added, /most_quoted, /random, /search &lt;term&gt;, '
        '/stats'),
        '• <b>Direct messages</b>: /chats or /start, /which',
        '',
        f'For extended help, DM <code>/help</code> to {username}',
    ]

    response = '\n'.join(response)

    update.message.reply_text(response,
        disable_web_page_preview=True, quote=False, parse_mode='HTML')


handler_help_group = CommandHandler(
    'help', handle_help_group, filters=Filters.group)


@session_wrapper
def handle_database(bot, update, session=None):
    user = update.message.from_user
    chat = update.message.chat

    database.add_or_update_user(session, user)

    if user.id != chat.id:
        database.add_or_update_chat(session, chat)
        database.add_membership(session, user.id, chat.id)


handler_database = MessageHandler(
    Filters.text | Filters.command, handle_database)


@session_wrapper
def handle_user_left(bot, update, session=None):
    user_id = update.message.left_chat_member.id
    chat_id = update.message.chat_id

    database.remove_membership(session, user_id, chat_id)


handler_user_left = MessageHandler(
    Filters.status_update.left_chat_member, handle_user_left)


@session_wrapper
def handle_group_migration(bot, update, session=None):
    if hasattr(update.message, 'migrate_to_chat_id'):
        database.migrate_chat(
            session, update.message.chat.id, update.message.migrate_to_chat_id)

    elif hasattr(update.message, 'migrate_from_chat_id'):
        assert not database.chat_exists(
            session, update.message.migrate_from_chat_id)


handler_group_migration = MessageHandler(
    Filters.status_update.migrate, handle_group_migration)
