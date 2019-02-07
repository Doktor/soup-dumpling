from .direct import dm_only_handler_cancel, dm_only_handler_select, dm_only_handler_which, start_handlers, SELECT_CHAT, SELECTED_CHAT
from .group import handler_addquote, handler_addqoute, handler_madquote, handler_sadquote
from .meta import handler_about, handler_database, handler_group_migration, handler_help, handler_help_group, handler_user_left
from .quotes import handler_random, handler_search, handler_vote
from .stats import handler_hi_scores, handler_lo_scores, handler_most_added, handler_most_quoted, handler_scores, handler_stats

from .quotes import dm_handler_random, dm_handler_search
from .stats import dm_handler_hi_scores, dm_handler_lo_scores, dm_handler_most_added, dm_handler_most_quoted, dm_handler_scores, dm_handler_stats

from telegram.ext import ConversationHandler

_all = globals()
dm_handlers = [v for k, v in _all.items() if k.startswith('dm_handler')]

_dm_handler = ConversationHandler(
    entry_points=start_handlers,
    states={
        SELECT_CHAT: [dm_only_handler_select],
        SELECTED_CHAT: [dm_only_handler_which] + dm_handlers,
    },
    fallbacks=[dm_only_handler_cancel],
    allow_reentry=True
)

handlers = [v for k, v in _all.items() if k.startswith('handler')]
handlers += [_dm_handler]
