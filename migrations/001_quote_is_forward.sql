-- Add new column: is_forward
CREATE TABLE IF NOT EXISTS quote_new (
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

    UNIQUE(chat_id, message_id) ON CONFLICT ROLLBACK,
    UNIQUE(sent_at, sent_by, content_html) ON CONFLICT ROLLBACK
);

-- Copy data to new table
INSERT INTO quote_new
    (id, chat_id, message_id, is_forward,
    sent_at, sent_by, content, content_html, quoted_by)
SELECT
    id, chat_id, message_id, 0,
    sent_at, sent_by, content, content_html, quoted_by
FROM quote;

-- Rename the new table
DROP TABLE quote;
ALTER TABLE quote_new RENAME TO quote;
