import dataclasses
import datetime
import factory
import factory.fuzzy
import faker
import logging
import os
import pytest
import random

from soup.database import QuoteDatabase

faker = faker.Faker()


# Mock classes


@dataclasses.dataclass
class User:
    id: int
    first_name: str
    last_name: str
    username: str


@dataclasses.dataclass
class Chat:
    id: int
    type: str
    title: str
    username: str


@dataclasses.dataclass
class Quote:
    id: int
    chat_id: int
    message_id: int

    is_forward: bool
    sent_at: datetime.datetime

    sent_by_id: int
    quoted_by_id: int

    content: str
    content_html: str

    deleted: bool
    score: int


# Factories


start_date = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)


def generate_bool():
    return random.choice((False, True))


def generate_id():
    return random.randint(-1e9, 1e9)


class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.LazyFunction(generate_id)
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    username = factory.LazyAttribute(
        lambda user: f"{user.first_name}_{user.last_name}".lower())


class ChatFactory(factory.Factory):
    class Meta:
        model = Chat

    id = factory.LazyFunction(generate_id)
    type = 'supergroup'
    title = factory.LazyAttribute(lambda chat: f"Friends of {faker.city()}")
    username = factory.LazyAttribute(
        lambda chat: chat.title.lower().replace(' ', '_'))


class QuoteFactory(factory.Factory):
    class Meta:
        model = Quote

    id = 0
    chat_id = factory.LazyFunction(generate_id)
    message_id = factory.LazyFunction(generate_id)

    is_forward = factory.LazyFunction(generate_bool)
    sent_at = factory.fuzzy.FuzzyDateTime(start_date)

    sent_by_id = factory.LazyFunction(generate_id)
    quoted_by_id = factory.LazyFunction(generate_id)

    content = ""
    content_html = ""

    deleted = False
    score = 0


# Fixtures


FILENAME = 'tests.db'


@pytest.fixture(scope='session')
def db():
    if os.path.isfile(FILENAME):
        os.remove(FILENAME)

    return QuoteDatabase(filename=FILENAME)


@pytest.fixture(scope='function', autouse=True)
def s(db):
    session = db.create_session()
    yield session
    session.close()


# User


def test_get_new_user_is_none(db, s):
    user = UserFactory()
    assert db.get_user_by_id(s, user.id) is None


def test_get_existing_user_is_not_none(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)
    assert db.get_user_by_id(s, user.id) is not None


def test_new_user_does_not_exist_in_database(db, s):
    user = UserFactory()
    assert not db.user_exists(s, user.id)


def test_existing_user_exists_in_database(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)
    assert db.user_exists(s, user.id)


