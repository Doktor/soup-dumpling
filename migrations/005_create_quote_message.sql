CREATE TABLE IF NOT EXISTS quote_message (
    id INTEGER PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    quote_id INTEGER NOT NULL
);
