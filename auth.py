from flask import Blueprint, request, render_template, flash, redirect, url_for, session,current_app
import pymysql
from argon2 import PasswordHasher
from werkzeug.utils import secure_filename
import os


ph = PasswordHasher()
authen = pymysql.connect(
    host='localhost',
    user="root",
    password="",
    database="apartment",
    cursorclass=pymysql.cursors.DictCursor
)

authenticated = Blueprint('authenticated', __name__)
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@authenticated.route('/Sign-Up', methods=['POST', 'GET'])
def usersignup():
    if request.method == 'POST':
        print("Request files:", request.files)
        name = request.form.get('signame')
        address = request.form.get('sigadd')
        platenum = request.form.get('platenum')
        Roomnumber = request.form.get('Roomno')
        email = request.form.get('sigmail')
        password = request.form.get('passwordField')
        retypepass = request.form.get('RepeatpasswordField')
        image_upload = request.files.get('profileImage')

        print("sa image upload", image_upload)

        signup_area = authen.cursor()
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

        if password != retypepass:
            flash('Password mismatch, please retry', 'danger')
            return render_template('signup.html')

        img_up = None  
        if image_upload and allowed_file(image_upload.filename):
            filename = secure_filename(image_upload.filename)
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            try:
                image_upload.save(file_path)
                img_up = os.path.join(filename)
            except Exception as e:
                flash(f'File upload failed: {str(e)}', 'danger')
                return render_template('signup.html')
        else:
            if not image_upload:
                flash('No image selected for uploading.', 'danger')


        hashed_password = ph.hash(password)

        signup_area.execute(
            'INSERT INTO apartmentsingup(name, address, plate_number, roomNumber, ProfilePic) VALUES (%s, %s, %s, %s, %s)',
            (name, address, platenum, Roomnumber, img_up)
        )
        authen.commit() 

        userid = signup_area.lastrowid

        signup_area.execute(
            'INSERT INTO loginapartment(email, password, loginid, uservalue) VALUES (%s, %s, %s, %s)',
            (email, hashed_password, userid, '0')
        )
        authen.commit() 

        flash("Signup Complete", 'success')
        return redirect(url_for('authenticated.userlogin')) 
    
    return render_template('signup.html')


@authenticated.route('/Login', methods=['POST', 'GET'])
def userlogin():
    if request.method == 'POST':
        loginmail = request.form.get('logemail')
        logpassword = request.form.get('LoginpasswordField')

        # Print debug information
        print("sa email:", loginmail)
        print("sa pass:", logpassword)

        login_area = authen.cursor()

        # Query to get user information including user value
        login_area.execute(''' 
            SELECT loginid, uservalue, password 
            FROM loginapartment 
            WHERE email=%s
        ''', (loginmail,))

        user = login_area.fetchone()

        # Debugging output
        print("Fetched user:", user)

        if user:
            loginid = user['loginid']
            uservalue = user['uservalue']
            stored_password = user['password']

            # Verify the password using Argon2
            try:
                if ph.verify(stored_password, logpassword):
                    session['user_id'] = loginid
                    session.permanent = True

                    # Check user value
                    if uservalue == 1:
                        flash('Welcome, Admin!', 'success')
                        return redirect(url_for('admins.Admin_dashboard'))  
                    elif uservalue == 0:
                        flash('Welcome, User!', 'success')
                        return redirect(url_for('userdashboard')) 
                    else:
                        flash('Unknown user type', 'danger')
                        return redirect(url_for('authenticated.userlogin')) 
                else:
                    flash('Invalid email or password', 'danger')
                    return redirect(url_for('authenticated.userlogin'))
            except Exception as e:
                flash('Error verifying password', 'danger')
                print("Verification error:", e)
                return redirect(url_for('authenticated.userlogin'))
        else:
            flash('Invalid email or password', 'danger')
            return redirect(url_for('authenticated.userlogin'))

    return render_template('login.html')

@authenticated.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
