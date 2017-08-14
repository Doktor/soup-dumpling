from telegram import Update
from telegram.ext import ConversationHandler


class ConversationHandlerFiltered(ConversationHandler):
    def __init__(self, *args, filters=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.filters = filters

    def check_update(self, update):
        if not isinstance(update, Update) and not update.message:
            return False

        message = update.message

        if self.filters is None:
            res = True
        elif isinstance(self.filters, list):
            res = any(f(message) for f in self.filters)
        else:
            res = self.filters(message)

        return res and super().check_update(update)
