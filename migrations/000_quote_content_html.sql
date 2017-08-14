-- Add new column: content_html
CREATE TABLE IF NOT EXISTS quote_new (
    id INTEGER PRIMARY KEY,
    chat_id INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    sent_at INTEGER NOT NULL,
    sent_by INTEGER NOT NULL REFERENCES user (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    content TEXT,
    content_html TEXT,
    quoted_by INTEGER REFERENCES user (id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    UNIQUE(chat_id, message_id) ON CONFLICT ROLLBACK
);

-- Copy data to new table
INSERT INTO quote_new SELECT id, chat_id, message_id, sent_at, sent_by, content, content, quoted_by FROM quote;

-- Replace HTML tags
UPDATE quote_new SET content = replace(content, '<b>', '');
UPDATE quote_new SET content = replace(content, '</b>', '');
UPDATE quote_new SET content = replace(content, '<i>', '');
UPDATE quote_new SET content = replace(content, '</i>', '');
UPDATE quote_new SET content = replace(content, '<code>', '');
UPDATE quote_new SET content = replace(content, '</code>', '');
UPDATE quote_new SET content = replace(content, '<pre>', '');
UPDATE quote_new SET content = replace(content, '</pre>', '');

-- Rename the new table
DROP TABLE quote;
ALTER TABLE quote_new RENAME TO quote;