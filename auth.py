from flask import Blueprint, request, render_template, flash, redirect, url_for, session
from argon2 import PasswordHasher
import pymysql
from werkzeug.utils import secure_filename
import os
import re

# Initialize password hasher and Flask blueprint
ph = PasswordHasher()
authenticated = Blueprint('authenticated', __name__)

# Set up upload folder and allowed file types
UPLOAD_FOLDER = os.path.join('static','uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_valid_contact(contact):
    pattern = re.compile(r'^\+?\d{11,12}$')
    return pattern.match(contact) is not None

# Function to get a database connection
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='apartment',
        cursorclass=pymysql.cursors.DictCursor
    )

@authenticated.route('/Sign-Up', methods=['POST', 'GET'])
def usersignup():
    if request.method == 'POST':
        # Collect form data
        name = request.form.get('signame')
        address = request.form.get('sigadd')
        platenum = request.form.get('platenum')
        Roomnumber = request.form.get('Roomno')
        contact=request.form.get('connum')
        email = request.form.get('sigmail')
        password = request.form.get('passwordField')
        retypepass = request.form.get('RepeatpasswordField')
        image_upload = request.files.get('profileImage')
        terms=request.form.get('terms')

        # Database connection
        try:
            authen = get_db_connection()
            signup_area = authen.cursor()

            # Check if email or room already exists
            signup_area.execute('SELECT loginid FROM loginapartment WHERE email=%s', (email,))
            existed_email = signup_area.fetchone()

            signup_area.execute('SELECT userid FROM apartmentsingup WHERE roomNumber=%s', (Roomnumber,))
            existed_Room = signup_area.fetchone()

            if existed_email:
                flash('This email already exists', 'danger')
                return render_template('signup.html')

            if existed_Room:
                flash('This Room is already occupied', 'danger')
                return render_template('signup.html')

            if not is_valid_contact(contact):
                flash('Invalid Contact Number')
                return render_template('signup.html')

            if password != retypepass:
                flash('Password mismatch, please retry', 'danger')
                return render_template('signup.html')
            
            if not terms:
                flash('You must accept the terms and conditions', 'danger')
                return render_template('signup.html')

            # Handle image upload
            img_up = None
            if image_upload and allowed_file(image_upload.filename):
                filename = secure_filename(image_upload.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                try:
                    image_upload.save(file_path)
                    img_up = filename
                except Exception as e:
                    flash(f'File upload failed: {str(e)}', 'danger')
                    return render_template('signup.html')
            else:
                if not image_upload:
                    flash('No image selected for uploading.', 'danger')
                    return render_template('signup.html')

            # Hash the password
            hashed_password = ph.hash(password)

            # Insert new user data
            signup_area.execute(
                'INSERT INTO apartmentsingup (name, address ,contact_number, plate_number, roomNumber, ProfilePic) VALUES (%s,%s, %s, %s, %s, %s)',
                (name, address,contact_number, platenum, Roomnumber, img_up)
            )
            authen.commit()
            userid = signup_area.lastrowid

            signup_area.execute(
                'INSERT INTO loginapartment (email, password, loginid, uservalue) VALUES (%s, %s, %s, %s)',
                (email, hashed_password, userid, '0')
            )
            authen.commit()

            flash("Signup Complete", 'success')
            return redirect(url_for('authenticated.userlogin'))

        except pymysql.MySQLError as e:
            flash('Database error occurred during signup. Please try again later.', 'danger')
            print(f"Database error: {e}")
        finally:
            if 'authen' in locals():
                authen.close()

    return render_template('signup.html')

@authenticated.route('/Login', methods=['POST', 'GET'])
def userlogin():
    if request.method == 'POST':
        # Collect login credentials
        login_email = request.form.get('logemail')
        login_password = request.form.get('LoginpasswordField')

        # Attempt to connect to the database
        try:
            authen = get_db_connection()
            login_area = authen.cursor()

            # Retrieve user details
            login_area.execute(
                'SELECT loginid, uservalue, password FROM loginapartment WHERE email=%s',
                (login_email,)
            )
            user = login_area.fetchone()

            # Check if user exists and password is correct
            if user:
                login_id = user['loginid']
                user_value = user['uservalue']
                stored_password = user['password']

                try:
                    # Verify the password
                    if ph.verify(stored_password, login_password):
                        # Set up session
                        session['user_id'] = login_id
                        session.permanent = True

                        # Redirect based on user role
                        if user_value == 1:
                            flash('Welcome, Admin!', 'success')
                            return redirect(url_for('admins.Admin_dashboard'))
                        elif user_value == 0:
                            flash('Welcome, User!', 'success')
                            return redirect(url_for('userdashboard'))
                        else:
                            flash('Unknown user type', 'danger')
                            return redirect(url_for('authenticated.userlogin'))
                    else:
                        flash('Invalid email or password', 'danger')
                except Exception as e:
                    flash(f'Error verifying password', 'danger')
            else:
                flash('Invalid email or password', 'danger')

        except pymysql.MySQLError as e:
            flash('Database connection failed. Please try again later.', 'danger')
            print(f"Database error: {e}")
        finally:
            if 'authen' in locals():
                authen.close()

    return render_template('login.html')

@authenticated.route('/logout')
def logout():
    # Clear the session and redirect to the homepage
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('index'))
