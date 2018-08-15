import dataclasses
import factory
import logging
import os
import pytest
import random

from soup.database import QuoteDatabase


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
    title = 'Telegram Group'
    username = 'telegram_group'


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
