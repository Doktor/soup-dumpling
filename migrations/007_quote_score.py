from database import QuoteDatabase

database = QuoteDatabase()

database.connect()

select = "SELECT id FROM quote;"
database.c.execute(select)

quote_ids = database.c.fetchall()

for quote_id in quote_ids:
    quote_id = int(quote_id[0])

    _, score, _ = database.get_votes_by_id(quote_id)

    update = "UPDATE quote SET score = ? WHERE id = ?;"
    database.c.execute(update, (score, quote_id))

database.db.commit()
