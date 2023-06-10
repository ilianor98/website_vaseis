from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file,
)
import pymysql, subprocess, os

app = Flask(__name__)


app.secret_key = "your_secret_key_here"

config = {
    "user": "root",
    "password": "2403",
    "host": "localhost",
    "database": "vas",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


@app.context_processor
def inject_user():
    if "username" in session:
        username = session["username"]
        role = session["role"]
        u_id = session["u_id"]
        return dict(username=username, role=role, u_id=u_id)
    return dict(username=None, role=None, u_id=None)


@app.route("/master_admin")
def master_admin():
    if "username" in session and session["role"] == "master admin":
        conn = pymysql.connect(**config)
        username = session["username"]
        with conn.cursor() as cursor:
            sql = "SELECT first_name, last_name from user WHERE username = %s"
            cursor.execute(sql, (username,))
            result = cursor.fetchone()
            admin_first = result["first_name"]
            admin_last = result["last_name"]
            admin_name = f"{admin_first} {admin_last}"

        return render_template("master_admin.html", admin_name=admin_name)
    else:
        return redirect(url_for("not_admin"))


@app.route("/backup_interface")
def backup_interface():
    if "username" in session and session["role"] == "master admin":
        return render_template("backup_interface.html")
    else:
        return redirect(url_for("not_admin"))


@app.route("/backup")
def backup_database():
    db_host = config["host"]
    db_user = config["user"]
    db_password = config["password"]
    db_name = config["database"]

    backup_dir = request.args.get("file_destination")
    backup_name = request.args.get("file_name") + ".sql"
    backup_path = os.path.join(backup_dir, backup_name)

    # mariadb_bin_dir = "C:/Program Files/Mariadb 11.1/bin"
    # os.chdir(mariadb_bin_dir)

    command = f"mysqldump --host={db_host} --user={db_user} --password={db_password} --routines -B {db_name} > {backup_path}"

    try:
        subprocess.run(command, shell=True, check=True)

        return send_file(backup_path, as_attachment=True, download_name=backup_name)
    except subprocess.CalledProcessError:
        flash("Error: An error occurred while creating the database backup.", "error")
        return redirect(url_for("backup_interface"))


@app.route("/admins")
def admins():
    if "username" in session and session["role"] == "master admin":
        conn = pymysql.connect(**config)
        with conn.cursor() as cursor:
            sql = "SELECT u.first_name, u.last_name, u.id, us.school_id, CASE r.role WHEN 3 THEN 'admin' ELSE 'not admin' END AS role_label FROM user u INNER JOIN role r ON u.id = r.user_id INNER JOIN user_school us ON u.id = us.user_id WHERE r.role = 3 ORDER BY school_id;"
            cursor.execute(sql)
            data = cursor.fetchall()

        return render_template("admins.html", data=data)
    else:
        return redirect(url_for("not_admin"))


@app.route("/admins_edit", methods=["GET", "POST"])
def admins_edit():
    if "username" in session and session["role"] == "master admin":
        if request.method == "POST":
            first_name = request.form.get("first_name")
            last_name = request.form.get("last_name")
            username = request.form.get("username")
            active = request.form.get("active")
            age = request.form.get("age")
            school_id = request.form.get("school_id")
            user_id = request.form.get("user_id")

            return redirect(
                url_for(
                    "admins_edit_submit",
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    active=active,
                    age=age,
                    school_id=school_id,
                    user_id=user_id,
                )
            )

        conn = pymysql.connect(**config)
        with conn.cursor() as cursor:
            sql = "SELECT u.*, us.school_id, CASE r.role WHEN 3 THEN 'admin' ELSE 'not admin' END AS role_label FROM user u INNER JOIN role r ON u.id = r.user_id INNER JOIN user_school us ON u.id = us.user_id WHERE r.role = 3 ORDER BY school_id;"
            cursor.execute(sql)
            data = cursor.fetchall()

        return render_template("admins_edit.html", data=data)
    else:
        return redirect(url_for("not_admin"))


@app.route("/admins_edit_submit", methods=["POST"])
def admins_edit_submit():
    if "username" in session and session["role"] == "master admin":
        username = request.form.get("username")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        active = request.form.get("active")
        age = request.form.get("age")
        school_id = request.form.get("school_id")
        user_id = request.form.get("user_id")

        conn = pymysql.connect(**config)
        with conn.cursor() as cursor:
            sql = "UPDATE user SET username = %s, first_name = %s, last_name = %s, active = %s, age = %s WHERE id = %s;"
            cursor.execute(sql, (username, first_name, last_name, active, age, user_id))
            conn.commit()

        with conn.cursor() as cursor:
            sql = "UPDATE user_school SET school_id = %s WHERE user_id = %s"
            cursor.execute(sql, (school_id, user_id))
            conn.commit()

        flash("Admin updated successfully!", "success")
        return redirect(url_for("admins_edit"))
    else:
        return redirect(url_for("not_admin"))


@app.route("/")
def index():
    if "username" in session:
        conn = pymysql.connect(**config)

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

        conn.close()
        role = session["role"]
        username = session["username"]
        u_id = session["u_id"]

        return render_template(
            "index.html",
            data=data,
            num_books=num_books,
            num_lib=num_lib,
            num_user=num_user,
            num_stud=num_stud,
            num_prof=num_prof,
            username=username,
            role=role,
            u_id=u_id,
        )
    else:
        return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "username" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        conn = pymysql.connect(**config)

        form_username = request.form["username"]
        password = request.form["password"]

        with conn.cursor() as cursor:
            query = "SELECT * FROM user WHERE username = %s AND password = %s"
            cursor.execute(query, (form_username, password))
            result = cursor.fetchone()

        if result:
            session_username = result["username"]
            u_id = result["id"]
            with conn.cursor() as cursor:
                sql = "SELECT r.role FROM user u INNER JOIN role r ON u.id = r.user_id WHERE u.username = %s"
                cursor.execute(sql, (session_username,))
                result_r = cursor.fetchone()

                role = None
                if result_r:
                    role_temp = result_r["role"]
                    if role_temp == 1:
                        role = "student"
                    elif role_temp == 2:
                        role = "professor"
                    elif role_temp == 3:
                        role = "admin"
                    elif role_temp == 4:
                        role = "master admin"

        conn.close()

        if result:
            session["username"] = session_username
            session["role"] = role
            session["u_id"] = u_id
            print(session["username"], session["role"], session["u_id"])
            return redirect(url_for("index"))
        else:
            return render_template("login.html", error="Invalid username or password")
    else:
        return render_template("login.html")


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/admin")
def admin():
    if "username" in session and session["role"] == "admin":
        conn = pymysql.connect(**config)
        username = session["username"]
        with conn.cursor() as cursor:
            sql = "SELECT first_name, last_name, id from user WHERE username = %s"
            cursor.execute(sql, (username,))
            result = cursor.fetchone()
            id = result["id"]
            admin_first = result["first_name"]
            admin_last = result["last_name"]
            admin_name = f"{admin_first} {admin_last}"
        with conn.cursor() as cursor:
            sql = "SELECT * from user_school where user_id = %s"
            cursor.execute(sql, (id,))
            result_s = cursor.fetchone()
            school_id = result_s["school_id"]

        return render_template("admin.html", admin_name=admin_name, school_id=school_id)
    else:
        return redirect(url_for("not_admin"))


@app.route("/notadmin")
def not_admin():
    return render_template("not_admin.html")


@app.route("/rate/<isbn>", methods=["GET", "POST"])
def rate(isbn):
    if "username" in session:
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            sql = "select * from book where ISBN = %s"
            cursor.execute(sql, (isbn,))
            book = cursor.fetchone()

        conn.close()

        return render_template("rate.html", book=book)
    else:
        return redirect(url_for("login"))


@app.route("/submit_rating/<isbn>", methods=["POST"])
def submit_rating(isbn):
    if "username" in session:
        rating = request.form.get("rating")
        username = session["username"]
        book_id = isbn

        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            sql = "SELECT id FROM user WHERE username = %s"
            cursor.execute(sql, (username,))
            result = cursor.fetchone()
            user_id = result["id"]

        with conn.cursor() as cursor:
            sql = "insert into ratings(book_id, user_id, rating) values (%s, %s, %s)"
            cursor.execute(sql, (book_id, user_id, rating))
            result = cursor.fetchall()
            conn.commit()

        conn.close()

        flash("Rating submitted successfully.", "success")
        return redirect(url_for("book_info", isbn=isbn))
    else:
        return redirect(url_for("login"))


@app.route("/school")
def school():
    if "username" in session:
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            sql = "SELECT * from school;"
            cursor.execute(sql)
            data = cursor.fetchall()

        conn.close()

        return render_template("school.html", data=data)
    else:
        return redirect(url_for("login"))


@app.route("/users")
def users():
    if "username" in session:
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            sql = "SELECT u.username, u.first_name, u.last_name, CASE r.role WHEN 1 THEN 'student' WHEN 2 THEN 'professor' WHEN 3 THEN 'admin' WHEN 4 THEN 'master admin ' ELSE 'unknown' END AS role_label FROM user u JOIN role r ON u.id = r.user_id ORDER BY r.role ASC;"
            cursor.execute(sql)
            data = cursor.fetchall()

        conn.close()

        return render_template("users.html", data=data)
    else:
        return redirect(url_for("login"))


from flask import request
import pymysql


@app.route("/users_active")
def users_active():
    if "username" in session and session["role"] == "admin":
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            search_term = request.args.get("search", "")
            if search_term:
                sql = """
                SELECT u.id AS user_id, u.username, u.first_name, u.last_name, us.school_id,
                    CASE u.active WHEN 1 THEN 'ACTIVE' WHEN 0 THEN 'NOT ACTIVE' END AS active_state, 
                    CASE r.role WHEN 1 THEN 'student' WHEN 2 THEN 'professor' WHEN 3 THEN 'admin' WHEN 4 THEN 'master admin ' ELSE 'unknown' END AS role_label 
                FROM user u 
                JOIN role r ON u.id = r.user_id 
                JOIN user_school us ON u.id = us.user_id
                WHERE u.id LIKE %s
                ORDER BY u.active, us.school_id, r.role;
                """
                cursor.execute(sql, f"%{search_term}%")
            else:
                sql = """
                SELECT u.id AS user_id, u.username, u.first_name, u.last_name, us.school_id,
                    CASE u.active WHEN 1 THEN 'ACTIVE' WHEN 0 THEN 'NOT ACTIVE' END AS active_state, 
                    CASE r.role WHEN 1 THEN 'student' WHEN 2 THEN 'professor' WHEN 3 THEN 'admin' WHEN 4 THEN 'master admin ' ELSE 'unknown' END AS role_label 
                FROM user u 
                JOIN role r ON u.id = r.user_id 
                JOIN user_school us ON u.id = us.user_id
                ORDER BY u.active, us.school_id, r.role;
                """
                cursor.execute(sql)

            data = cursor.fetchall()

        conn.close()

        return render_template("users_active.html", data=data)
    else:
        return redirect(url_for("not_admin"))


@app.route("/toggle_user_active/<int:user_id>/<string:active_state>", methods=["POST"])
def toggle_user_active(user_id, active_state):
    if "username" in session and session["role"] == "admin":
        conn = pymysql.connect(**config)

        new_active_state = 0 if active_state == "ACTIVE" else 1

        with conn.cursor() as cursor:
            sql = "UPDATE user SET active = %s WHERE id = %s"
            cursor.execute(sql, (new_active_state, user_id))
            conn.commit()

        conn.close()

        return redirect(url_for("users_active"))
    else:
        return redirect(url_for("not_admin"))


@app.route("/add_user", methods=["GET", "POST"])
def add_user():
    if "username" in session and session["role"] == "admin":
        if request.method == "POST":
            username = request.form["username"]
            password = request.form["password"]
            num_books = int(request.form["num_books"])
            active = int(request.form["active"])
            last_name = request.form["last_name"]
            first_name = request.form["first_name"]
            age = int(request.form["age"])

            conn = pymysql.connect(**config)

            try:
                with conn.cursor() as cursor:
                    sql = (
                        "INSERT INTO user (username, password, num_books, active, last_name, first_name, age) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                    )
                    print(
                        username,
                        first_name,
                        last_name,
                        password,
                        num_books,
                        active,
                        age,
                    )

                    cursor.execute(
                        sql,
                        (
                            username,
                            password,
                            num_books,
                            active,
                            last_name,
                            first_name,
                            age,
                        ),
                    )

                conn.commit()

                return render_template("add_user_success.html")

            except Exception as e:
                print(f"Error: {e}")
                conn.rollback()

                return render_template("add_user_fail.html")

            finally:
                conn.close()

        return render_template("add_user.html")
    else:
        return redirect(url_for("not_admin"))


@app.route("/rating")
def rating():
    if "username" in session:
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            sql = "SELECT b.titleBK, b.ISBN, AVG(r.rating) AS average_rating FROM book b LEFT JOIN ratings r ON b.ISBN = r.book_id GROUP BY b.titleBK, b.ISBN;"
            cursor.execute(sql)
            data = cursor.fetchall()

        conn.close()

        return render_template("rating.html", data=data)
    else:
        return redirect(url_for("login"))


@app.route("/book", methods=["GET", "POST"])
def book():
    if "username" in session:
        conn = pymysql.connect(**config)
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM category")
            categories = cursor.fetchall()

        if request.method == "POST":
            search_query = request.form.get("search_query")
            category_id = request.form.get("category_id")
            author_search = request.form.get("author_search")

            if category_id == "0":
                category_id = None

            params = []

            sql = """
                SELECT b.titleBK, GROUP_CONCAT(DISTINCT a.name) AS author_names, GROUP_CONCAT(DISTINCT c.category) AS categories, b.ISBN
                FROM book b
                LEFT JOIN book_author ba ON b.ISBN = ba.book_isbn
                LEFT JOIN author a ON ba.author_id = a.id
                LEFT JOIN book_category bc ON b.ISBN = bc.book_id
                LEFT JOIN category c ON bc.category_id = c.id
                WHERE 1=1
            """

            if search_query:
                sql += " AND b.titleBK LIKE %s"
                params.append(f"%{search_query}%")

            if category_id:
                sql += " AND bc.category_id = %s"
                params.append(category_id)

            if author_search:
                sql += " AND a.name LIKE %s"
                params.append(f"%{author_search}%")

            sql += " GROUP BY b.titleBK"

            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                data = cursor.fetchall()
        else:
            sql = """
                SELECT b.titleBK, GROUP_CONCAT(DISTINCT a.name) AS author_names, GROUP_CONCAT(DISTINCT c.category) AS categories, b.ISBN
                FROM book b
                LEFT JOIN book_author ba ON b.ISBN = ba.book_isbn
                LEFT JOIN author a ON ba.author_id = a.id
                LEFT JOIN book_category bc ON b.ISBN = bc.book_id
                LEFT JOIN category c ON bc.category_id = c.id
                GROUP BY b.titleBK
            """

            with conn.cursor() as cursor:
                cursor.execute(sql)
                data = cursor.fetchall()

        conn.close()

        return render_template("book.html", data=data, categories=categories)
    else:
        return redirect(url_for("login"))


@app.route("/book/<int:isbn>")
def book_info(isbn):
    if "username" in session:
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            book_sql = "SELECT * FROM book WHERE ISBN = %s;"
            cursor.execute(book_sql, (isbn,))
            book = cursor.fetchone()

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


@app.route("/book_update", methods=["GET", "POST"])
def book_update():
    if "username" in session and session["role"] == "admin":
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM category")
            categories = cursor.fetchall()

        if request.method == "POST":
            search_query = request.form.get("search_query")
            category_id = request.form.get("category_id")

            if category_id == "0":
                category_id = None

            sql = "SELECT b.titleBK, b.ISBN FROM book b WHERE b.titleBK LIKE %s"

            params = [f"%{search_query}%"]

            if category_id is not None:
                sql += " AND EXISTS (SELECT 1 FROM book_category bc WHERE bc.book_id = b.ISBN AND bc.category_id = %s)"
                params.append(category_id)

            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                data = cursor.fetchall()
        else:
            sql = "SELECT b.titleBK, b.ISBN, GROUP_CONCAT(a.name) AS author_names FROM book b INNER JOIN book_author ba ON b.ISBN = ba.book_isbn INNER JOIN author a ON ba.author_id = a.id GROUP BY b.titleBK, b.ISBN;"
            with conn.cursor() as cursor:
                cursor.execute(sql)
                data = cursor.fetchall()

        conn.close()

        return render_template("book_update.html", data=data, categories=categories)
    else:
        return redirect(url_for("not_admin"))


@app.route("/book_update_form/<isbn>", methods=["GET", "POST"])
def update_book_form(isbn):
    if "username" in session and session["role"] == "admin":
        conn = pymysql.connect(**config)

        if request.method == "POST":
            title = request.form.get("title")
            publisher = request.form.get("publisher")
            num_pages = request.form.get("num_pages")
            language = request.form.get("language")
            summary = request.form.get("summary")
            image = request.form.get("image")

            with conn.cursor() as cursor:
                sql = "UPDATE book SET titleBK=%s, publisher=%s, num_pages=%s, language=%s, summary=%s, image=%s WHERE ISBN=%s"
                cursor.execute(
                    sql, (title, publisher, num_pages, language, summary, image, isbn)
                )
            conn.commit()

            flash("Book details updated successfully!", "success")
            return redirect(url_for("book_info", isbn=isbn))

        with conn.cursor() as cursor:
            sql = "SELECT * FROM book WHERE ISBN = %s"
            cursor.execute(sql, (isbn,))
            book = cursor.fetchone()

        return render_template("update_book_form.html", isbn=isbn, book=book)

    return redirect(url_for("not_admin"))


@app.route("/book_add", methods=["GET", "POST"])
def book_add():
    if "username" in session and session["role"] == "admin":
        conn = pymysql.connect(**config)

        if request.method == "POST":
            isbn = request.form.get("isbn")
            title = request.form.get("title")
            publisher = request.form.get("publisher")
            num_pages = request.form.get("num_pages")
            language = request.form.get("language")
            summary = request.form.get("summary")
            image = request.form.get("image")

            with conn.cursor() as cursor:
                sql = "INSERT INTO book (ISBN, titleBK, publisher, num_pages, language, summary, image) VALUES (%s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(
                    sql, (isbn, title, publisher, num_pages, language, summary, image)
                )
            conn.commit()

            flash("Book added successfully!", "success")
            return redirect(url_for("book_info", isbn=isbn))
        return render_template("book_add.html")
    else:
        return redirect(url_for("not_admin"))


@app.route("/rent/<isbn>", methods=["GET", "POST"])
def rent(isbn):
    if "username" in session:
        if request.method == "POST":
            id = session["u_id"]
            conn = pymysql.connect(**config)

            try:
                with conn.cursor() as cursor:
                    reservation_sql = "call make_reservation(%s,%s)"
                    cursor.execute(
                        reservation_sql,
                        (
                            isbn,
                            id,
                        ),
                    )
                    result = cursor.fetchone()
                    message = result["message"]
                    print(message)

                    conn.commit()
            finally:
                conn.close()

            if message == "Reservation made successfully.":
                flash(message, "success")
            else:
                flash(f"Error: {message}", "error")
            return redirect(url_for("user_reservations"))

        else:
            conn = pymysql.connect(**config)

            try:
                with conn.cursor() as cursor:
                    book_sql = "SELECT * FROM book WHERE ISBN = %s;"
                    cursor.execute(book_sql, (isbn,))
                    book = cursor.fetchone()

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


@app.route("/open_reservations")
def open_reservations():
    if "username" in session and session["role"] == "admin":
        admin_username = session["username"]

        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            query = "SELECT school_id FROM user_school WHERE user_id IN (SELECT id FROM user WHERE username = %s)"
            cursor.execute(query, (admin_username,))
            result = cursor.fetchone()

        if result:
            school_id = result["school_id"]

            with conn.cursor() as cursor:
                query = "SELECT * FROM reservation WHERE school_id = %s and return_date IS NULL and borrow_date IS NOT NULL;"
                cursor.execute(query, (school_id,))
                reservations = cursor.fetchall()

            conn.close()

            if reservations:
                return render_template(
                    "open_reservations.html", reservations=reservations
                )
        else:
            return "Error: School ID not found for the admin user."
    else:
        return redirect(url_for("not_admin"))


@app.route("/pending_reservations")
def pending_reservations():
    if "username" in session and session["role"] == "admin":
        admin_username = session["username"]

        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            query = "SELECT school_id FROM user_school WHERE user_id IN (SELECT id FROM user WHERE username = %s)"
            cursor.execute(query, (admin_username,))
            result = cursor.fetchone()

        if result:
            school_id = result["school_id"]

            with conn.cursor() as cursor:
                query = "SELECT * FROM reservation WHERE school_id = %s and reservation_status = 0 and is_approved = 0;"
                cursor.execute(query, (school_id,))
                reservations = cursor.fetchall()

            conn.close()

            return render_template(
                "pending_reservations.html", reservations=reservations
            )
        else:
            return "Error: School ID not found for the admin user."
    else:
        return redirect(url_for("not_admin"))


@app.route("/approved_reservations")
def approved_reservations():
    if "username" in session and session["role"] == "admin":
        admin_username = session["username"]

        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            query = "SELECT school_id FROM user_school WHERE user_id IN (SELECT id FROM user WHERE username = %s)"
            cursor.execute(query, (admin_username,))
            result = cursor.fetchone()

        if result:
            school_id = result["school_id"]

            with conn.cursor() as cursor:
                query = "SELECT * FROM reservation WHERE school_id = %s and reservation_status = 0 and is_approved = 1;"
                cursor.execute(query, (school_id,))
                reservations = cursor.fetchall()

            conn.close()

            return render_template(
                "approved_reservations.html", reservations=reservations
            )
        else:
            return "Error: School ID not found for the admin user."
    else:
        return redirect(url_for("not_admin"))


@app.route("/past_reservations")
def past_reservations():
    if "username" in session and session["role"] == "admin":
        admin_username = session["username"]

        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            query = "SELECT school_id FROM user_school WHERE user_id IN (SELECT id FROM user WHERE username = %s)"
            cursor.execute(query, (admin_username,))
            result = cursor.fetchone()

        if result:
            school_id = result["school_id"]

            with conn.cursor() as cursor:
                query = "SELECT * FROM reservation WHERE school_id = %s and return_date IS NOT NULL;"
                cursor.execute(query, (school_id,))
                reservations = cursor.fetchall()

            conn.close()

            return render_template("past_reservations.html", reservations=reservations)
        else:
            return "Error: School ID not found for the admin user."
    else:
        return redirect(url_for("not_admin"))


@app.route("/reservations_info/<reservation_id>", methods=["GET", "POST"])
def reservations_info(reservation_id):
    if "username" in session and session["role"] == "admin":
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            book_sql = "SELECT * FROM reservation WHERE reservation_id = %s;"
            cursor.execute(book_sql, (reservation_id,))
            reservation = cursor.fetchone()
            user_id = reservation["user_id"]

        with conn.cursor() as cursor:
            user_sql = "select * from user where id = %s"
            cursor.execute(user_sql, (user_id,))
            user = cursor.fetchone()

        with conn.cursor() as cursor:
            user_sql = "select * from user_school where id = %s"
            cursor.execute(user_sql, (user_id,))
            user_school = cursor.fetchone()

        with conn.cursor() as cursor:
            sql = "SELECT r.role FROM user u INNER JOIN role r ON u.id = r.user_id WHERE u.id = %s"
            cursor.execute(sql, (user_id,))
            result_r = cursor.fetchone()

            role_u = None
            if result_r:
                role_temp = result_r["role"]
                if role_temp == 1:
                    role_u = "student"
                elif role_temp == 2:
                    role_u = "professor"
                elif role_temp == 3:
                    role_u = "admin"
                elif role_temp == 4:
                    role_u = "master admin"

        conn.close()

        if book:
            return render_template(
                "reservations_info.html",
                reservation=reservation,
                user=user,
                user_school=user_school,
                role_u=role_u,
            )
        else:
            return "Reservation not found."
    else:
        return redirect(url_for("not_admin"))


@app.route("/pending_reservations_info/<reservation_id>", methods=["GET", "POST"])
def pending_reservations_info(reservation_id):
    if ("username" in session and session["role"] == "admin") or (
        "username" in session
    ):
        if request.method == "POST":
            conn = pymysql.connect(**config)

            try:
                with conn.cursor() as cursor:
                    reservation_sql = "call approve_reservation(%s)"
                    cursor.execute(reservation_sql, (reservation_id,))
                    result = cursor.fetchone()
                    message = result["message"]

                    conn.commit()
            finally:
                conn.close()

            flash(message, "success")
            return redirect(url_for("pending_reservations"))

        else:
            conn = pymysql.connect(**config)
            with conn.cursor() as cursor:
                book_sql = "SELECT * FROM reservation WHERE reservation_id = %s;"
                cursor.execute(book_sql, (reservation_id,))
                reservation = cursor.fetchone()
                user_id = reservation["user_id"]

            with conn.cursor() as cursor:
                user_sql = "select * from user where id = %s"
                cursor.execute(user_sql, (user_id,))
                user = cursor.fetchone()

            with conn.cursor() as cursor:
                user_sql = "select * from user_school where id = %s"
                cursor.execute(user_sql, (user_id,))
                user_school = cursor.fetchone()

            with conn.cursor() as cursor:
                sql = "SELECT r.role FROM user u INNER JOIN role r ON u.id = r.user_id WHERE u.id = %s"
                cursor.execute(sql, (user_id,))
                result_r = cursor.fetchone()

                role_u = None
                if result_r:
                    role_temp = result_r["role"]
                    if role_temp == 1:
                        role_u = "student"
                    elif role_temp == 2:
                        role_u = "professor"
                    elif role_temp == 3:
                        role_u = "admin"
                    elif role_temp == 4:
                        role_u = "master admin"

            conn.close()

            return render_template(
                "pending_reservations_info.html",
                reservation=reservation,
                user=user,
                user_school=user_school,
                role_u=role_u,
            )
    else:
        return redirect(url_for("not_admin"))


@app.route("/approved_reservations_info/<reservation_id>", methods=["GET", "POST"])
def approved_reservations_info(reservation_id):
    if ("username" in session and session["role"] == "admin") or (
        "username" in session
    ):
        if request.method == "POST":
            conn = pymysql.connect(**config)

            try:
                with conn.cursor() as cursor:
                    reservation_sql = "call borrow_book(%s);"
                    cursor.execute(reservation_sql, (reservation_id,))
                    result = cursor.fetchone()
                    message = result["message"]

                    conn.commit()
            finally:
                conn.close()

            flash(message, "success")
            return redirect(url_for("approved_reservations"))

        else:
            conn = pymysql.connect(**config)
            with conn.cursor() as cursor:
                book_sql = "SELECT * FROM reservation WHERE reservation_id = %s;"
                cursor.execute(book_sql, (reservation_id,))
                reservation = cursor.fetchone()
                user_id = reservation["user_id"]

            with conn.cursor() as cursor:
                user_sql = "select * from user where id = %s"
                cursor.execute(user_sql, (user_id,))
                user = cursor.fetchone()

            with conn.cursor() as cursor:
                user_sql = "select * from user_school where id = %s"
                cursor.execute(user_sql, (user_id,))
                user_school = cursor.fetchone()

            with conn.cursor() as cursor:
                sql = "SELECT r.role FROM user u INNER JOIN role r ON u.id = r.user_id WHERE u.id = %s"
                cursor.execute(sql, (user_id,))
                result_r = cursor.fetchone()

                role_u = None
                if result_r:
                    role_temp = result_r["role"]
                    if role_temp == 1:
                        role_u = "student"
                    elif role_temp == 2:
                        role_u = "professor"
                    elif role_temp == 3:
                        role_u = "admin"
                    elif role_temp == 4:
                        role_u = "master admin"

            conn.close()

            return render_template(
                "approved_reservations_info.html",
                reservation=reservation,
                user=user,
                user_school=user_school,
                role_u=role_u,
            )
    else:
        return redirect(url_for("not_admin"))


@app.route("/open_reservations_info/<reservation_id>", methods=["GET", "POST"])
def open_reservations_info(reservation_id):
    if ("username" in session and session["role"] == "admin") or (
        "username" in session
    ):
        if request.method == "POST":
            conn = pymysql.connect(**config)

            try:
                with conn.cursor() as cursor:
                    reservation_sql = "call return_book(%s);"
                    cursor.execute(reservation_sql, (reservation_id,))
                    result = cursor.fetchone()
                    message = result["message"]

                    conn.commit()
            finally:
                conn.close()

            flash(message, "success")
            return redirect(url_for("open_reservations"))

        else:
            conn = pymysql.connect(**config)
            with conn.cursor() as cursor:
                book_sql = "SELECT * FROM reservation WHERE reservation_id = %s;"
                cursor.execute(book_sql, (reservation_id,))
                reservation = cursor.fetchone()
                user_id = reservation["user_id"]

            with conn.cursor() as cursor:
                user_sql = "select * from user where id = %s"
                cursor.execute(user_sql, (user_id,))
                user = cursor.fetchone()

            with conn.cursor() as cursor:
                user_sql = "select * from user_school where id = %s"
                cursor.execute(user_sql, (user_id,))
                user_school = cursor.fetchone()

            with conn.cursor() as cursor:
                sql = "SELECT r.role FROM user u INNER JOIN role r ON u.id = r.user_id WHERE u.id = %s"
                cursor.execute(sql, (user_id,))
                result_r = cursor.fetchone()

                role_u = None
                if result_r:
                    role_temp = result_r["role"]
                    if role_temp == 1:
                        role_u = "student"
                    elif role_temp == 2:
                        role_u = "professor"
                    elif role_temp == 3:
                        role_u = "admin"
                    elif role_temp == 4:
                        role_u = "master admin"

            conn.close()

            return render_template(
                "open_reservations_info.html",
                reservation=reservation,
                user=user,
                user_school=user_school,
                role_u=role_u,
            )
    else:
        return redirect(url_for("not_admin"))


@app.route("/past_reservations_info/<reservation_id>", methods=["GET"])
def past_reservations_info(reservation_id):
    if ("username" in session and session["role"] == "admin") or (
        "username" in session
    ):
        conn = pymysql.connect(**config)
        with conn.cursor() as cursor:
            book_sql = "SELECT * FROM reservation WHERE reservation_id = %s;"
            cursor.execute(book_sql, (reservation_id,))
            reservation = cursor.fetchone()
            user_id = reservation["user_id"]

        with conn.cursor() as cursor:
            user_sql = "select * from user where id = %s"
            cursor.execute(user_sql, (user_id,))
            user = cursor.fetchone()

        with conn.cursor() as cursor:
            user_sql = "select * from user_school where id = %s"
            cursor.execute(user_sql, (user_id,))
            user_school = cursor.fetchone()

        with conn.cursor() as cursor:
            sql = "SELECT r.role FROM user u INNER JOIN role r ON u.id = r.user_id WHERE u.id = %s"
            cursor.execute(sql, (user_id,))
            result_r = cursor.fetchone()

            role_u = None
            if result_r:
                role_temp = result_r["role"]
                if role_temp == 1:
                    role_u = "student"
                elif role_temp == 2:
                    role_u = "professor"
                elif role_temp == 3:
                    role_u = "admin"
                elif role_temp == 4:
                    role_u = "master admin"

        conn.close()

        return render_template(
            "past_reservations_info.html",
            reservation=reservation,
            user=user,
            user_school=user_school,
            role_u=role_u,
        )
    else:
        return redirect(url_for("not_admin"))


@app.route("/delayed_users")
def delayed_users():
    if "username" in session and session["role"] == "admin":
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            sql = "SELECT r.reservation_id, u.first_name, u.last_name, DATEDIFF(CURDATE(), r.expected_date) AS delayed_days FROM reservation r JOIN user u ON r.user_id = u.id WHERE r.return_date IS NULL AND CURDATE() > r.expected_date;"
            cursor.execute(sql)
            data = cursor.fetchall()

        conn.close()

        return render_template("delayed_users.html", data=data)
    else:
        return redirect(url_for("not_admin"))


@app.route("/update_user", methods=["GET", "POST"])
def update_user():
    if "username" in session and session["role"] == "admin":
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            search_query = request.args.get("search")
            if search_query:
                sql = "SELECT * FROM user WHERE id = %s"
                cursor.execute(sql, (search_query,))
            else:
                sql = "SELECT * FROM user"
                cursor.execute(sql)
            users = cursor.fetchall()

        return render_template("update_user.html", users=users)
    else:
        return redirect(url_for("not_admin"))


@app.route("/update_user_form/<int:user_id>", methods=["GET", "POST"])
def update_user_form(user_id):
    if "username" in session and session["role"] == "admin":
        conn = pymysql.connect(**config)

        if request.method == "POST":
            username = request.form.get("username")
            last_name = request.form.get("last_name")
            first_name = request.form.get("first_name")
            age = request.form.get("age")

            if username is None or username.strip() == "":
                return redirect(url_for("update_user_form", user_id=user_id))

            with conn.cursor() as cursor:
                sql = "UPDATE user SET username=%s, last_name=%s, first_name=%s, age=%s WHERE id=%s"
                cursor.execute(sql, (username, last_name, first_name, age, user_id))
            conn.commit()

            flash("User details updated successfully!", "success")
            return redirect(url_for("update_user_form", user_id=user_id))

        with conn.cursor() as cursor:
            sql = "SELECT * FROM user WHERE id=%s"
            cursor.execute(sql, (user_id,))
            user = cursor.fetchone()

        return render_template("update_user_form.html", user=user)
    else:
        return redirect(url_for("not_admin"))


@app.route("/account")
def account():
    if "username" in session:
        conn = pymysql.connect(**config)
        username = session["username"]
        with conn.cursor() as cursor:
            sql = "SELECT u.*, r.role, us.school_id from user u inner join role r on u.id=r.user_id inner join user_school us on u.id=us.user_id where u.username=%s"
            cursor.execute(sql, (username,))
            user = cursor.fetchone()

        with conn.cursor() as cursor:
            sql = "SELECT r.role FROM user u INNER JOIN role r ON u.id = r.user_id WHERE u.username = %s"
            cursor.execute(sql, (username,))
            result_r = cursor.fetchone()

            role_u = None
            if result_r:
                role_temp = result_r["role"]
                if role_temp == 1:
                    role_u = "student"
                elif role_temp == 2:
                    role_u = "professor"
                elif role_temp == 3:
                    role_u = "admin"
                elif role_temp == 4:
                    role_u = "master admin"
        conn.close()

        return render_template("account.html", user=user, role_u=role_u)
    else:
        return redirect(url_for("login"))


@app.route("/account_update")
def account_update():
    if "username" in session:
        conn = pymysql.connect(**config)
        username = session["username"]
        with conn.cursor() as cursor:
            sql = "SELECT * FROM user WHERE username = %s"
            cursor.execute(sql, (username,))
            user = cursor.fetchone()
        conn.close()

        role = session["role"]
        print(role)
        if user:
            if role == "student":
                return redirect(url_for("not_admin"))
            else:
                return render_template("account_update.html", user=user)
        else:
            flash("User not found.", "error")
            return redirect(url_for("account"))
    else:
        return redirect(url_for("login"))


@app.route("/account_update_success", methods=["GET", "POST"])
def account_update_success():
    if "username" in session:
        username = session["username"]
        last_name = request.form.get("last_name")
        first_name = request.form.get("first_name")
        age = request.form.get("age")

        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            sql = "UPDATE user SET last_name = %s, first_name = %s, age = %s WHERE username = %s"
            cursor.execute(sql, (last_name, first_name, age, username))
            conn.commit()

        conn.close()

        flash("Account updated successfully.", "success")
        return redirect(url_for("account"))
    else:
        return redirect(url_for("login"))


@app.route("/password_update")
def password_update():
    if "username" in session:
        return render_template("password_update.html")
    else:
        return redirect(url_for("login"))


@app.route("/password_update_success", methods=["POST"])
def password_update_success():
    if "username" in session:
        username = session["username"]
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            sql = "SELECT password from user where username=%s"
            cursor.execute(sql, (username))
            password = cursor.fetchone()

        if current_password == password["password"]:
            if new_password == confirm_password:
                with conn.cursor() as cursor:
                    sql = "UPDATE user SET password = %s where username = %s"
                    cursor.execute(
                        sql,
                        (
                            new_password,
                            username,
                        ),
                    )
                    conn.commit()

                conn.close()

                flash("Password updated successfully.", "success")
                return redirect(url_for("account"))
            else:
                flash("Error: Passwords dont match.", "error")
                return redirect(url_for("password_update"))
        else:
            flash("Error: Current password is not correct.", "error")
            return redirect(url_for("password_update"))

    else:
        return redirect(url_for("login"))


@app.route("/user_reservations")
def user_reservations():
    if "username" in session:
        username = session["username"]

        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            sql = "SELECT r.*, b.titleBK FROM reservation r inner join book b on r.book_id = b.ISBN WHERE r.user_id = (SELECT id FROM user WHERE username = %s) order by r.return_date;"
            cursor.execute(sql, (username,))
            reservations = cursor.fetchall()

        conn.close()

        return render_template("user_reservations.html", reservations=reservations)
    else:
        return redirect(url_for("login"))


@app.route("/pending_reservations_info_user/<reservation_id>", methods=["GET", "POST"])
def pending_reservations_info_user(reservation_id):
    if "username" in session:
        if request.method == "POST":
            conn = pymysql.connect(**config)

            try:
                with conn.cursor() as cursor:
                    reservation_sql = (
                        "delete from reservation where reservation_id = %s"
                    )
                    cursor.execute(reservation_sql, (reservation_id,))

                    conn.commit()
            finally:
                conn.close()

            flash("Reservation deleted.", "success")
            return redirect(url_for("user_reservations"))

        else:
            conn = pymysql.connect(**config)
            with conn.cursor() as cursor:
                book_sql = "SELECT * FROM reservation WHERE reservation_id = %s;"
                cursor.execute(book_sql, (reservation_id,))
                reservation = cursor.fetchone()
                user_id = reservation["user_id"]

            with conn.cursor() as cursor:
                user_sql = "select * from user where id = %s"
                cursor.execute(user_sql, (user_id,))
                user = cursor.fetchone()

            with conn.cursor() as cursor:
                user_sql = "select * from user_school where id = %s"
                cursor.execute(user_sql, (user_id,))
                user_school = cursor.fetchone()

            with conn.cursor() as cursor:
                sql = "SELECT r.role FROM user u INNER JOIN role r ON u.id = r.user_id WHERE u.id = %s"
                cursor.execute(sql, (user_id,))
                result_r = cursor.fetchone()

                role_u = None
                if result_r:
                    role_temp = result_r["role"]
                    if role_temp == 1:
                        role_u = "student"
                    elif role_temp == 2:
                        role_u = "professor"
                    elif role_temp == 3:
                        role_u = "admin"
                    elif role_temp == 4:
                        role_u = "master admin"

            conn.close()

            return render_template(
                "pending_reservations_info_user.html",
                reservation=reservation,
                user=user,
                user_school=user_school,
                role_u=role_u,
            )
    else:
        return redirect(url_for("login"))


@app.route("/approved_reservations_info_user/<reservation_id>", methods=["GET", "POST"])
def approved_reservations_info_user(reservation_id):
    if "username" in session:
        if request.method == "POST":
            conn = pymysql.connect(**config)

            try:
                with conn.cursor() as cursor:
                    reservation_sql = (
                        "delete from reservation where reservation_id = %s"
                    )
                    cursor.execute(reservation_sql, (reservation_id,))

                    conn.commit()
            finally:
                conn.close()

            flash("Reservation delete.", "success")
            return redirect(url_for("user_reservations"))

        else:
            conn = pymysql.connect(**config)
            with conn.cursor() as cursor:
                book_sql = "SELECT * FROM reservation WHERE reservation_id = %s;"
                cursor.execute(book_sql, (reservation_id,))
                reservation = cursor.fetchone()
                user_id = reservation["user_id"]

            with conn.cursor() as cursor:
                user_sql = "select * from user where id = %s"
                cursor.execute(user_sql, (user_id,))
                user = cursor.fetchone()

            with conn.cursor() as cursor:
                user_sql = "select * from user_school where id = %s"
                cursor.execute(user_sql, (user_id,))
                user_school = cursor.fetchone()

            with conn.cursor() as cursor:
                sql = "SELECT r.role FROM user u INNER JOIN role r ON u.id = r.user_id WHERE u.id = %s"
                cursor.execute(sql, (user_id,))
                result_r = cursor.fetchone()

                role_u = None
                if result_r:
                    role_temp = result_r["role"]
                    if role_temp == 1:
                        role_u = "student"
                    elif role_temp == 2:
                        role_u = "professor"
                    elif role_temp == 3:
                        role_u = "admin"
                    elif role_temp == 4:
                        role_u = "master admin"

            conn.close()

            return render_template(
                "approved_reservations_info_user.html",
                reservation=reservation,
                user=user,
                user_school=user_school,
                role_u=role_u,
            )
    else:
        return redirect(url_for("login"))


@app.route("/open_reservations_info_user/<reservation_id>", methods=["GET"])
def open_reservations_info_user(reservation_id):
    if "username" in session:
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            book_sql = "SELECT * FROM reservation WHERE reservation_id = %s;"
            cursor.execute(book_sql, (reservation_id,))
            reservation = cursor.fetchone()
            user_id = reservation["user_id"]

        with conn.cursor() as cursor:
            user_sql = "select * from user where id = %s"
            cursor.execute(user_sql, (user_id,))
            user = cursor.fetchone()

        with conn.cursor() as cursor:
            user_sql = "select * from user_school where id = %s"
            cursor.execute(user_sql, (user_id,))
            user_school = cursor.fetchone()

        with conn.cursor() as cursor:
            sql = "SELECT r.role FROM user u INNER JOIN role r ON u.id = r.user_id WHERE u.id = %s"
            cursor.execute(sql, (user_id,))
            result_r = cursor.fetchone()

            role_u = None
            if result_r:
                role_temp = result_r["role"]
                if role_temp == 1:
                    role_u = "student"
                elif role_temp == 2:
                    role_u = "professor"
                elif role_temp == 3:
                    role_u = "admin"
                elif role_temp == 4:
                    role_u = "master admin"

        conn.close()

        return render_template(
            "open_reservations_info_user.html",
            reservation=reservation,
            user=user,
            user_school=user_school,
            role_u=role_u,
        )
    else:
        return redirect(url_for("login"))


@app.route("/past_reservations_info_user/<reservation_id>", methods=["GET"])
def past_reservations_info_user(reservation_id):
    if "username" in session:
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            book_sql = "SELECT * FROM reservation WHERE reservation_id = %s;"
            cursor.execute(book_sql, (reservation_id,))
            reservation = cursor.fetchone()
            user_id = reservation["user_id"]

        with conn.cursor() as cursor:
            user_sql = "select * from user where id = %s"
            cursor.execute(user_sql, (user_id,))
            user = cursor.fetchone()

        with conn.cursor() as cursor:
            user_sql = "select * from user_school where id = %s"
            cursor.execute(user_sql, (user_id,))
            user_school = cursor.fetchone()

        with conn.cursor() as cursor:
            sql = "SELECT r.role FROM user u INNER JOIN role r ON u.id = r.user_id WHERE u.id = %s"
            cursor.execute(sql, (user_id,))
            result_r = cursor.fetchone()

            role_u = None
            if result_r:
                role_temp = result_r["role"]
                if role_temp == 1:
                    role_u = "student"
                elif role_temp == 2:
                    role_u = "professor"
                elif role_temp == 3:
                    role_u = "admin"
                elif role_temp == 4:
                    role_u = "master admin"

        conn.close()

        return render_template(
            "past_reservations_info_user.html",
            reservation=reservation,
            user=user,
            user_school=user_school,
            role_u=role_u,
        )
    else:
        return redirect(url_for("login"))


@app.route("/school_view")
def school_view():
    if "username" in session and session["role"] == "admin":
        conn = pymysql.connect(**config)
        u_id = session["u_id"]
        with conn.cursor() as cursor:
            sql = "SELECT * FROM user_school WHERE user_id = %s"
            cursor.execute(sql, (u_id))
            result = cursor.fetchone()
            school_id = result["school_id"]
        with conn.cursor() as cursor:
            sql = "SELECT * FROM school WHERE id = %s"
            cursor.execute(sql, (school_id,))
            school = cursor.fetchone()

        conn.close()

        return render_template("school_view.html", school=school)
    else:
        return redirect(url_for("login"))


@app.route("/school_update/<school_id>", methods=["GET", "POST"])
def school_update(school_id):
    if "username" in session and session["role"] == "admin":
        conn = pymysql.connect(**config)

        if request.method == "POST":
            name = request.form.get("name")
            city = request.form.get("city")
            phone = request.form.get("phone")
            email = request.form.get("email")
            director_name = request.form.get("director_name")
            admin_name = request.form.get("admin_name")

            with conn.cursor() as cursor:
                sql = "UPDATE school SET name = %s, city = %s, phone = %s, email = %s, director_name = %s, admin_name = %s WHERE id = %s"
                cursor.execute(
                    sql,
                    (name, city, phone, email, director_name, admin_name, school_id),
                )
            conn.commit()

            flash("School details updated successfully!", "success")
            return redirect(url_for("school_view"))

        with conn.cursor() as cursor:
            sql = "SELECT * FROM school WHERE id = %s"
            cursor.execute(sql, (school_id,))
            school = cursor.fetchone()

        return render_template("school_update.html", school=school)

    return redirect(url_for("not_admin"))


from flask import request


@app.route("/total_reservations", methods=["GET", "POST"])
def total_reservations():
    if "username" in session and session["role"] == "master admin":
        if request.method == "POST":
            res_year = request.form.get("res_year")
            res_month = request.form.get("res_month")
        else:
            res_year = None
            res_month = None

        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            query = """SELECT YEAR(reservation_date) AS year, MONTH(reservation_date) AS month,
       school_id,
       COUNT(*) AS count
FROM reservation
WHERE YEAR(reservation_date) = %s AND MONTH(reservation_date) = %s
GROUP BY YEAR(reservation_date), MONTH(reservation_date), school_id
ORDER BY YEAR(reservation_date), MONTH(reservation_date), school_id;"""
            cursor.execute(query, (res_year, res_month))
            reservations = cursor.fetchall()

        conn.close()

        return render_template("total_reservations.html", reservations=reservations)
    else:
        return redirect(url_for("not_admin"))


@app.route("/top_users", methods=["GET", "POST"])
def top_users():
    if "username" in session and session["role"] == "master admin":
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            query = """SELECT u.first_name, u.last_name, r.user_id, COUNT(*) AS count
                       FROM user u
                       INNER JOIN reservation r ON u.id = r.user_id
                       INNER JOIN role l ON u.id = l.user_id
                       WHERE l.role = 2 and u.age < 40
                       GROUP BY r.user_id
                       ORDER BY count DESC
                       LIMIT 5;"""
            cursor.execute(query)
            users = cursor.fetchall()

        conn.close()

        return render_template("top_users.html", users=users)
    else:
        return redirect(url_for("not_admin"))


@app.route("/category_author", methods=["GET", "POST"])
def category_author():
    if "username" in session and session["role"] == "master admin":
        if request.method == "POST":
            category = request.form.get("category")
        else:
            category = None

        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            # Retrieve categories
            category_query = "SELECT id, category FROM category"
            cursor.execute(category_query)
            categories = cursor.fetchall()

            if category:
                query = """SELECT c.category, a.name, u.first_name, u.last_name
                           FROM user u
                           INNER JOIN role l ON u.id = l.user_id
                           INNER JOIN reservation r ON u.id = r.user_id
                           INNER JOIN book_author ba ON r.book_id = ba.book_isbn
                           INNER JOIN author a ON a.id = ba.author_id
                           INNER JOIN book_category bc ON bc.book_id = r.book_id
                           INNER JOIN category c ON bc.category_id = c.id
                           WHERE l.role = 2
                           AND c.id = %s
                           AND r.reservation_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR);"""
                cursor.execute(query, (category,))
                reservations = cursor.fetchall()
            else:
                reservations = []

        conn.close()

        return render_template(
            "category_author.html", reservations=reservations, categories=categories
        )
    else:
        return redirect(url_for("not_admin"))


@app.route("/professor_most", methods=["GET", "POST"])
def professor_most():
    if "username" in session and session["role"] == "master admin":
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            query = """SELECT u.first_name, u.last_name, r.user_id, COUNT(*) AS count
                       FROM user u
                       INNER JOIN reservation r ON u.id = r.user_id
                       INNER JOIN role l ON u.id = l.user_id
                       WHERE l.role = 2 and u.age < 40
                       GROUP BY r.user_id
                       ORDER BY count DESC
                       LIMIT 5;"""
            cursor.execute(query)
            users = cursor.fetchall()

        conn.close()

        return render_template("professor_most.html", users=users)
    else:
        return redirect(url_for("not_admin"))


@app.route("/no_res")
def no_res():
    if "username" in session and session["role"] == "master admin":
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            query = """SELECT a.name
                       FROM author a
                       WHERE NOT EXISTS (
                         SELECT 1
                         FROM book_author ba
                         INNER JOIN reservation r ON ba.book_isbn = r.book_id
                         WHERE ba.author_id = a.id
                       );"""
            cursor.execute(query)
            authors = cursor.fetchall()

        conn.close()

        return render_template("no_res.html", authors=authors)
    else:
        return redirect(url_for("not_admin"))


@app.route("/same")
def same():
    if "username" in session and session["role"] == "master admin":
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            query = """
            SELECT s1.admin_name
            FROM school s1
            INNER JOIN (
              SELECT r.school_id, COUNT(*) AS reservation_count
              FROM reservation r
              WHERE r.reservation_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
              GROUP BY r.school_id
              HAVING COUNT(*) > 20
            ) s2 ON s1.id = s2.school_id
            INNER JOIN (
              SELECT COUNT(*) AS reservation_count
              FROM reservation
              WHERE reservation_date >= DATE_SUB(CURDATE(), INTERVAL 1 YEAR)
              GROUP BY school_id
              HAVING COUNT(*) > 20
            ) s3 ON s2.reservation_count = s3.reservation_count
            GROUP BY s1.admin_name
            HAVING COUNT(*) > 1;
            """
            cursor.execute(query)
            admins = cursor.fetchall()

        conn.close()

        return render_template("same.html", admins=admins)
    else:
        return redirect(url_for("not_admin"))


@app.route("/popcat")
def popcat():
    if "username" in session and session["role"] == "master admin":
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            query = """SELECT bc1.category_id AS category_1_id, c1.category AS category_1,
                              bc2.category_id AS category_2_id, c2.category AS category_2,
                              COUNT(r.book_id) AS reservation_count
                       FROM book_category bc1
                       INNER JOIN book_category bc2 ON bc1.book_id = bc2.book_id AND bc1.category_id < bc2.category_id
                       INNER JOIN reservation r ON bc1.book_id = r.book_id
                       INNER JOIN category c1 ON bc1.category_id = c1.id
                       INNER JOIN category c2 ON bc2.category_id = c2.id
                       GROUP BY bc1.category_id, c1.category, bc2.category_id, c2.category
                       ORDER BY reservation_count DESC
                       LIMIT 3;"""
            cursor.execute(query)
            categories = cursor.fetchall()

        conn.close()

        return render_template("popcat.html", categories=categories)
    else:
        return redirect(url_for("not_admin"))


@app.route("/less")
def less():
    conn = pymysql.connect(**config)

    with conn.cursor() as cursor:
        query = """SELECT author_id, COUNT(*) AS display_count
        FROM book_author
        GROUP BY author_id
        HAVING COUNT(*) < (
            SELECT COUNT(*) - 4 AS top_count
            FROM book_author
            GROUP BY author_id
            ORDER BY top_count DESC
            LIMIT 1
        )
        ORDER BY display_count DESC;"""
        cursor.execute(query)
        results = cursor.fetchall()

    conn.close()

    return render_template("less.html", results=results)


@app.route("/user_rating", methods=["GET", "POST"])
def user_rating():
    if "username" in session and session["role"] == "admin":
        conn = pymysql.connect(**config)

        with conn.cursor() as cursor:
            # Fetch categories
            cursor.execute("SELECT id, category FROM category")
            categories = cursor.fetchall()

        conn.close()

        if request.method == "POST":
            user_id = request.form.get("user_id")
            category_id = request.form.get("category_id")

            conn = pymysql.connect(**config)

            with conn.cursor() as cursor:
                query = """SELECT u.first_name, u.last_name, c.category, AVG(r.rating)
                           FROM user u
                           LEFT JOIN ratings r ON u.id = r.user_id
                           JOIN book_category bc ON r.book_id = bc.book_id
                           JOIN category c ON bc.category_id = c.id
                           WHERE u.id = %s
                           AND c.id = %s
                           GROUP BY u.first_name, u.last_name, c.category
                           ORDER BY c.category;"""
                cursor.execute(query, (user_id, category_id))
                ratings = cursor.fetchall()

            conn.close()

            return render_template(
                "user_rating.html", ratings=ratings, categories=categories
            )
        else:
            return render_template("user_rating.html", categories=categories)
    else:
        return redirect(url_for("not_admin"))


@app.route("/book_admin", methods=["GET", "POST"])
def book_admin():
    if "username" in session:
        conn = pymysql.connect(**config)
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM category")
            categories = cursor.fetchall()

        if request.method == "POST":
            search_query = request.form.get("search_query")
            category_id = request.form.get("category_id")
            author_search = request.form.get("author_search")

            if category_id == "0":
                category_id = None

            params = []

            sql = """
                SELECT b.titleBK, GROUP_CONCAT(DISTINCT a.name) AS author_names, GROUP_CONCAT(DISTINCT c.category) AS categories, b.ISBN, bs.inventory
                FROM book b
                LEFT JOIN book_author ba ON b.ISBN = ba.book_isbn
                LEFT JOIN author a ON ba.author_id = a.id
                LEFT JOIN book_category bc ON b.ISBN = bc.book_id
                LEFT JOIN category c ON bc.category_id = c.id
                LEFT JOIN book_school bs ON b.ISBN=bs.book_id
                WHERE 1=1
            """

            if search_query:
                sql += " AND b.titleBK LIKE %s"
                params.append(f"%{search_query}%")

            if category_id:
                sql += " AND bc.category_id = %s"
                params.append(category_id)

            if author_search:
                sql += " AND a.name LIKE %s"
                params.append(f"%{author_search}%")

            sql += " GROUP BY b.titleBK"

            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                data = cursor.fetchall()
        else:
            sql = """
                SELECT b.titleBK, GROUP_CONCAT(DISTINCT a.name) AS author_names, GROUP_CONCAT(DISTINCT c.category) AS categories, b.ISBN, bs.inventory
                FROM book b
                LEFT JOIN book_author ba ON b.ISBN = ba.book_isbn
                LEFT JOIN author a ON ba.author_id = a.id
                LEFT JOIN book_category bc ON b.ISBN = bc.book_id
                LEFT JOIN category c ON bc.category_id = c.id
                LEFT JOIN book_school bs ON b.ISBN=bs.book_id
                GROUP BY b.titleBK
            """

            with conn.cursor() as cursor:
                cursor.execute(sql)
                data = cursor.fetchall()

        conn.close()

        return render_template("book_admin.html", data=data, categories=categories)
    else:
        return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
