import functools

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import exists
from sqlalchemy.sql.expression import func

from soup.classes import Base, User, Chat, Quote, QuoteMessage, Vote


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

        engine = create_engine(f"sqlite:///{filename}", echo=False)
        Base.metadata.create_all(engine)

        self.session_factory = sessionmaker(bind=engine)

    def create_session(self, **kwargs):
        return self.session_factory(**kwargs)

    # User methods

    def get_user_by_id(self, session, user_id):
        """Returns a User object for the user with the given ID, or None if the
        user doesn't exist."""
        return session.query(User).filter(User.id == user_id).one_or_none()

    def user_exists(self, session, user_id):
        """Returns whether the given user exists in the database."""
        return session.query(exists().where(User.id == user_id)).scalar()

    def add_or_update_user(self, session, tg_user):
        """Adds a user to the database if they don't exist, or updates their
        data otherwise."""
        if self.user_exists(session, tg_user.id):
            # Update the user's info
            user = self.get_user_by_id(session, tg_user.id)
            user.first_name = tg_user.first_name
            user.last_name = tg_user.last_name
            user.username = tg_user.username
        else:
            user = User(
                id=tg_user.id, first_name=tg_user.first_name,
                last_name=tg_user.last_name, username=tg_user.username)
            session.add(user)

    def get_user_chats(self, session, user_id):
        """Returns a list of chats that a user is a member of."""
        user = self.get_user_by_id(session, user_id)
        return [] if user is None else user.chats

    def get_user_score(self, session, user_id, chat_id):
        """Returns the total number of upvotes and downvotes, and the total
        score for the user's quotes."""
        total_up = total_score = total_down = 0

        for quote in self.get_user_quotes(session, user_id, chat_id):
            up, score, down = self.get_votes_by_id(session, quote.id)

            total_up += up
            total_score += score
            total_down += down

        return total_up, total_score, total_down

    def get_user_quotes(self, session, user_id, chat_id):
        """Returns the user's quotes."""
        return (session.query(Quote)
            .filter(
                Quote.sent_by_id == user_id,
                Quote.chat_id == chat_id,
                Quote.deleted == False))

    # Chat methods

    def get_chat_by_id(self, session, chat_id):
        """Returns the chat with the given ID."""
        return session.query(Chat).filter(Chat.id == chat_id).one_or_none()

    def chat_exists(self, session, chat_id):
        """Determines if the given chat exists in the database."""
        return session.query(exists().where(Chat.id == chat_id)).scalar()

    def add_or_update_chat(self, session, tg_chat):
        """Adds a chat to the database if it doesn't exist, or updates its data
        if it does."""
        if self.chat_exists(session, tg_chat.id):
            # Update the chat's info
            chat = self.get_chat_by_id(session, tg_chat.id)
            chat.title = tg_chat.title
            chat.username = tg_chat.username
        else:
            chat = Chat(
                id=tg_chat.id, type=tg_chat.type,
                title=tg_chat.title, username=tg_chat.username)
            session.add(chat)

    def migrate_chat(self, session, from_id, to_id):
        """Updates a chat's ID when it's converted from a regular group to
        a supergroup."""
        chat = self.get_chat_by_id(session, from_id)
        chat.id = to_id

    # Membership methods

    def add_membership(self, session, user_id, chat_id):
        """Adds a membership listing, indicating that a user is in a chat."""
        user = self.get_user_by_id(session, user_id)
        chat = self.get_chat_by_id(session, chat_id)

        if chat not in user.chats:
            user.chats.append(chat)
            session.add(user)

    def remove_membership(self, session, user_id, chat_id):
        """Removes a membership listing, when a user leaves or is removed from
        a group."""
        user = self.get_user_by_id(session, user_id)
        chat = self.get_chat_by_id(session, chat_id)

        user.chats.remove(chat)

    # User ranking methods

    def rank_users(self, session, chat_id, column, limit=5):
        count = func.count(User.id).label('count')

        return (session.query(User, count)
            .join(Quote, column == User.id)
            .filter(Quote.chat_id == chat_id, Quote.deleted == False)
            .group_by(column)
            .order_by(count.desc())
            .limit(limit))

    def get_most_quoted(self, session, chat_id, limit=5):
        """Returns the names of the users who have the most quotes attributed
        to them."""
        return self.rank_users(session, chat_id, Quote.sent_by_id, limit=limit)

    def get_most_quotes_added(self, session, chat_id, limit=5):
        """Returns the names of the users who have added the most quotes."""
        return self.rank_users(
            session, chat_id, Quote.quoted_by_id, limit=limit)

    def get_user_scores(self, session, chat_id, limit=5, direction=1):
        chat = self.get_chat_by_id(session, chat_id)
        scores = []

        for user in chat.users:
            up, score, down = self.get_user_score(session, user.id, chat.id)

            if direction == 1 and score == 0:
                continue
            elif direction == -1 and score > 0:
                continue

            scores.append((user, up, score, down))

        users = sorted(scores, key=lambda u: u[2], reverse=direction == 1)
        return users[:limit]

    get_lowest_scoring = functools.partialmethod(get_user_scores, direction=-1)
    """Returns users with the lowest overall scores."""

    get_highest_scoring = functools.partialmethod(get_user_scores, direction=1)
    """Returns users with the highest overall scores."""

    # Quote methods

    def get_quote_by_id(self, session, quote_id):
        return (session.query(Quote)
            .filter(Quote.id == quote_id).one_or_none())

    def get_quote_by_ids(self, session, chat_id, message_id):
        return (session.query(Quote)
            .filter(Quote.chat_id == chat_id, Quote.message_id == message_id)
            .one_or_none())

    def get_quote_count(self, session, chat_id):
        """Returns the number of quotes added in the given chat."""
        return (session.query(func.count(Quote.id))
            .filter(Quote.chat_id == chat_id).scalar())

    def get_random_quote(self, session, chat_id, name=None):
        """Returns a random quote, and the user who wrote the quote."""
        query = (session.query(Quote)
            .join(Chat, Quote.chat_id == Chat.id)
            .filter(Chat.id == chat_id, Quote.deleted == False))

        if name is not None:
            query = query.filter(User.username.ilike(f'%{name}%'))

        quote = query.order_by(func.random()).first()

        if quote is not None:
            return quote, quote.sent_by
        else:
            return None, None

    def search_quote(self, session, chat_id, terms, tags):
        """Returns a random quote matching the search terms, and the user
        who wrote the quote."""
        query = (session.query(Quote)
            .filter(Quote.chat_id == chat_id, Quote.deleted == False))

        if terms:
            query = query.filter(Quote.content.ilike(f'%{terms}%'))

        for tag in tags:
            query = tag.apply_filter(query)

        quote = query.order_by(func.random()).first()

        print(query)

        if quote is not None:
            return quote, quote.sent_by
        else:
            return None, None

    def add_quote(self, session, chat_id, message_id, is_forward,
            sent_at, sent_by_id, content, content_html, quoted_by_id, score=0):
        """Inserts a quote."""
        quote = (session.query(Quote.id, Quote.deleted)
            .filter(Quote.sent_at == sent_at,
                User.id == sent_by_id,
                Quote.content_html == content_html)
            .one_or_none())

        if quote is None:
            pass
        else:
            quote_id, deleted = quote

            if deleted:
                return None, self.QUOTE_PREVIOUSLY_DELETED

            quote = self.get_quote_by_id(session, quote_id)
            return quote, self.QUOTE_ALREADY_EXISTS

        chat = self.get_chat_by_id(session, chat_id)
        sent_by = self.get_user_by_id(session, sent_by_id)
        quoted_by = self.get_user_by_id(session, quoted_by_id)

        quote = Quote(
            chat=chat, message_id=message_id, is_forward=is_forward,
            sent_at=sent_at, sent_by=sent_by, content=content,
            content_html=content_html, quoted_by=quoted_by, score=score)

        session.add(quote)

        return quote, self.QUOTE_ADDED

    def add_quote_for_test(self, session, quote):
        return self.add_quote(session, quote.chat_id, quote.message_id,
            quote.is_forward, quote.sent_at, quote.sent_by_id, quote.content,
            quote.content_html, quote.quoted_by_id, quote.score)

    def delete_quote(self, session, quote_id):
        """Marks a quote as deleted."""
        quote = self.get_quote_by_id(session, quote_id)
        quote.deleted = True

    # Quote message methods

    def add_message(self, session, chat_id, message_id, quote):
        """Adds a quote message, i.e. a bot message that contains a quote."""
        chat = self.get_chat_by_id(session, chat_id)
        session.add(chat)

        qm = QuoteMessage(chat=chat, message_id=message_id, quote=quote)
        session.add(qm)

    def get_quote_id_from_message(self, session, chat_id, message_id):
        """Returns the quote ID corresponding to the given quote message."""
        Qm = QuoteMessage

        try:
            return (session.query(Qm.quote_id)
                .filter(Qm.chat_id == chat_id,
                    Qm.message_id == message_id)
                .scalar())
        except NoResultFound:
            return None

    def get_quote_messages(self, session, quote_id):
        """Returns a list of all messages that refer to the given quote."""
        return (session.query(QuoteMessage)
            .filter(QuoteMessage.quote_id == quote_id)) or []

    # Vote methods

    def get_user_vote(self, session, user_id, quote_id):
        return (session.query(Vote)
            .filter(Vote.user_id == user_id, Vote.quote_id == quote_id)
            .one_or_none())

    def add_vote(self, session, user_id, quote_id, direction):
        user = self.get_user_by_id(session, user_id)
        session.add(user)
        quote = self.get_quote_by_id(session, quote_id)
        session.add(quote)

        vote = self.get_user_vote(session, user_id, quote_id)

        if vote is None:
            vote = Vote(user=user, quote=quote, direction=direction)
            session.add(vote)
        elif vote.direction == direction:
            return self.ALREADY_VOTED
        else:
            vote.direction = direction
            session.add(vote)

        _, score, _ = self.get_votes_by_id(session, quote_id)
        quote.score = score

        if score <= self.SCORE_TO_DELETE:
            self.delete_quote(session, quote_id)
            return self.QUOTE_DELETED
        else:
            return self.VOTE_ADDED

    def get_votes(self, session, chat_id, message_id):
        """Returns the number of upvotes / downvotes and score for a quote."""
        quote_id = self.get_quote_id_from_message(session, chat_id, message_id)
        return self.get_votes_by_id(session, quote_id)

    def get_votes_by_id(self, session, quote_id):
        """Returns the number of upvotes / downvotes and score for a quote."""
        votes = session.query(Vote.direction).filter(Vote.quote_id == quote_id)

        up, score, down = 0, 0, 0

        for vote in votes:
            vote = vote.direction

            if vote == 1:
                up += 1
                score += 1
            elif vote == -1:
                down += 1
                score -= 1

        return up, score, down