def test_add_new_user(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    db_user = db.get_user_by_id(s, user.id)
    for p in ('id', 'first_name', 'last_name', 'username'):
        assert getattr(user, p) == getattr(db_user, p)


def test_update_existing_user(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    db_user = db.get_user_by_id(s, user.id)

    user.first_name = faker.first_name()
    user.last_name = faker.last_name()
    user.username = f'{user.first_name}_{user.last_name}'.lower()
    db.add_or_update_user(s, user)

    for p in ('first_name', 'last_name', 'username'):
        assert getattr(user, p) == getattr(db_user, p)


def test_user_has_no_groups(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    assert not db.get_user_chats(s, user.id)


def test_user_has_multiple_groups(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat1 = ChatFactory()
    db.add_or_update_chat(s, chat1)

    chat2 = ChatFactory()
    db.add_or_update_chat(s, chat2)

    db.add_membership(s, user.id, chat1.id)
    db.add_membership(s, user.id, chat2.id)

    db_chat1 = db.get_chat_by_id(s, chat1.id)
    db_chat2 = db.get_chat_by_id(s, chat2.id)

    chats = db.get_user_chats(s, user.id)
    assert db_chat1 in chats
    assert db_chat2 in chats


def test_user_score_is_0(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    assert db.get_user_score(s, user.id, chat.id) == (0, 0, 0)


@pytest.mark.skip
def test_user_score_is_10_in_current_chat(db, s):
    pass


def test_user_has_no_quotes(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    assert len(list(db.get_user_quotes(s, user.id, chat.id))) == 0


@pytest.mark.skip
def test_user_has_quotes_in_current_chat(db, s):
    pass


@pytest.mark.skip
def test_user_has_no_quotes_in_current_chat(db, s):
    pass


# Chat


def test_get_new_chat_is_none(db, s):
    chat = ChatFactory()
    assert db.get_chat_by_id(s, chat.id) is None


def test_get_existing_chat_is_not_none(db, s):
    chat = ChatFactory()
    db.add_or_update_chat(s, chat)
    assert db.get_chat_by_id(s, chat.id) is not None


def test_new_chat_does_not_exist_in_database(db, s):
    chat = ChatFactory()
    assert not db.chat_exists(s, chat.id)


def test_existing_chat_exists_in_database(db, s):
    chat = ChatFactory()
    db.add_or_update_chat(s, chat)
    assert db.chat_exists(s, chat.id)


def test_add_new_chat(db, s):
    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    db_chat = db.get_chat_by_id(s, chat.id)
    for p in ('id', 'type', 'title', 'username'):
        assert getattr(chat, p) == getattr(db_chat, p)


def test_update_existing_chat(db, s):
    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    db_chat = db.get_chat_by_id(s, chat.id)

    city = faker.city()
    chat.title = f"Friends of {city}"
    chat.username = chat.title.lower().replace(' ', '_')
    db.add_or_update_chat(s, chat)

    for p in ('title', 'username'):
        assert getattr(chat, p) == getattr(db_chat, p)


def test_migrate_chat(db, s):
    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    db_chat = db.get_chat_by_id(s, chat.id)

    new_id = generate_id()
    db.migrate_chat(s, chat.id, new_id)

    assert db_chat.id == new_id


# Membership


def test_add_user_to_chat(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    db_chat = db.get_chat_by_id(s, chat.id)

    assert db_chat not in db.get_user_chats(s, user.id)
    db.add_membership(s, user.id, chat.id)
    assert db_chat in db.get_user_chats(s, user.id)


def test_remove_user_from_chat(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    db_chat = db.get_chat_by_id(s, chat.id)

    db.add_membership(s, user.id, chat.id)
    db.remove_membership(s, user.id, chat.id)
    assert db_chat not in db.get_user_chats(s, user.id)


# Stats


@pytest.mark.skip
def test_most_quoted_users(db, s):
    pass


@pytest.mark.skip
def test_most_quotes_added(db, s):
    pass


@pytest.mark.skip
def test_get_highest_user_scores(db, s):
    pass


@pytest.mark.skip
def test_get_lowest_user_scores(db, s):
    pass


# Quotes


def test_get_new_quote_by_id_is_none(db, s):
    quote = QuoteFactory()
    assert db.get_quote_by_id(s, quote.id) is None


def test_get_new_quote_by_ids_is_none(db, s):
    quote = QuoteFactory()
    assert db.get_quote_by_ids(s, quote.chat_id, quote.message_id) is None


def test_get_existing_quote_by_id_is_not_none(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    quote = QuoteFactory(sent_by_id=user.id, chat_id=chat.id)
    db_quote, _ = db.add_quote_for_test(s, quote)

    s.flush()
    assert db.get_quote_by_id(s, db_quote.id) is not None


def test_get_existing_quote_by_ids_is_not_none(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    quote = QuoteFactory(sent_by_id=user.id, chat_id=chat.id)
    db.add_quote_for_test(s, quote)
    assert db.get_quote_by_ids(s, quote.chat_id, quote.message_id) is not None


def test_quote_count_is_0(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    assert db.get_quote_count(s, chat.id) == 0


def test_quote_count_is_10_in_current_chat(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    for _ in range(10):
        quote = QuoteFactory(sent_by_id=user.id, chat_id=chat.id)
        db.add_quote_for_test(s, quote)

    assert db.get_quote_count(s, chat.id) == 10


def test_quote_count_is_0_in_current_chat(db, s):
    """Quotes added to other chats don't affect the count in this chat."""
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat1 = ChatFactory()
    db.add_or_update_chat(s, chat1)

    for _ in range(10):
        quote = QuoteFactory(sent_by_id=user.id, chat_id=chat1.id)
        db.add_quote_for_test(s, quote)

    chat2 = ChatFactory()
    db.add_or_update_chat(s, chat2)

    assert db.get_quote_count(s, chat2.id) == 0


@pytest.mark.skip
def test_get_first_quote(db, s):
    pass


@pytest.mark.skip
def test_get_last_quote(db, s):
    pass


def test_get_random_quote(db, s):
    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    for _ in range(10):
        quote = QuoteFactory(sent_by_id=None, chat_id=chat.id)
        db.add_quote_for_test(s, quote)

    for _ in range(10):
        assert db.get_random_quote(s, chat.id) is not None


def test_get_random_quote_from_current_chat(db, s):
    """Quotes should only be retrieved from the current chat."""
    chat1 = ChatFactory()
    db.add_or_update_chat(s, chat1)

    for _ in range(10):
        quote = QuoteFactory(sent_by_id=None, chat_id=chat1.id)
        db.add_quote_for_test(s, quote)

    chat2 = ChatFactory()
    db.add_or_update_chat(s, chat2)

    for _ in range(10):
        quote = QuoteFactory(sent_by_id=None, chat_id=chat2.id)
        db.add_quote_for_test(s, quote)

    for _ in range(10):
        quote, _ = db.get_random_quote(s, chat1.id)
        assert quote.chat_id == chat1.id and quote.chat_id != chat2.id


def test_get_random_quote_by_username(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    for _ in range(10):
        quote = QuoteFactory(sent_by_id=user.id, chat_id=chat.id)
        db.add_quote_for_test(s, quote)

    for _ in range(10):
        quote, _ = db.get_random_quote(s, chat.id, name=user.username)
        assert quote is not None


@pytest.mark.skip
def test_search_quote(db, s):
    pass


@pytest.mark.ship
def test_add_quote(db, s):
    pass


def test_delete_quote(db, s):
    quote = QuoteFactory(sent_by_id=None, chat_id=None)
    db_quote, _ = db.add_quote_for_test(s, quote)
    s.flush()

    assert not db_quote.deleted
    db.delete_quote(s, db_quote.id)
    assert db_quote.deleted


def test_delete_deleted_quote(db, s):
    quote = QuoteFactory(sent_by_id=None, chat_id=None)
    db_quote, _ = db.add_quote_for_test(s, quote)
    s.flush()

    db.delete_quote(s, db_quote.id)
    assert db_quote.deleted

    db.delete_quote(s, db_quote.id)
    assert db_quote.deleted


# Quote messages


@pytest.mark.skip
def test_add_message(db, s):
    pass


@pytest.mark.skip
def test_get_quote_id_from_message(db, s):
    pass


@pytest.mark.skip
def test_get_quote_messages(db, s):
    pass


# Votes


@pytest.mark.skip
def test_get_user_vote(db, s):
    pass


@pytest.mark.skip
def test_add_vote(db, s):
    pass


@pytest.mark.skip
def test_get_votes(db, s):
    pass


@pytest.mark.skip
def test_get_votes_by_id(db, s):
    pass
