import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year_published in reader:
        db.execute("INSERT INTO books (isbn, title, author, year_published) "
                   "VALUES (:isbn, :title, :author, :year_published)",
                   {"isbn": isbn, "title": title, "author": author, "year_published": year_published})
        print(f"Added {title}from {author}.")
    db.commit()


if __name__ == "__main__":
    main()
