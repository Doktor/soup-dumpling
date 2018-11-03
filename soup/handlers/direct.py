from html import escape
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ConversationHandler, CommandHandler, Filters, MessageHandler)

from soup.core import (
    chunks, database, session_wrapper, SELECT_CHAT, SELECTED_CHAT)
from soup.handlers.quotes import dm_kwargs


def handle_cancel(bot, update, user_data):
    user_data['current'] = None
    update.message.reply_text('canceled')
    return ConversationHandler.END


dm_only_handler_cancel = CommandHandler('cancel', handle_cancel, **dm_kwargs)


@session_wrapper
def handle_start(bot, update, user_data, session=None):
    user_id = update.message.from_user.id

    chats = database.get_user_chats(session, user_id)

    if not chats:
        response = "<b>Chat selection</b>\nno chats found"
        update.message.reply_text(response, parse_mode='HTML')
        return ConversationHandler.END

    response = [
        "<b>Chat selection</b>",
        "Choose a chat by its number or title:",
        "",
    ]

    mapping = []
    for i, chat in enumerate(chats):
        response.append("<b>[{0}]</b> {1}".format(i, escape(chat.title)))
        mapping.append([i, chat.id, chat.title])

    user_data['choices'] = mapping
    response = '\n'.join(response)

    if len(chats) < 6:
        # Use a reply keyboard
        titles = [chat.title for chat in chats]
        reply_keyboard = list(chunks(titles, 2))
        markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, resize_keyboard=True)

        update.message.reply_text(
            response, parse_mode='HTML', reply_markup=markup)
    else:
        # Too many choices: send the choices in a message
        update.message.reply_text(response, parse_mode='HTML')

    return SELECT_CHAT


_handler_start = CommandHandler('start', handle_start, **dm_kwargs)
_handler_chats = CommandHandler('chats', handle_start, **dm_kwargs)

start_handlers = [_handler_start, _handler_chats]


def handle_select_chat(bot, update, user_data):
    choice = update.message.text

    try:
        i = int(choice)
        _, selected_id, title = user_data['choices'][i]
    except IndexError:
        update.message.reply_text("invalid chat number")
        return SELECT_CHAT
    except ValueError:
        try:
            _, selected_id, title = next(filter(
                lambda chat: choice.lower() in chat[2].lower(),
                user_data['choices']))
        except StopIteration:
            update.message.reply_text("no titles matched")
            return SELECT_CHAT

    user_data['current'] = selected_id

    response = 'selected chat "{0}"'.format(title)
    update.message.reply_text(response, reply_markup=ReplyKeyboardRemove())

    return SELECTED_CHAT


dm_only_handler_select = MessageHandler(
    Filters.text | Filters.command, handle_select_chat, pass_user_data=True)


def handle_which(bot, update, user_data):
    chat = database.get_chat_by_id(user_data['current'])

    response = 'searching quotes from "{0}"'.format(escape(chat.title))
    update.message.reply_text(response)


dm_only_handler_which = CommandHandler('which', handle_which, **dm_kwargs)
