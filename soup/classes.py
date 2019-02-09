from sqlalchemy import (
    Boolean, Column, Enum, DateTime, ForeignKey, Integer, PrimaryKeyConstraint,
    String, Text, UniqueConstraint)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Table

Base = declarative_base()


membership_table = Table('membership', Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id')),
    Column('chat_id', Integer, ForeignKey('chat.id')),
    PrimaryKeyConstraint('user_id', 'chat_id'))


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String)
    username = Column(String, unique=True)

    chats = relationship(
        "Chat", secondary=membership_table, back_populates="users")
    quotes = relationship(
        "Quote", back_populates="sent_by", foreign_keys="Quote.sent_by_id")
    quotes_added = relationship(
        "Quote", back_populates="quoted_by", foreign_keys="Quote.quoted_by_id")
    votes = relationship("Vote", back_populates="user")


class Chat(Base):
    __tablename__ = 'chat'

    id = Column(Integer, primary_key=True, autoincrement=False)
    type = Column(
        Enum('private', 'group', 'supergroup', 'channel'), nullable=False)
    title = Column(String)
    username = Column(String, unique=True)

    users = relationship(
        "User", secondary=membership_table, back_populates="chats")
    quotes = relationship("Quote", back_populates="chat")
    quote_messages = relationship("QuoteMessage", back_populates="chat")


class Quote(Base):
    __tablename__ = 'quote'

    id = Column(Integer, primary_key=True, autoincrement=True)

    chat_id = Column(Integer, ForeignKey('chat.id'), nullable=True)
    chat = relationship(
        "Chat", back_populates="quotes", cascade='save-update, merge')

    message_id = Column(Integer)
    is_forward = Column(Boolean, default=False)
    sent_at = Column(DateTime)

    sent_by_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    sent_by = relationship(
        "User", back_populates="quotes", cascade='save-update, merge',
        foreign_keys=[sent_by_id])

    content = Column(Text)
    content_html = Column(Text)

    file_id = Column(Text)

    message_type = Column(Enum('text', 'photo'), default='text')

    quoted_by_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    quoted_by = relationship(
        "User", back_populates="quotes_added", cascade='save-update, merge',
        foreign_keys=[quoted_by_id])

    deleted = Column(Boolean, default=False)
    score = Column(Integer, default=0)

    constraint1 = UniqueConstraint('chat_id', 'message_id')
    constraint2 = UniqueConstraint('sent_at', 'sent_by_id', 'content_html')

    messages = relationship("QuoteMessage", back_populates="quote")
    votes = relationship("Vote", back_populates="quote")


class QuoteMessage(Base):
    __tablename__ = 'quote_message'

    id = Column(Integer, primary_key=True, autoincrement=True)

    chat_id = Column(Integer, ForeignKey('chat.id'), nullable=True)
    chat = relationship(
        "Chat", back_populates="quote_messages", cascade='save-update, merge')

    message_id = Column(Integer)

    quote_id = Column(Integer, ForeignKey('quote.id'), nullable=True)
    quote = relationship(
        "Quote", back_populates="messages", cascade='save-update, merge')


class Vote(Base):
    __tablename__ = 'vote'

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    user = relationship(
        "User", back_populates="votes", cascade='save-update, merge')

    quote_id = Column(Integer, ForeignKey('quote.id'), nullable=True)
    quote = relationship(
        "Quote", back_populates="votes", cascade='save-update, merge')

    direction = Column(Integer, default=0, nullable=False)

    constraint1 = UniqueConstraint('user_id', 'quote_id')
