import datetime
import re

from soup.classes import Quote, User


class Tag:
    value = None

    def apply_filter(self, query):
        raise NotImplementedError

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.value}>"

    def __repr__(self):
        return str(self)


class AuthorTag(Tag):
    def __init__(self, value=None):
        self.value = value.lower()

    def apply_filter(self, query):
        return (query.join(User, Quote.sent_by_id == User.id)
            .filter(User.first_name.ilike(f'%{self.value}%')
                    | User.last_name.ilike(f'%{self.value}%')))


class UsernameTag(Tag):
    def __init__(self, value=None):
        self.value = value.lower()

    def apply_filter(self, query):
        return (query.join(User, Quote.sent_by_id == User.id)
            .filter(User.username.ilike(f'%{self.value}%')))


class QuotedByTag(Tag):
    def __init__(self, value=None):
        self.value = value.lower()

    def apply_filter(self, query):
        return (query.join(User, Quote.quoted_by_id == User.id)
            .filter(User.username.ilike(f'%{self.value}%')))


class DateTag(Tag):
    def __init__(self, value=None):
        try:
            self.day = datetime.datetime.strptime(value, '%Y-%m-%d')
            self.next_day = self.day + datetime.timedelta(days=1)
        except ValueError as e:
            raise e

    def apply_filter(self, query):
        return query.filter(
            Quote.sent_at >= self.day,
            Quote.sent_at < self.next_day)


class ScoreTag(Tag):
    def __init__(self, value=None, cmp='='):
        self.value = int(value)
        self.cmp = cmp

    def apply_filter(self, query):
        if self.cmp == '<':
            return query.filter(Quote.score < self.value)
        elif self.cmp == '<=':
            return query.filter(Quote.score <= self.value)
        elif self.cmp == '>=':
            return query.filter(Quote.score >= self.value)
        elif self.cmp == '>':
            return query.filter(Quote.score > self.value)
        else:
            return query.filter(Quote.score == self.value)


TAGS = {
    'author': AuthorTag,
    'username': UsernameTag,
    'u': UsernameTag,
    'quoted_by': QuotedByTag,
    'date': DateTag,
    'score': ScoreTag,
}


def create_tag(name, value, cmp=None):
    tag = TAGS.get(name, None)

    if tag is None:
        raise ValueError("Invalid tag name")

    if cmp is not None:
        if cmp not in ['<', '<=', '>=', '>']:
            raise ValueError("Invalid comparator")
        else:
            try:
                return tag(value=value, cmp=cmp)
            except TypeError as e:
                raise ValueError("This tag does not accept comparators") from e

    return tag(value=value)


PATTERN = re.compile(r'^([-\w]+):(<|<=|>=|>)?([-\w]+)$')
