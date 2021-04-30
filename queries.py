import psycopg2
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from werkzeug.security import generate_password_hash
import requests
#
DATABASE_URL ='postgresql://lhkejbssojucjk:b862ec6522c00e1bdc173af49036dc0abaf4a7fa5ac0b168e799aead95cc46f4@ec2-52-1-115-6.compute-1.amazonaws.com:5432/d3djp2n6ghoahm'

# DATABASE_URL = "postgresql://postgres:password@localhost:5432/projectone"
engine = create_engine(DATABASE_URL)
db = sessionmaker(bind=engine)
dbSession = db()

def add_user(username, password):
    data = {'username' : username, 'password' : generate_password_hash(password)}
    statement = text("""
                        INSERT INTO users(username, password) VALUES(:username, :password)
                    """)
    dbSession.execute(statement, data)
    dbSession.commit()


# Query to check if the username already exists
def check_username(username):
    query = f"""
        SELECT * FROM users WHERE username='{username}'
    """
    result = dbSession.execute(query).first()
    return result


# Search query for search page
def search_text(param):
    result = dbSession.execute(
                "SELECT * FROM books WHERE LOWER(title) LIKE :isbn OR LOWER(title) LIKE :title OR LOWER(author) LIKE :author OR year LIKE :year ORDER BY isbn",
                {"isbn":param, "title": param, "author": param, "year": param}).fetchall()
    return result

def get_details_isbn(isbn):
    
    print(f"{isbn}")
    res = requests.get(f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data")
    jsonFormat = res.json()[f'ISBN:{isbn}'] if f"ISBN:{isbn}" in res.json().keys() else "None"
    if jsonFormat != "None":
        image_url = jsonFormat['cover']['medium'] if 'cover' in jsonFormat.keys() else "None"
    else:
        return "None"
 
    
    return image_url
    
def return_detail(isbn):
    query = f"""
        SELECT isbn,title,author,year,average_rating,image_url FROM books WHERE isbn='{isbn}'
    """
    result = dbSession.execute(query).one()
    return result 

def search_reviews(user, book_id):
    query = f"""
        SELECT * FROM reviews WHERE user_id='{user}' AND book_isbn='{book_id}'
    """
    result = dbSession.execute(query).fetchall()
    return result

def get_all_reviews(book_id):
    query = f"""
        SELECT * FROM reviews WHERE book_isbn='{book_id}'
    """
    result = dbSession.execute(query).fetchall()
    return result


#Post review update query
def update_review(books_isbn, user_id, description, rating):
    query = f"""
        UPDATE reviews SET description = '{description}', rating='{rating}' WHERE user_id='{user_id}' AND book_isbn='{books_isbn}'
    """
    dbSession.execute(query)
    dbSession.commit()
# process api isbn request query
def api_query(q_isbn):
    return dbSession.execute("SELECT * FROM books WHERE isbn LIKE :isbn LIMIT 1", {"isbn": q_isbn}).fetchone()


def insert_review(book_isbn, user_id, description, rating):
    query = f"""
        INSERT INTO reviews(book_isbn, user_id, description, rating) VALUES (:book_isbn, :user_id, :description, :rating)
    """
    dbSession.execute(query, {'description':description, 'rating':rating, 'user_id':user_id, 'book_isbn':book_isbn})
    dbSession.commit()


def insert_additional():
    without_images = dbSession.execute("""
        SELECT isbn from books WHERE image_url='None';
    """).fetchall()
    count = 1
    for entry in without_images:
        print(entry[0])
        req = requests.get(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{entry[0]}")
        
        print(f"{req.json()}, {count}" )
        result = req.json()
        if (result['totalItems'] > 0):
            if ('imageLinks' in result['items'][0]['volumeInfo'].keys()):
                dbSession.execute(f"""
                    UPDATE books set image_url = '{entry[0]}' WHERE isbn='{entry[0]}';
                """, {'image_url': result['items'][0]['volumeInfo']['imageLinks']['thumbnail']})
                dbSession.commit()
                count += 1


def insert_google_books():
    allbooks  = dbSession.execute("""
        select isbn from books;
    """).fetchall()
 
    for entry in allbooks:
        req = requests.get(f"https://www.googleapis.com/books/v1/volumes?q=isbn:{entry[0]}")
        result = req.json()
        
        if (result['totalItems'] > 0):
            if ('averageRating' in result['items'][0]['volumeInfo']):
                dbSession.execute(f"""
                    UPDATE books set google_books_rating = '{result['items'][0]['volumeInfo']['averageRating']}'
                    WHERE isbn = '{entry[0]}';
                """)
                print("Updated single data")

            if ('ratingsCount' in result['items'][0]['volumeInfo']):
                dbSession.execute(f"""
                    UPDATE books set rating_count = '{result['items'][0]['volumeInfo']['ratingsCount']}'
                    WHERE isbn = '{entry[0]}';
                """)
                print("Updated single data")
        
        dbSession.commit()
        #     if ('rating' in result['items'][0]):

        

if (__name__ == '__main__'):
    # insert_additional()
    insert_google_books()



