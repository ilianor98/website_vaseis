from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql, datetime

app = Flask(__name__)

# Set the secret key for the app
app.secret_key = "your_secret_key_here"


@app.route("/")
def index():
    # Check if the user is logged in
    if "username" in session:
        # Connect to the database
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="2403",
            db="vas",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        # Execute the query to retrieve data from the database
        with conn.cursor() as cursor:
            sql = "SELECT * FROM user"
            cursor.execute(sql)
            data = cursor.fetchall()

        with conn.cursor() as cursor:
            sql = "SELECT COUNT(ISBN) FROM book;"
            cursor.execute(sql)
            result = cursor.fetchone()
            num_books = result["COUNT(ISBN)"]

        with conn.cursor() as cursor:
            sql = "SELECT COUNT(id) FROM school;"
            cursor.execute(sql)
            result_lib = cursor.fetchone()
            num_lib = result_lib["COUNT(id)"]

        with conn.cursor() as cursor:
            sql = "SELECT COUNT(id) FROM user;"
            cursor.execute(sql)
            result_us = cursor.fetchone()
            num_user = result_us["COUNT(id)"]

        with conn.cursor() as cursor:
            sql = "select count(u.id) from user u inner join role l on u.id=l.user_id where role = 1;"
            cursor.execute(sql)
            result_stud = cursor.fetchone()
            num_stud = result_stud["count(u.id)"]

        with conn.cursor() as cursor:
            sql = "select count(u.id) from user u inner join role l on u.id=l.user_id where role = 2;"
            cursor.execute(sql)
            result_prof = cursor.fetchone()
            num_prof = result_prof["count(u.id)"]

        # Close the database connection
        conn.close()

        # Render the HTML template and pass the data to it
        return render_template(
            "index.html",
            data=data,
            num_books=num_books,
            num_lib=num_lib,
            num_user=num_user,
            num_stud=num_stud,
            num_prof=num_prof,
        )
    else:
        return redirect(url_for("login"))


