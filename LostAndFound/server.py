from flask import Flask, request, redirect, render_template, session
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
from flask import send_file
import mysql.connector

app = Flask(__name__)

# configurations
from config import Config
app.config.from_object(Config)
app.secret_key = app.config['SECRET_KEY']


# error handling
# @app.errorhandler(404)
# def not_found_error(error):
#     return render_template('404.html'), 404
#
#
# @app.errorhandler(500)
# def server_internal_error(error):
#     return render_template('500.html'), 500


def get_listings():
    cnx = mysql.connector.connect(user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], database=app.config['DB_NAME'])
    cursor = cnx.cursor()

    query = "SELECT * FROM listings WHERE is_live=1"
    cursor.execute(query)
    listings = cursor.fetchall()

    cursor.close()
    cnx.close()
    return listings


@app.route('/')
def index():
    if 'username' in session:
        return render_template("index.html", listings=get_listings(), login=True)
    else:
        return render_template("index.html", listings=get_listings(), login=False)


@app.route('/my_listings')
def my_listings():
    if 'username' in session:
        cnx = mysql.connector.connect(user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], database=app.config['DB_NAME'])
        cursor = cnx.cursor()

        query = "SELECT * FROM listings WHERE is_live=1 AND posterid='" + session['username'] + "'"
        cursor.execute(query)
        listings = cursor.fetchall()

        cursor.close()
        cnx.close()
        if listings:
            return render_template("my_listings.html", listings=listings)
        else:
            return render_template("my_listings.html", messages="No listings here :)")
    else:
        return render_template("my_listings.html", messages="Login to see your listings")


@app.route('/archived')
def view_archived():
    if 'username' in session:
        cnx = mysql.connector.connect(user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], database=app.config['DB_NAME'])
        cursor = cnx.cursor()

        query = "SELECT * FROM listings WHERE is_live=0 AND posterid='" + session['username'] + "'"
        cursor.execute(query)
        listings = cursor.fetchall()

        cursor.close()
        cnx.close()
        if listings:
            return render_template("archived.html", listings=listings)
        else:
            return render_template("archived.html", messages="No archived listings here :)")
    else:
        return render_template("archived.html", messages="Login to see your archived listings")


@app.route('/edit/<postid>', methods=['get'])
def edit(postid):
    cnx = mysql.connector.connect(user=app.config['DB_USER'], password=app.config['DB_PASSWORD'],
                                  database=app.config['DB_NAME'])
    cursor = cnx.cursor()

    query = "SELECT * FROM listings WHERE id=%s"
    data = (postid,)
    cursor.execute(query, data)
    listing = cursor.fetchall()[0]

    cursor.close()
    cnx.close()

    return render_template("edit_my_listing.html", postid=postid, listing=listing)


@app.route('/edit-listing/<postid>', methods=['post'])
def edit_listing(postid):
    cnx = mysql.connector.connect(user=app.config['DB_USER'], password=app.config['DB_PASSWORD'],
                                  database=app.config['DB_NAME'])
    cursor = cnx.cursor()

    query = "UPDATE listings SET item_name=%s, item_location=%s, additional_info=%s, image=%s WHERE id=%s"

    f = request.files['file']
    new_image = f.read()

    data = (request.form['item_name'], request.form['item_location'], request.form['additional_info'], new_image, postid)
    cursor.execute(query, data)
    cnx.commit()

    cursor.close()
    cnx.close()
    return redirect('/my_listings')


@app.route('/archive-listing/<postid>', methods=['get'])
def archive_listing(postid):
    cnx = mysql.connector.connect(user=app.config['DB_USER'], password=app.config['DB_PASSWORD'],
                                  database=app.config['DB_NAME'])
    cursor = cnx.cursor()

    query = "UPDATE listings SET is_live=%s WHERE id=%s"
    data = (0, postid)
    cursor.execute(query, data)
    cnx.commit()

    print("no longer live")

    cursor.close()
    cnx.close()
    return redirect('/my_listings')


