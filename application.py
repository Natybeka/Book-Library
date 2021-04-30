import os
import json
from flask import Flask, session, render_template, url_for, request, flash, redirect, jsonify
from flask_session import Session   
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from queries import check_username, add_user, search_text, search_reviews, return_detail, get_all_reviews, update_review, insert_review, api_query
from werkzeug.security import check_password_hash


app = Flask(__name__)
app.secret_key = "qeruthfsd1238h120dh71hdhiud1988ncfd9123"
# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Setup views here for the search, login, register, and book page
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST", "GET"])
def register():
    # Register user to the database
    if (request.method == "POST"):
        username = request.form['username']
        password = request.form['password']
        reenter = request.form['re-password']

        # validate inputs for registration

        # Check if the username already exists
        if check_username(username):
            flash("User name already exists", category='error')
            return redirect(url_for('register'))
        elif password != reenter:
            flash("Passwords do not match", category='error')
            return redirect(url_for('register'))
        elif len(password) < 8:
            flash("password must be longer than 8 characters", category='error')
            return redirect(url_for('register'))
        else:
            add_user(username, password)
            flash("Account created Successfully. You can now login", category='success')
            return redirect(url_for('login'))
   
        
    else:
        return render_template("register.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = check_username(username)
        if user:
            if check_password_hash(user[1], password):
                session["user"] = username
                return redirect(url_for('user_home'))
            else:
                flash("Invalid password", category='error')
                return redirect(url_for("login"))
        else:
            flash("username doesn't exist", category='error')
            return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/home", methods=['GET'])
def user_home():
    usr = session['user']
    if usr == None:
        flash(f'Please log in to access homepage!', category='error')
        return redirect(url_for('login'))
    return render_template('user.html') 
        

@app.route("/search")
def search(): 
    if request.method == "GET":
        usr = session['user']
        if usr == None:
            flash("Please login to access search page!", category='error' )
            return redirect(url_for('login'), "303")
        else:
            query = request.args.get('q')
            if query is None:
                return render_template("search.html", message="No results.")
            text = f"%{query}%".lower()
            result = search_text(text)
            flash(f"Showing results for '{query}'", category='warning')
            return render_template("search.html", res=result, parameter=query)
        
    
    
@app.route("/logout")
def logout():
    session["user"] =  None
    flash("User logged out successfully", category='success')
    return redirect(url_for("login"))


@app.route("/<string:isbn>/review", methods=['GET', 'POST'])
def review(isbn):
    user = session['user']
    if user != None:
        alreadySubmitted = False 
        if (search_reviews(user, isbn)):
            alreadySubmitted = True

        if request.method == 'POST':
            if alreadySubmitted:
                update_review(isbn, user, request.form.get('reviewDescription'), int(str(request.form.get('selectedRating'))))
            else:
                insert_review(isbn, user, request.form.get('reviewDescription'), int(str(request.form.get('selectedRating'))))
                alreadySubmitted = True
            allRev = get_all_reviews(isbn)
            return redirect(url_for('review', isbn=isbn))

        elif request.method == 'GET':
            bookDetails = return_detail(isbn)
            allRev = get_all_reviews(isbn)
            flash(f"No reviews for {bookDetails[1]}", category='info')
            return render_template("review.html",submitted=alreadySubmitted, allReviews=allRev, detail=bookDetails, reviews=search_reviews(user,isbn))
    else:
        flash("You need to log in to review books", category='error')
        return redirect(url_for('login'))


#api route for request
@app.route('/api/<int:q_isbn>')
def isbn(q_isbn):
    q_isbn = f"%{q_isbn}%".lower()
    res = api_query(q_isbn) 
    if res is None:
        return jsonify(
            {
                "error_code": 404,
                "error_message": "Not Found"
            }
        ), 404

    result = {
        "title": res[1],
        "author": res[2],
        "year": res[3],
        "isbn": res[0],
        "review_count": res[6],
        "average_score": float(res[4])
    }
    return jsonify(result)
if __name__ == '__main__':
    app.run(debug=True)