@app.route("/student")
def about():
    # Check if the user is logged in
    if "username" in session:
        # Connect to the database
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="2403",
            db="vas",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        # Execute the query to retrieve data from the database
        with conn.cursor() as cursor:
            sql = "SELECT * FROM student"
            cursor.execute(sql)
            data = cursor.fetchall()

        # Close the database connection
        conn.close()

        return render_template("student.html", data=data)
    else:
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    # Check if the user is already logged in
    if "username" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        # Connect to the database
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="2403",
            db="vas",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        # Get username and password from form submission
        username = request.form["username"]
        password = request.form["password"]

        # Query database for user
        with conn.cursor() as cursor:
            query = "SELECT * FROM user WHERE username = %s AND password = %s"
            cursor.execute(query, (username, password))
            result = cursor.fetchone()

        # Close the database connection
        conn.close()

        if result:
            # If user exists, store username in session and redirect to home page
            session["username"] = username
            return redirect(url_for("index"))
        else:
            # If user does not exist, redirect back to login page with error message
            return render_template("login.html", error="Invalid username or password")
    else:
        return render_template("login.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("username", None)
    flash("You were logged out")
    return redirect(url_for("login"))


@app.route("/rate", methods=["GET", "POST"])
def rate():
    if "username" in session:
        username = session["username"]
        book_id = request.form.get("book_id")
        rating = request.form.get("rating")

        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="2403",
            db="vas",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        with conn.cursor() as cursor:
            # Retrieve the user_id based on the username
            sql = f"SELECT id FROM user WHERE username = '{username}'"
            cursor.execute(sql)
            result = cursor.fetchone()
            user_id = result["id"]

            # Insert the rating into the ratings table
            sql = "INSERT INTO ratings (user_id, book_id, rating) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_id, book_id, rating))

        conn.commit()
        conn.close()

        return redirect(url_for("rating"))
    else:
        return redirect(url_for("login"))


@app.route("/school")
def school():
    if "username" in session:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="2403",
            db="vas",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        with conn.cursor() as cursor:
            sql = "SELECT * from book_inventory_view;"
            cursor.execute(sql)
            data = cursor.fetchall()
            school_ids = [item["school_id"] for item in data]

        conn.close()

        return render_template("school.html", school_ids=school_ids, data=data)
    else:
        return redirect(url_for("login"))


@app.route("/delayed")
def delayed():
    if "username" in session:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="2403",
            db="vas",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        with conn.cursor() as cursor:
            sql = "SELECT * FROM borrow"
            cursor.execute(sql)
            data = cursor.fetchall()

        conn.close()

        return render_template("delayed.html", data=data)
    else:
        return redirect(url_for("login"))


@app.route("/users")
def users():
    if "username" in session:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="2403",
            db="vas",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        with conn.cursor() as cursor:
            sql = "SELECT u.username, u.first_name, u.last_name, CASE r.role WHEN 1 THEN 'student' WHEN 2 THEN 'professor' WHEN 3 THEN 'admin' ELSE 'unknown' END AS role_label FROM user u JOIN role r ON u.id = r.user_id ORDER BY r.role ASC;"
            cursor.execute(sql)
            data = cursor.fetchall()

        conn.close()

        return render_template("users.html", data=data)
    else:
        return redirect(url_for("login"))


@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if request.method == "POST":
        # Retrieve the form data
        username = request.form["username"]
        password = request.form["password"]
        num_books = int(request.form["num_books"])
        active = int(request.form["active"])
        last_name = request.form["last_name"]
        first_name = request.form["first_name"]
        age = int(request.form["age"])

        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="2403",
            db="vas",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        try:
            # Create a cursor object to interact with the database
            with conn.cursor() as cursor:
                # Prepare the SQL statement
                sql = (
                    "INSERT INTO user (username, password, num_books, active, last_name, first_name, age) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                )
                print(username, first_name, last_name, password, num_books, active, age)

                # Execute the SQL statement
                cursor.execute(
                    sql,
                    (username, password, num_books, active, last_name, first_name, age),
                )

            # Commit the transaction
            conn.commit()

            # Redirect to a success page or any other desired page
            return render_template("add_user_success.html")

        except Exception as e:
            # Handle the error, rollback the transaction, or display an error message
            print(f"Error: {e}")
            conn.rollback()
            # Redirect to an error page or display an error message to the user
            return render_template("add_user_fail.html")

        finally:
            # Close the database connection
            conn.close()

        # Redirect to a success page or any other desired page

    # Render the add_user.html template for GET requests
    return render_template("add_user.html")


@app.route("/rating")
def rating():
    if "username" in session:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="2403",
            db="vas",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        with conn.cursor() as cursor:
            sql = "SELECT b.titleBK, b.ISBN, AVG(r.rating) AS average_rating FROM book b LEFT JOIN ratings r ON b.ISBN = r.book_id GROUP BY b.titleBK, b.ISBN;"
            cursor.execute(sql)
            data = cursor.fetchall()

        conn.close()

        return render_template("rating.html", data=data)
    else:
        return redirect(url_for("login"))


@app.route("/book")
def book():
    if "username" in session:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="2403",
            db="vas",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        with conn.cursor() as cursor:
            sql = "select titleBK, ISBN from book;"
            cursor.execute(sql)
            data = cursor.fetchall()

        conn.close()

        return render_template("book.html", data=data)
    else:
        return redirect(url_for("login"))


@app.route("/book/<int:isbn>")
def book_info(isbn):
    if "username" in session:
        conn = pymysql.connect(
            host="localhost",
            user="root",
            password="2403",
            db="vas",
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )

        with conn.cursor() as cursor:
            # Retrieve book information
            book_sql = "SELECT * FROM book WHERE ISBN = %s;"
            cursor.execute(book_sql, (isbn,))
            book = cursor.fetchone()

            # Retrieve author information for the book
            author_sql = """
            SELECT author.* FROM author
            JOIN book_author ON author.id = book_author.author_id
            WHERE book_author.book_isbn = %s;
            """
            cursor.execute(author_sql, (isbn,))
            authors = cursor.fetchall()

        conn.close()

        if book:
            return render_template("book_info.html", book=book, authors=authors)
        else:
            return "Book not found."

    else:
        return redirect(url_for("login"))


@app.route("/rent/<isbn>", methods=["GET", "POST"])
def rent(isbn):
    if "username" in session:
        if request.method == "POST":
            # Retrieve user_id
            username = session["username"]
            conn = pymysql.connect(
                host="localhost",
                user="root",
                password="2403",
                db="vas",
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )

            try:
                with conn.cursor() as cursor:
                    # Retrieve the user_id using the username
                    user_id_sql = "SELECT id FROM user WHERE username = %s;"
                    cursor.execute(user_id_sql, (username,))
                    result = cursor.fetchone()
                    user_id = result["id"]

                    school_id_sql = (
                        "SELECT school_id FROM user_school WHERE user_id = %s;"
                    )
                    cursor.execute(school_id_sql, (user_id,))
                    result1 = cursor.fetchone()
                    school_id = result1["school_id"]

                    reservation_date = datetime.date.today().strftime("%Y-%m-%d")

                    # Insert into the reservation table
                    reservation_sql = "INSERT INTO reservation (user_id, book_id, reservation_date, school_id) VALUES (%s, %s, %s, %s);"
                    cursor.execute(
                        reservation_sql, (user_id, isbn, reservation_date, school_id)
                    )
                    conn.commit()
            finally:
                conn.close()

            return "Rent request submitted successfully!"

        else:
            conn = pymysql.connect(
                host="localhost",
                user="root",
                password="2403",
                db="vas",
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
            )

            try:
                with conn.cursor() as cursor:
                    # Retrieve book information
                    book_sql = "SELECT * FROM book WHERE ISBN = %s;"
                    cursor.execute(book_sql, (isbn,))
                    book = cursor.fetchone()

                    # Retrieve author information for the book
                    author_sql = """
                    SELECT author.* FROM author
                    JOIN book_author ON author.id = book_author.author_id
                    WHERE book_author.book_isbn = %s;
                    """
                    cursor.execute(author_sql, (isbn,))
                    authors = cursor.fetchall()
            finally:
                conn.close()

            if book:
                return render_template("rent.html", book=book, authors=authors)
            else:
                return "Book not found."
    else:
        return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