@app.route('/relist-listing/<postid>', methods=['get'])
def relist_listing(postid):
    cnx = mysql.connector.connect(user=app.config['DB_USER'], password=app.config['DB_PASSWORD'],
                                  database=app.config['DB_NAME'])
    cursor = cnx.cursor()

    query = "UPDATE listings SET is_live=1 WHERE id=%s"
    data = (postid,)
    cursor.execute(query, data)
    cnx.commit()

    cursor.close()
    cnx.close()
    return redirect('/archived')


@app.route('/register_user_page')
def register_user_page():
    return render_template("register_user.html")


@app.route('/register_user', methods=['post'])
def register_user():
    cnx = mysql.connector.connect(user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], database=app.config['DB_NAME'])
    cursor = cnx.cursor()
    insert_stmp = 'INSERT INTO users VALUES (%s, %s, %s, %s, %s)'

    hash = generate_password_hash(request.form['password'])
    data = (None, request.form['username'], request.form['email'], hash, request.form['fullname'])
    cursor.execute(insert_stmp, data)
    cnx.commit()
    cursor.close()
    cnx.close()
    return redirect("/login_page")


@app.route('/login_page')
def login_page():
    return render_template("login.html")


@app.route('/login', methods=['post'])
def login():

    if 'username' in session:
        return render_template('index.html', listings=get_listings(), login=True)
    else:
        cnx = mysql.connector.connect(user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], database=app.config['DB_NAME'])
        cursor = cnx.cursor()

        cursor.execute("SELECT * FROM users WHERE email='" + request.form['email'] + "'")
        users = cursor.fetchall()

        if users:
            user = users[0]

            username = user[1]
            hash = user[3]
            if check_password_hash(hash, request.form['password']):
                session['username'] = username
                return redirect('/')
            else:
                # check for password

                return render_template('login.html', messages='Incorrect email or password')
        else:
            return render_template('login.html', messages='Incorrect email or password')


@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('username', None)
    return redirect('/')


@app.route('/create_listing_page')
def create_listing_page():
    return render_template("create_listing.html", login=('username' in session))


@app.route('/create_listing', methods=['post'])
def create_listing():
    cnx = mysql.connector.connect(user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], database=app.config['DB_NAME'])
    cursor = cnx.cursor()
    insert_stmt = "INSERT INTO listings VALUES (%s, %s, %s, %s, %s, %s, %s)"

    print(request.form['item_name'])
    print(request.form['item_location'])
    print(request.form['additional_info'])

    f = request.files['file']
    img_data = f.read()

    data = (None, request.form['item_name'], request.form['item_location'], session['username'], request.form['additional_info'], img_data, 1)
    cursor.execute(insert_stmt, data)
    cnx.commit()
    cursor.close()
    cnx.close()

    return redirect("/")


@app.route('/users/<postid>', methods=['get'])
def get_image(postid):
    cnx = mysql.connector.connect(user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], database=app.config['DB_NAME'])
    cursor = cnx.cursor()

    query = "select * from listings where id=%s"
    data = (postid,)
    cursor.execute(query, data)
    listings = cursor.fetchall()

    cursor.close()
    cnx.close()

    # send file
    bytes_io = BytesIO(listings[0][5])

    return send_file(bytes_io, mimetype='image/jpeg')


@app.route('/contact/<posterid>/<postid>', methods=['get'])
def get_listing(posterid, postid):
    cnx = mysql.connector.connect(user=app.config['DB_USER'], password=app.config['DB_PASSWORD'], database=app.config['DB_NAME'])
    cursor = cnx.cursor()

    query = "select * from listings where id=%s"
    data = (postid,)
    cursor.execute(query, data)
    listings = cursor.fetchall()[0]

    query = "select (email) from users where username=%s"
    data = (posterid,)
    cursor.execute(query, data)
    email = cursor.fetchall()[0][0]
    print(email)

    cursor.close()
    cnx.close()
    return render_template("listing.html", listing=listings, poster=email)


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')  # use 0.0.0.0, allow access this app from my cell phone
