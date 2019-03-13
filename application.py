import os

from flask import Flask, session, render_template, request, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

from helpers import login_required

app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # User reached route via POST
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html", message="Please enter a username.")

        # Ensure password was submitted
        if not request.form.get("password"):
            return render_template("error.html", message="Please enter a password.")

        # Ensure password confirmation was submitted
        if not request.form.get("password_confirmation"):
            return render_template("error.html", message="Please confirm your password.")

        # Ensure password and password confirmation match
        elif request.form.get("password") != request.form.get("password_confirmation"):
            return render_template("error.html", message="Password confirmation does not match.")

        # Query database for username
        username_exists = db.execute("SELECT COUNT (*) FROM users WHERE username = :username",
                                     {"username": request.form.get("username")}).fetchall()

        # If username exists render error
        if username_exists != [(0,)]:
            return render_template("error.html", message="Username already exists.")

        username = request.form.get("username")

        # Hash password
        password_hash = generate_password_hash(request.form.get("password"))

        # Insert user into database
        db.execute("INSERT INTO users (username, password_hash) VALUES (:username, :password_hash)",
                   {"username": username, "password_hash": password_hash})

        db.commit()

        return render_template("index.html")

    # User reached rout via GET
    else:
        return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget any user_id
    session.clear()

    # User reached route via POST
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("error.html", message="Please enter username.")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("error.html", message="Please enter password.")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchall()

        # Ensure username exists ans password is correct
        if len(rows[0]) != 3 or not check_password_hash(rows[0][2], request.form.get("password")):
            return render_template("error.html", message="Invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0][0]

        # Redirect user to search
        return redirect("/search")

    # User reached route via GET
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():

    # Forget any user id
    session.clear()

    # Redirect user to index
    return redirect("/")


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():

    # User reached route via POST
    if request.method == "POST":

        # If searched by title
        if request.form.get("title"):
            books = db.execute("SELECT DISTINCT title, author, isbn, year_published, id "
                               "FROM books WHERE title LIKE :title",
                               {"title": '%'+request.form.get("title")+'%'}).fetchall()
            if not books:
                return render_template("search.html", message="Sorry, could not find a book with this title.")
            else:
                return render_template("search.html", results="Results", books=books)

        # If searched by author
        elif request.form.get("author"):
            books = db.execute("SELECT DISTINCT title, author, isbn, year_published, id "
                               "FROM books WHERE author LIKE :author",
                               {"author": '%'+request.form.get("author")+'%'}).fetchall()
            if not books:
                return render_template("search.html", message="Sorry, could not find a book from this author.")
            else:
                return render_template("search.html", results="Results", books=books)

        elif request.form.get("isbn"):
            books = db.execute("SELECT DISTINCT title, author, isbn, year_published, id "
                               "FROM books WHERE isbn LIKE :isbn",
                               {"isbn": '%'+request.form.get("isbn")+'&'}).fetchall()
            if not books:
                return render_template("search.html", message="Sorry, could not find a book with this ISBN.")
            else:
                return render_template("search.html", results="Results", books=books)

        else:
            return render_template("error.html", message="Please enter Title, Author, or ISBN.")

    # User reached route via GET
    else:
        return render_template("search.html")


@app.route("/book/<int:id>", methods=["GET", "POST"])
def books(id):

    book = db.execute("SELECT title, author, year_published, isbn FROM books WHERE id = :id",
                      {"id": id}).fetchall()

    return render_template("books.html", book=book)


if __name__ == '__main__':
    app.run(debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)
