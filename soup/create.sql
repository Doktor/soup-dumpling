CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT,
    username TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS chat (
    id INTEGER PRIMARY KEY,
    type TEXT NOT NULL CHECK (type IN ('private', 'group', 'supergroup', 'channel')),
    title TEXT,
    username TEXT
);

CREATE TABLE IF NOT EXISTS membership (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES user (id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    chat_id INTEGER NOT NULL REFERENCES chat (id)
        ON UPDATE CASCADE
        ON DELETE CASCADE,

    UNIQUE(user_id, chat_id) ON CONFLICT ROLLBACK
);

CREATE TABLE IF NOT EXISTS quote (
    id INTEGER PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    is_forward BOOLEAN NOT NULL CHECK (is_forward IN (0, 1)),
    sent_at INTEGER NOT NULL,
    sent_by INTEGER NOT NULL REFERENCES user (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    content TEXT,
    content_html TEXT,
    quoted_by INTEGER REFERENCES user (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    deleted INTEGER DEFAULT 0 NOT NULL,
    score INTEGER DEFAULT 0 NOT NULL,

    UNIQUE(chat_id, message_id) ON CONFLICT ROLLBACK,
    UNIQUE(sent_at, sent_by, content_html) ON CONFLICT ROLLBACK
);

CREATE TABLE IF NOT EXISTS quote_message (
    id INTEGER PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    quote_id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS vote (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    quote_id INTEGER NOT NULL,
    direction INTEGER NOT NULL,

    UNIQUE(user_id, quote_id) ON CONFLICT ROLLBACK
);