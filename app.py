from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql

app = Flask(__name__)

# Set the secret key for the app
app.secret_key = 'your_secret_key_here'


@app.route('/')
def index():
    # Check if the user is logged in
    if 'username' in session:
        # Connect to the database
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='2403',
            db='vas',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        # Execute the query to retrieve data from the database
        with conn.cursor() as cursor:
            sql = 'SELECT * FROM user'
            cursor.execute(sql)
            data = cursor.fetchall()

        # Close the database connection
        conn.close()

        # Render the HTML template and pass the data to it
        return render_template('index.html', data=data)
    else:
        return redirect(url_for('login'))


@app.route('/student')
def about():
    # Check if the user is logged in
    if 'username' in session:
        # Connect to the database
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='2403',
            db='vas',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        # Execute the query to retrieve data from the database
        with conn.cursor() as cursor:
            sql = 'SELECT * FROM student'
            cursor.execute(sql)
            data = cursor.fetchall()

        # Close the database connection
        conn.close()

        return render_template('student.html', data=data)
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if the user is already logged in
    if 'username' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Connect to the database
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='2403',
            db='vas',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        # Get username and password from form submission
        username = request.form['username']
        password = request.form['password']

        # Query database for user
        with conn.cursor() as cursor:
            query = "SELECT * FROM user WHERE username = %s AND password = %s"
            cursor.execute(query, (username, password))
            result = cursor.fetchone()

        # Close the database connection
        conn.close()

        if result:
            # If user exists, store username in session and redirect to home page
            session['username'] = username
            return redirect(url_for('index'))
        else:
            # If user does not exist, redirect back to login page with error message
            return render_template('login.html', error='Invalid username or password')
    else:
        return render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    flash('You were logged out')
    return redirect(url_for('login'))


@app.route('/rent')
def rent():
    return render_template('rent.html')


@app.route('/rate', methods=['GET','POST'])
def rate():
    if 'username' in session:
        username = session['username']
        book_id = request.form.get('book_id')
        rating = request.form.get('rating')

        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='2403',
            db='vas',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:
            # Retrieve the user_id based on the username
            sql = "SELECT id FROM user WHERE username = %s"
            cursor.execute(sql, (username,))
            result = cursor.fetchone()
            user_id = result['id']

            # Insert the rating into the ratings table
            sql = "INSERT INTO ratings (user_id, book_id, rating) VALUES (%s, %s, %s)"
            cursor.execute(sql, (user_id, book_id, rating))

        conn.commit()
        conn.close()

        return redirect(url_for('rating'))
    else:
        return redirect(url_for('login'))



@app.route('/school')
def school():
    if 'username' in session:

        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='2403',
            db='vas',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:
            sql = 'SELECT * FROM book_inventory_view;'
            cursor.execute(sql)
            data = cursor.fetchall()

        conn.close()

        return render_template('school.html', data=data)
    else: return redirect(url_for('login'))

@app.route('/delayed')
def delayed():
    if 'username' in session:

        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='2403',
            db='vas',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:
            sql = 'SELECT * FROM borrow'
            cursor.execute(sql)
            data = cursor.fetchall()

        conn.close()

        return render_template('delayed.html', data=data)
    else: return redirect(url_for('login'))

@app.route('/users')
def users():
    if 'username' in session:

        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='2403',
            db='vas',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:
            sql = 'CALL roles()'
            cursor.execute(sql)
            data = cursor.fetchall()

        conn.close()

        return render_template('users.html', data=data)
    else: return redirect(url_for('login'))

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        # Retrieve the form data
        username = request.form['username']
        password = request.form['password']
        num_books = int(request.form['num_books'])
        active = int(request.form['active'])
        last_name = request.form['last_name']
        first_name = request.form['first_name']
        age = int(request.form['age'])

        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='2403',
            db='vas',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        try:
            # Create a cursor object to interact with the database
            with conn.cursor() as cursor:
                # Prepare the SQL statement
                sql = "INSERT INTO user (username, password, num_books, active, last_name, first_name, age) " \
                      "VALUES (%s, %s, %s, %s, %s, %s, %s)"
                print(username, first_name, last_name, password, num_books, active, age)

                # Execute the SQL statement
                cursor.execute(sql, (username, password, num_books, active, last_name, first_name, age))

            # Commit the transaction
            conn.commit()

            # Redirect to a success page or any other desired page
            return render_template('index.html')

        except Exception as e:
            # Handle the error, rollback the transaction, or display an error message
            print(f"Error: {e}")
            conn.rollback()
            # Redirect to an error page or display an error message to the user
            return render_template('school.html')

        finally:
            # Close the database connection
            conn.close()

        # Redirect to a success page or any other desired page
        

    # Render the add_user.html template for GET requests
    return render_template('add_user.html')

@app.route('/rating')
def rating():
    if 'username' in session:

        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='2403',
            db='vas',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:
            sql = 'CALL avgrating();'
            cursor.execute(sql)
            data = cursor.fetchall()

        conn.close()

        return render_template('rating.html', data=data)
    else: return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)