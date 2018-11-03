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

FILENAME = 'tests.db'


# Setup and teardown


def setup_module():
    if os.path.isfile(FILENAME):
        os.remove(FILENAME)


def teardown_module():
    os.remove(FILENAME)


# Fixtures


@pytest.fixture(scope='session')
def db():
    return QuoteDatabase(filename=FILENAME)


@pytest.fixture(scope='function', autouse=True)
def s(db):
    session = db.create_session()
    yield session
    session.close()


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


# User


def test__get_user_by_id__new_user__is_none(db, s):
    user = UserFactory()
    assert db.get_user_by_id(s, user.id) is None


def test__get_user_by_id__existing_user__is_not_none(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)
    assert db.get_user_by_id(s, user.id) is not None


def test__user_exists__new_user__is_false(db, s):
    user = UserFactory()
    assert not db.user_exists(s, user.id)


def test__user_exists__existing_user__is_true(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)
    assert db.user_exists(s, user.id)


def test__add_or_update_user__new_user__is_successful(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    db_user = db.get_user_by_id(s, user.id)
    for p in ('id', 'first_name', 'last_name', 'username'):
        assert getattr(user, p) == getattr(db_user, p)


def test__add_or_update_user__existing_user__is_successful(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    db_user = db.get_user_by_id(s, user.id)

    user.first_name = faker.first_name()
    user.last_name = faker.last_name()
    user.username = f'{user.first_name}_{user.last_name}'.lower()
    db.add_or_update_user(s, user)

    for p in ('first_name', 'last_name', 'username'):
        assert getattr(user, p) == getattr(db_user, p)


def test__get_user_chats__new_user__user_has_no_chats(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    assert len(db.get_user_chats(s, user.id)) == 0


def test__get_user_chats__user_with_chats__user_has_chats(db, s):
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


def test__get_user_score__user_has_score_0_in_current_chat(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    assert db.get_user_score(s, user.id, chat.id) == (0, 0, 0)


@pytest.mark.skip
def test__get_user_score__user_has_score_10_in_current_chat(db, s):
    pass


def test__get_user_quotes__user_has_no_quotes(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    assert len(list(db.get_user_quotes(s, user.id, chat.id))) == 0


def test__get_user_quotes__user_has_quotes(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    current = ChatFactory()
    db.add_or_update_chat(s, current)

    for _ in range(10):
        quote = QuoteFactory(sent_by_id=user.id, chat_id=current.id)
        db.add_quote_for_test(s, quote)

    assert len(list(db.get_user_quotes(s, user.id, current.id))) == 10


def test__get_user_quotes__user_has_no_quotes_in_current_chat__list_is_empty(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    current = ChatFactory()
    db.add_or_update_chat(s, current)

    other = ChatFactory()
    db.add_or_update_chat(s, other)

    for _ in range(10):
        quote = QuoteFactory(sent_by_id=user.id, chat_id=other.id)
        db.add_quote_for_test(s, quote)

    assert len(list(db.get_user_quotes(s, user.id, current.id))) == 0


# Chat


def test__get_chat_by_id__new_chat__is_none(db, s):
    chat = ChatFactory()
    assert db.get_chat_by_id(s, chat.id) is None


def test__get_chat_by_id__existing_chat__is_not_none(db, s):
    chat = ChatFactory()
    db.add_or_update_chat(s, chat)
    assert db.get_chat_by_id(s, chat.id) is not None


def test__chat_exists__new_chat__is_false(db, s):
    chat = ChatFactory()
    assert not db.chat_exists(s, chat.id)


def test__chat_exists__existing_chat__is_true(db, s):
    chat = ChatFactory()
    db.add_or_update_chat(s, chat)
    assert db.chat_exists(s, chat.id)


def test__add_or_update_chat__new_chat__is_successful(db, s):
    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    db_chat = db.get_chat_by_id(s, chat.id)
    for p in ('id', 'type', 'title', 'username'):
        assert getattr(chat, p) == getattr(db_chat, p)


def test__add_or_update_chat__existing_chat__is_successful(db, s):
    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    db_chat = db.get_chat_by_id(s, chat.id)

    city = faker.city()
    chat.title = f"Friends of {city}"
    chat.username = chat.title.lower().replace(' ', '_')
    db.add_or_update_chat(s, chat)

    for p in ('title', 'username'):
        assert getattr(chat, p) == getattr(db_chat, p)


def test__migrate_chat__existing_chat__chat_id_is_changed(db, s):
    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    old_id = chat.id
    db_chat = db.get_chat_by_id(s, old_id)

    new_id = generate_id()
    db.migrate_chat(s, chat.id, new_id)

    assert db_chat.id == new_id
    assert not db.chat_exists(s, old_id)
    assert db.chat_exists(s, new_id)


# Membership


def test__add_membership__new_pair__is_successful(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    db_chat = db.get_chat_by_id(s, chat.id)

    assert db_chat not in db.get_user_chats(s, user.id)
    db.add_membership(s, user.id, chat.id)
    assert db_chat in db.get_user_chats(s, user.id)


def test__add_membership__existing_pair__does_nothing(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    db_chat = db.get_chat_by_id(s, chat.id)

    for _ in range(5):
        db.add_membership(s, user.id, chat.id)

    chats = db.get_user_chats(s, user.id)
    assert db_chat in chats
    assert len(chats) == 1


def test__remove_membership__existing_pair__is_successful(db, s):
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
def test__most_quoted(db, s):
    pass


@pytest.mark.skip
def test__most_quotes_added(db, s):
    pass


@pytest.mark.skip
def test__get_highest_scoring(db, s):
    pass


@pytest.mark.skip
def test__get_lowest_scoring(db, s):
    pass


# Quotes


def test__get_quote_by_id__new_quote__is_none(db, s):
    quote = QuoteFactory()
    assert db.get_quote_by_id(s, quote.id) is None


def test__get_quote_by_ids__new_quote__is_none(db, s):
    quote = QuoteFactory()
    assert db.get_quote_by_ids(s, quote.chat_id, quote.message_id) is None


def test__get_quote_by_id__existing_quote__is_not_none(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    quote = QuoteFactory(sent_by_id=user.id, chat_id=chat.id)
    db_quote, _ = db.add_quote_for_test(s, quote)

    s.flush()
    assert db.get_quote_by_id(s, db_quote.id) is not None


def test__get_quote_by_ids__existing_quote__is_not_none(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    quote = QuoteFactory(sent_by_id=user.id, chat_id=chat.id)
    db.add_quote_for_test(s, quote)
    assert db.get_quote_by_ids(s, quote.chat_id, quote.message_id) is not None


def test__get_quote_count__new_pair__is_0(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    assert db.get_quote_count(s, chat.id) == 0


def test__get_quote_count__existing_pair__is_not_0(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    for _ in range(10):
        quote = QuoteFactory(sent_by_id=user.id, chat_id=chat.id)
        db.add_quote_for_test(s, quote)

    assert db.get_quote_count(s, chat.id) == 10


def test__get_quote_count__multiple_chats__only_counts_quotes_in_current_chat(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    current = ChatFactory()
    db.add_or_update_chat(s, current)

    other = ChatFactory()
    db.add_or_update_chat(s, other)

    for _ in range(10):
        quote = QuoteFactory(sent_by_id=user.id, chat_id=other.id)
        db.add_quote_for_test(s, quote)

    assert db.get_quote_count(s, current.id) == 0

    db.add_or_update_chat(s, current)

    assert db.get_quote_count(s, current.id) == 0


@pytest.mark.skip
def test__get_first_quote(db, s):
    pass


@pytest.mark.skip
def test__get_last_quote(db, s):
    pass


def test__get_random_quote__populated_chat__is_not_none(db, s):
    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    for _ in range(10):
        quote = QuoteFactory(sent_by_id=None, chat_id=chat.id)
        db.add_quote_for_test(s, quote)

    for _ in range(10):
        assert db.get_random_quote(s, chat.id) is not None


def test__get_random_quote__populated_chat__quote_is_from_current_chat(db, s):
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


def test__get_random_quote__populated_chat_and_specific_user__quote_is_by_user(db, s):
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
def test__search_quote(db, s):
    pass


def test__add_quote__new_quote__returns_quote_added(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    quote = QuoteFactory(sent_by_id=user.id, chat_id=chat.id)
    db_quote, status = db.add_quote_for_test(s, quote)

    assert db_quote is not None
    assert status == QuoteDatabase.QUOTE_ADDED


def test__add_quote__existing_quote__returns_quote_already_exists(db, s):
    user = UserFactory()
    db.add_or_update_user(s, user)

    chat = ChatFactory()
    db.add_or_update_chat(s, chat)

    quote = QuoteFactory(sent_by_id=user.id, chat_id=chat.id)
    db_quote1, _ = db.add_quote_for_test(s, quote)

    db_quote2, status = db.add_quote_for_test(s, quote)
    assert db_quote1 == db_quote2
    assert status == QuoteDatabase.QUOTE_ALREADY_EXISTS


def test__delete_quote__existing_quote__marks_quote_as_deleted(db, s):
    quote = QuoteFactory(sent_by_id=None, chat_id=None)
    db_quote, _ = db.add_quote_for_test(s, quote)
    s.flush()

    assert not db_quote.deleted
    db.delete_quote(s, db_quote.id)
    assert db_quote.deleted


# Quote messages


@pytest.mark.skip
def test__add_message(db, s):
    pass


@pytest.mark.skip
def test__get_quote_id_from_message(db, s):
    pass


@pytest.mark.skip
def test__get_quote_messages(db, s):
    pass


# Votes


@pytest.mark.skip
def test__get_user_vote(db, s):
    pass


@pytest.mark.skip
def test__add_vote(db, s):
    pass


@pytest.mark.skip
def test__get_votes(db, s):
    pass


@pytest.mark.skip
def test__get_votes_by_id(db, s):
    pass
