import functools
import os
import sqlite3

from classes import Quote, Result, Chat, User


class QuoteDatabase:
    # Status codes for quotes
    QUOTE_ADDED = 1
    QUOTE_ALREADY_EXISTS = 2
    QUOTE_PREVIOUSLY_DELETED = 3

    # Status codes: voting
    VOTE_ADDED = 11
    ALREADY_VOTED = 12
    QUOTE_DELETED = 13

    SCORE_TO_DELETE = -5

    def __init__(self, filename='data.db'):
        self.filename = filename

        if not os.path.isfile(filename):
            self.setup()

    # Database methods

    def connect(self):
        """Connects to the database."""
        self.db = sqlite3.connect(self.filename)
        self.c = self.db.cursor()

    def setup(self):
        """Creates the database."""
        self.connect()

        with open('create.sql', 'r') as f:
            create = f.read().strip()

        self.c.executescript(create)
        self.db.commit()

    # User methods

    def get_user_by_id(self, user_id):
        """Returns a User object for the user with the given ID, or None if the
        user doesn't exist."""
        self.connect()

        select = "SELECT * FROM user WHERE id = ?;"
        self.c.execute(select, (user_id,))

        user = self.c.fetchone()
        if not user:
            return None
        else:
            return User.from_database(user)

    def user_exists(self, user):
        """Returns whether the given user exists in the database."""
        self.connect()

        select = "SELECT EXISTS(SELECT * FROM user WHERE id = ? LIMIT 1);"
        self.c.execute(select, (user.id,))

        result = self.c.fetchone()
        return result[0]

    def add_or_update_user(self, user):
        """Adds a user to the database if they don't exist, or updates their
        data otherwise."""
        self.connect()

        if self.user_exists(user):
            update = ("UPDATE user SET "
                "first_name = ?, last_name = ?, username = ? WHERE id = ?;")
            self.c.execute(update,
                (user.first_name, user.last_name, user.username, user.id))
        else:
            insert = "INSERT INTO user VALUES (?, ?, ?, ?);"
            self.c.execute(insert,
                (user.id, user.first_name, user.last_name, user.username))

        self.db.commit()

    def get_user_chats(self, user_id):
        """Returns a list of chats that a user is a member of."""
        self.connect()

        select = """SELECT chat.id, chat.title AS title FROM chat
            INNER JOIN membership AS mem
            ON mem.chat_id = chat.id
            AND mem.user_id = ?
            ORDER BY title COLLATE NOCASE"""
        self.c.execute(select, (user_id,))

        return self.c.fetchall()

    def get_user_score(self, user_id, chat_id):
        """Returns the total number of upvotes and downvotes, and the total
        score for the user's quotes."""
        total_up = total_score = total_down = 0

        for quote_id in self.get_user_quote_ids(user_id, chat_id):
            up, score, down = self.get_votes_by_id(quote_id)

            total_up += up
            total_score += score
            total_down += down

        return total_up, total_score, total_down

    def get_user_quote_ids(self, user_id, chat_id):
        """Returns a list of IDs of the user's quotes."""
        self.connect()

        select = """SELECT id FROM quote
            WHERE sent_by = ? AND chat_id = ? AND deleted = 0;"""
        self.c.execute(select, (user_id, chat_id))

        return [item[0] for item in self.c.fetchall()]

    # Chat methods

    def get_chat_by_id(self, chat_id):
        """Returns the chat with the given ID."""
        self.connect()

        select = "SELECT * FROM chat WHERE id = ?;"
        self.c.execute(select, (chat_id,))

        chat = self.c.fetchone()
        if not chat:
            return None
        else:
            return Chat.from_database(chat)

    def chat_exists(self, chat):
        """Determines if the given chat exists in the database."""
        self.connect()

        select = "SELECT EXISTS(SELECT * FROM chat WHERE id = ? LIMIT 1);"
        self.c.execute(select, (chat.id,))

        return self.c.fetchone()[0]

    def add_or_update_chat(self, chat):
        """Adds a chat to the database if it doesn't exist, or updates its data
        if it does."""
        self.connect()

        if self.chat_exists(chat):
            update = ("UPDATE chat SET "
                "title = ?, username = ? WHERE id = ?;")
            self.c.execute(update, (chat.title, chat.username, chat.id))
        else:
            insert = "INSERT INTO chat VALUES (?, ?, ?, ?);"
            self.c.execute(insert,
                (chat.id, chat.type, chat.title, chat.username))

        self.db.commit()

    def get_chat_user_ids(self, chat_id):
        """Returns a list of IDs of users in the given chat."""
        self.connect()

        select = """SELECT user.id FROM user
            INNER JOIN membership AS m
            WHERE m.chat_id = ?
            AND m.user_id = user.id;"""

        self.c.execute(select, (chat_id,))

        return [item[0] for item in self.c.fetchall()]

    # Membership methods

    def add_membership(self, user_id, chat_id):
        """Adds a membership listing, indicating that a user is in a chat."""
        self.connect()

        select = "INSERT INTO membership (user_id, chat_id) VALUES (?, ?)"
        try:
            self.c.execute(select, (user_id, chat_id))
        except sqlite3.IntegrityError:
            pass
        else:
            self.db.commit()

    def remove_membership(self, user_id, chat_id):
        """Removes a membership listing, when a user leaves or is removed from
        a group."""
        self.connect()

        delete = "DELETE FROM membership WHERE user_id = ? AND chat_id = ?;"
        self.c.execute(delete, (user_id, chat_id))

    # User ranking methods

    def get_most_quoted(self, chat_id, limit=5):
        """Returns the names of the users who have the most quotes attributed
        to them."""
        self.connect()

        select = """SELECT COUNT(*) AS count, user.first_name, user.last_name
            FROM quote INNER JOIN user
            ON quote.sent_by = user.id
            AND quote.chat_id = ?
            AND deleted = 0
            GROUP BY quote.sent_by
            ORDER BY count DESC
            LIMIT ?"""
        self.c.execute(select, (chat_id, limit))

        return self.c.fetchall()

    def get_most_quotes_added(self, chat_id, limit=5):
        """Returns the names of the users who have added the most quotes."""
        self.connect()

        select = """SELECT COUNT(*) AS count, user.first_name, user.last_name
            FROM quote INNER JOIN user
            ON quote.quoted_by = user.id
            AND quote.chat_id = ?
            AND deleted = 0
            GROUP BY quote.quoted_by
            ORDER BY count DESC
            LIMIT ?"""
        self.c.execute(select, (chat_id, limit))

        return self.c.fetchall()

    def get_user_scores(self, chat_id, limit=5, direction=1):
        self.connect()

        user_ids = self.get_chat_user_ids(chat_id)

        scores = []
        for user_id in user_ids:
            up, score, down = self.get_user_score(user_id, chat_id)

            user = [user_id, up, score, down]
            scores.append(user)

        users = sorted(scores, key=lambda item: item[2], reverse=direction == 1)

        final = []
        for data in users[:limit]:
            user = self.get_user_by_id(data[0])

            final.append([user.first_name, user.last_name, *data[1:]])

        return final

    get_lowest_scoring = functools.partialmethod(get_user_scores, direction=-1)
    """Returns users with the lowest overall scores."""

    get_highest_scoring = functools.partialmethod(get_user_scores, direction=1)
    """Returns users with the highest overall scores."""

    # Quote methods

    def get_quote_by_id(self, id_):
        self.connect()

        select = """SELECT id, chat_id, message_id, sent_at, sent_by,
            content_html FROM quote WHERE id = ?;"""
        self.c.execute(select, (id_,))

        row = self.c.fetchone()
        if row is None:
            return None

        quote = Quote.from_database(row)
        user = self.get_user_by_id(quote.sent_by)
        return Result(quote, user)

    def get_quote_by_ids(self, chat_id, message_id):
        self.connect()

        select = """SELECT id, chat_id, message_id, sent_at, sent_by,
            content_html FROM quote WHERE chat_id = ? AND message_id = ?;"""
        self.c.execute(select, (chat_id, message_id,))

        row = self.c.fetchone()
        if row is None:
            return None

        quote = Quote.from_database(row)
        user = self.get_user_by_id(quote.sent_by)
        return Result(quote, user)

    def get_quote_count(self, chat_id, search=None):
        """Returns the number of quotes added in the given chat."""
        self.connect()

        if search is None:
            select = """SELECT COUNT(*) FROM quote
                WHERE quote.chat_id = ?"""
            self.c.execute(select, (chat_id,))
            return self.c.fetchone()[0]
        else:
            template = """SELECT COUNT(DISTINCT quote.id),
                user.first_name ||
                    COALESCE(' ' || user.last_name, '') AS full_name
                FROM quote INNER JOIN user
                ON quote.sent_by = user.id
                AND quote.chat_id = ?
                AND deleted = 0
                AND {cond};"""

            # The number of quotes containing the search term
            select = template.format(cond="quote.content LIKE ?")
            self.c.execute(select, (chat_id, '%' + search + '%'))

            content = self.c.fetchone()[0]

            # The number of quotes by this author
            select = template.format(
                cond="(full_name LIKE ? OR user.username LIKE ?)")
            search = '%' + search + '%'
            self.c.execute(select, (chat_id, search, search))

            author = self.c.fetchone()[0]

            return content, author

    def get_first_quote(self, chat_id):
        """Returns the first quote added in the given chat."""
        return self._get_edge_quote(chat_id, 'ASC')

    def get_last_quote(self, chat_id):
        """Returns the last quote added in the given chat."""
        return self._get_edge_quote(chat_id, 'DESC')

    def _get_edge_quote(self, chat_id, direction):
        """Returns the first/last quote added in the given chat."""
        self.connect()

        assert direction in ['ASC', 'DESC']

        select = """SELECT id, chat_id, message_id, sent_at, sent_by,
            content_html FROM quote
            WHERE chat_id = ?
            AND deleted = 0
            ORDER BY sent_at {}
            LIMIT 1""".format(direction)
        self.c.execute(select, (chat_id,))

        row = self.c.fetchone()
        if row is None:
            return None

        quote = Quote.from_database(row)
        user = self.get_user_by_id(quote.sent_by)
        return Result(quote, user)

    def get_random_quote(self, chat_id, name=None):
        """Returns a random quote, and the user who wrote the quote."""
        self.connect()

        if name is None:
            select = """SELECT id, chat_id, message_id, sent_at, sent_by,
                content_html FROM quote
                WHERE chat_id = ?
                ORDER BY RANDOM() LIMIT 1;"""
            self.c.execute(select, (chat_id,))
        else:
            name = name.lstrip('@')
            select = """SELECT
                quote.id, chat_id, message_id, sent_at, sent_by, content,
                user.first_name ||
                    COALESCE(' ' || user.last_name, '') AS full_name
                FROM quote INNER JOIN user
                ON quote.sent_by = user.id
                AND quote.chat_id = ?
                AND (full_name LIKE ? OR username LIKE ?)
                AND deleted = 0
                ORDER BY RANDOM() LIMIT 1;"""
            self.c.execute(select,
                (chat_id, '%' + name + '%', '%' + name + '%'))

        row = self.c.fetchone()
        if row is None:
            return None

        if name is not None:
            row = row[0:6]

        quote = Quote.from_database(row)
        user = self.get_user_by_id(quote.sent_by)
        return Result(quote, user)

    def search_quote(self, chat_id, search_terms):
        """Returns a random quote matching the search terms, and the user
        who wrote the quote."""
        self.connect()

        select = """SELECT id, chat_id, message_id, sent_at, sent_by,
            content_html FROM quote
            WHERE content LIKE ?
            AND deleted = 0
            ORDER BY RANDOM() LIMIT 1;"""
        self.c.execute(select, ('%' + search_terms + '%',))

        row = self.c.fetchone()
        if row is None:
            return None

        quote = Quote.from_database(row)
        user = self.get_user_by_id(quote.sent_by)
        return Result(quote, user)

    def add_quote(self, chat_id, message_id, is_forward,
            sent_at, sent_by, content, content_html, quoted_by):
        """Inserts a quote."""
        self.connect()

        select = """SELECT id, deleted FROM quote
            WHERE sent_at = ? AND sent_by = ? AND content_html = ?;"""
        self.c.execute(
            select, (sent_at, sent_by, content_html))

        result = self.c.fetchone()

        if result is None:
            pass
        else:
            quote_id, deleted = result

            if deleted:
                return None, self.QUOTE_PREVIOUSLY_DELETED

            quote = self.get_quote_by_id(quote_id)
            return quote, self.QUOTE_ALREADY_EXISTS

        insert = """INSERT INTO quote
            (chat_id, message_id, is_forward,
            sent_at, sent_by, content, content_html, quoted_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);"""

        self.c.execute(insert,
            (chat_id, message_id, is_forward,
                sent_at, sent_by, content, content_html, quoted_by))
        self.db.commit()

        quote = self.get_quote_by_id(self.c.lastrowid)
        return quote, self.QUOTE_ADDED

    def delete_quote(self, quote_id):
        """Marks a quote as deleted."""
        self.connect()

        update = "UPDATE quote SET deleted = 1 WHERE id = ?"
        self.c.execute(update, (quote_id,))
        self.db.commit()

    # Quote message methods

    def add_message(self, chat_id, message_id, quote_id):
        """Adds a quote message, i.e. a bot message that contains a quote."""
        self.connect()

        insert = """INSERT INTO quote_message (chat_id, message_id, quote_id)
            VALUES (?, ?, ?);"""
        self.c.execute(insert, (chat_id, message_id, quote_id))
        self.db.commit()

    def get_quote_id_from_message(self, chat_id, message_id):
        """Returns the quote ID corresponding to the given quote message."""
        self.connect()

        select = """SELECT quote_id FROM quote_message
            WHERE chat_id = ? AND message_id = ?;"""
        self.c.execute(select, (chat_id, message_id))

        message = self.c.fetchone()

        if message:
            return message[0]

        return None

    def get_quote_messages(self, quote_id):
        """Returns a list of all messages that refer to the given quote."""
        self.connect()

        select = """SELECT chat_id, message_id FROM quote_message
            WHERE quote_id = ?;"""
        self.c.execute(select, (quote_id,))

        results = self.c.fetchall()

        return [] if results is None else results

    # Vote methods

    def get_user_vote(self, user_id, quote_id):
        self.connect()

        select = """SELECT direction FROM vote
            WHERE user_id = ? AND quote_id = ?;"""
        self.c.execute(select, (user_id, quote_id))

        vote = self.c.fetchone()
        return 0 if vote is None else vote[0]

    def add_vote(self, user_id, quote_id, direction):
        self.connect()

        vote = self.get_user_vote(user_id, quote_id)

        if vote == 0:
            pass
        elif vote == direction:
            return self.ALREADY_VOTED

        insert = """INSERT OR REPLACE INTO vote (user_id, quote_id, direction)
            VALUES (?, ?, ?);"""
        self.c.execute(insert, (user_id, quote_id, direction))
        self.db.commit()

        _, score, _ = self.get_votes_by_id(quote_id)

        if score <= self.SCORE_TO_DELETE:
            self.delete_quote(quote_id)
            return self.QUOTE_DELETED
        else:
            return self.VOTE_ADDED

    def get_votes(self, chat_id, message_id):
        """Returns the number of upvotes / downvotes and score for a quote."""
        self.connect()

        quote_id = self.get_quote_id_from_message(chat_id, message_id)

        return self.get_votes_by_id(quote_id)

    def get_votes_by_id(self, quote_id):
        """Returns the number of upvotes / downvotes and score for a quote."""
        select = "SELECT direction FROM vote WHERE quote_id = ?;"
        self.c.execute(select, (quote_id,))

        up, score, down = 0, 0, 0

        for vote in self.c:
            vote = vote[0]

            if vote == 1:
                up += 1
                score += 1
            elif vote == -1:
                down += 1
                score -= 1

        return up, score, down
