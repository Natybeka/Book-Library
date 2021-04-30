import csv
import os
import psycopg2
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from queries import get_details_isbn

DATABASE_URL ='postgresql://lhkejbssojucjk:b862ec6522c00e1bdc173af49036dc0abaf4a7fa5ac0b168e799aead95cc46f4@ec2-52-1-115-6.compute-1.amazonaws.com:5432/d3djp2n6ghoahm'
# DATABASE_URL = "postgresql://postgres:password@localhost:5432/projectone"

#set up local database url
engine = create_engine(DATABASE_URL)
db = sessionmaker(bind=engine)
dbSession = db()

def parse_csv():
    if (os.path.exists('books.csv')):
        with open('books.csv', 'r') as books_sheet:
            has_header = csv.Sniffer().has_header(books_sheet.read(1024))
            books_sheet.seek(0)  # Rewind.
            reader = csv.reader(books_sheet)
            if has_header:
                next(reader)
                count = 0
            for isbn,title, author, year in reader:
                image_url= get_details_isbn(isbn)
                statement = text("""
                    INSERT INTO books(isbn, title, author, year, image_url) VALUES(:isbn, :title, :author, :year, :image_url)
                    ON CONFLICT (isbn) DO NOTHING
                """)
                dbSession.execute(statement, {'isbn':isbn, 'title': title, 'author':author, 'year': year, 'image_url': image_url})
                print(f"Added data point {count}")
                count+=1
                dbSession.commit()
                    


# Setup tables triggers and functions for db operations
def create_tables():
    dbSession.execute("""
        CREATE TABLE IF NOT EXISTS books (isbn VARCHAR(250) PRIMARY KEY, title TEXT, author TEXT, year TEXT, average_rating 
        DECIMAL(2,1) CHECK (average_rating >= 0 AND average_rating <= 5) DEFAULT 0.0, description TEXT, rating_count INTEGER DEFAULT 0, image_url TEXT);
    """)

    dbSession.execute("""
        CREATE TABLE IF NOT EXISTS users (username VARCHAR(250) PRIMARY KEY, password TEXT);
    """)

    dbSession.execute("""
        CREATE TABLE IF NOT EXISTS reviews (review_id SERIAL PRIMARY KEY, rating DECIMAL(2,1) CHECK (rating >= 0 AND rating <= 5),
        description TEXT, user_id VARCHAR(250), review_date DATE NOT NULL DEFAULT CURRENT_DATE, book_isbn VARCHAR(250),
        CONSTRAINT user_constraint 
            FOREIGN KEY(user_id) 
                REFERENCES users(username),
        CONSTRAINT book_id 
            FOREIGN KEY(book_isbn) 
                REFERENCES books(isbn));
    """)

    dbSession.execute("""
        CREATE OR REPLACE FUNCTION addbookrating() 
        RETURNS TRIGGER LANGUAGE PLPGSQL 
        AS $$
        BEGIN 
            UPDATE books
            SET average_rating = ((rating_count * average_rating) + NEW.rating)/ (rating_count + 1), rating_count = rating_count + 1
            WHERE NEW.book_isbn = isbn;

            RETURN NEW;
        END
        $$;
    """)

    dbSession.execute("""
        CREATE OR REPLACE FUNCTION updatebookrating() 
        RETURNS TRIGGER LANGUAGE PLPGSQL 
        AS $$
        BEGIN 
            UPDATE books
            SET average_rating = (SELECT AVG(rating) FROM reviews WHERE reviews.book_isbn = NEW.book_isbn)
            WHERE isbn = NEW.book_isbn;

            RETURN NEW;
        END
        $$;
    """)

    dbSession.execute("""
        CREATE TRIGGER add_rating AFTER INSERT ON reviews
        FOR EACH ROW EXECUTE PROCEDURE addbookrating();
    """)

    dbSession.execute("""
        CREATE TRIGGER update_rating AFTER UPDATE ON reviews
        FOR EACH ROW EXECUTE PROCEDURE updatebookrating();
    """)



    
    
    dbSession.commit()
    print("tables for database successfully created!")

    
               
if __name__=='__main__':
    create_tables()
    parse_csv()

