from flask import Flask,render_template,session,redirect,url_for,request,flash,jsonify
import os
import re
from admin import admins
from auth import authenticated
from datetime import datetime,timedelta,date
from werkzeug.utils import secure_filename
from flask_session import Session
import pymysql.cursors
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import logging

secret_key=os.urandom(10)
# Configure logging
logging.basicConfig(level=logging.DEBUG)

conn=pymysql.connect(host='localhost',
                    user="root",
                     password="",
                    database="apartment",
                    cursorclass=pymysql.cursors.DictCursor)





app=Flask(__name__,static_url_path=('/static'))

#Configuration
ph = PasswordHasher()
app.config['SECRET_KEY']=secret_key
app.config['SESSION_TYPE']='filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_USE_SIGNER'] = True
UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.register_blueprint(admins, url_prefix='/admin')
app.register_blueprint(authenticated, url_prefix='')
Session(app)


def is_valid_contact(contact):
    pattern = re.compile(r'^\+?\d{11,12}$')
    return pattern.match(contact) is not None

#index area or home area
@app.route("/terms&Condition")
def terms():
    return render_template('terms.html')
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/Plans')
def plans():
    return render_template("plans.html")


@app.route('/Room_Available')
def roomavailable():
    
    show_room = conn.cursor()
    show_room.execute("SELECT * FROM room_avail ORDER BY room_id ASC")
    rooms = show_room.fetchall()

        # Fetch distinct occupied room numbers
    show_room.execute("SELECT DISTINCT roomNumber FROM apartmentsingup")
    occupied_rooms = show_room.fetchall()
    occupied_room_numbers = {room['roomNumber'] for room in occupied_rooms}  

    print("Occupied Rooms:", occupied_room_numbers)
    print("Room Availability:", rooms)


 
    return render_template("roomavailability.html", rooms=rooms, occupied_room_numbers=occupied_room_numbers)

@app.route('/FloorPlan')
def apartmentplan():

    return render_template('floorplan.html')

@app.route('/Dashboard', methods=['GET', 'POST'])
def userdashboard():
    session.permanent = True
    login_id = session.get('user_id')
    if login_id is None:
        return redirect(url_for('authenticated.userlogin'))

    established = conn.cursor()
    
    try:
    # Fetch room details if assigned to a room
        established.execute('SELECT roomNumber FROM apartmentsingup WHERE userid = %s', (login_id,))
        its_occupied = established.fetchone()
        print("Room number data:", its_occupied)

        room_details = None
        if its_occupied:
            room_number = its_occupied['roomNumber']
            # Fetch room details
            established.execute('''SELECT room_id, Unit_name, room_floor, room_size, Room_Img 
                                FROM room_avail 
                                WHERE RoomNumber = %s''', (room_number,))
            room_details = established.fetchone()
            print("Room details data:", room_details)

    # Fetch lease data
        established.execute("""
    SELECT 
        DATE_FORMAT(lease.lease_start, '%%m/%%d/%%Y') AS format_lease_start,
        DATE_FORMAT(lease.lease_end, '%%m/%%d/%%Y') AS format_lease_end,
        TIMESTAMPDIFF(MONTH, lease.lease_start, lease.lease_end) AS addmonth,
        lease.monthly,
        lease.status,
        lease.deposite,
        CASE WHEN utilities.water = 1 THEN 200 ELSE 0 END AS water_cost,
        CASE WHEN utilities.electricity = 1 THEN 500 ELSE 0 END AS electricity_cost,
        CASE WHEN utilities.internet = 1 THEN 300 ELSE 0 END AS internet_cost,
        lease.monthly + 
        (CASE WHEN utilities.water = 1 THEN 200 ELSE 0 END +
         CASE WHEN utilities.electricity = 1 THEN 500 ELSE 0 END +
         CASE WHEN utilities.internet = 1 THEN 300 ELSE 0 END) AS overall_cost,
        DATE_FORMAT(DATE_ADD(lease.lease_start, INTERVAL 1 MONTH), '%%m/%%d/%%Y') AS next_payment_date,
        lease.monthly + 
        (CASE WHEN utilities.water = 1 THEN 200 ELSE 0 END +
         CASE WHEN utilities.electricity = 1 THEN 500 ELSE 0 END +
         CASE WHEN utilities.internet = 1 THEN 300 ELSE 0 END) AS total_next_payment_cost
    FROM 
        lease_inform lease
    LEFT JOIN 
        utilities ON lease.login_id = utilities.login_id
    WHERE 
        lease.login_id = %s;
""", (login_id,))


        
        lease_data = established.fetchall()
        print("Lease Data:", lease_data)

        # Fetch utility data
        established.execute(''' 
            SELECT 
                utilitiesid, 
                CASE WHEN water = 1 THEN 'Included' ELSE 'Not Included' END AS water_status,
                CASE WHEN electricity = 1 THEN 'Included' ELSE 'Not Included' END AS electricity_status,
                CASE WHEN internet = 1 THEN 'Included' ELSE 'Not Included' END AS internet_status
            FROM utilities 
            WHERE login_id = %s
        ''', (login_id,))
        utils = established.fetchall()
        print("Utilities Data:", utils)

        # Fetch visitor data
        established.execute(''' 
            SELECT 
                visit_id, 
                visitor_name, 
                visitor_email, 
                visited_room,
                time_in,
                visit_reason,
                confirmation,
                DATE_FORMAT(visited_date, '%%m/%%d/%%Y') AS formatted_visited_date 
            FROM visitors_apartment 
            WHERE visited_room = %s AND (time_out IS NULL OR time_out = '')
        ''', (room_number,))
        visitors = established.fetchall()
        print("Visitor Data:", visitors)

        if request.method == 'POST':
            action = request.json.get('action') 
            visitor_id = request.json.get('visitor_id')
            
            if not visitor_id:
                return jsonify({"message": "Missing visitor ID."}), 400  

            
            time_now = datetime.now()
            formatted_time = time_now.strftime("%I:%M %p")  
            
            
            try:
                if action == 'approve':
                    established.execute('''UPDATE visitors_apartment SET confirmation = 'approved' WHERE visit_id = %s''', (visitor_id,))
                    conn.commit()  
                    return jsonify({"message": "Visitor approved successfully."}), 200

                elif action == 'delete':
                    established.execute('''DELETE FROM visitors_apartment WHERE visit_id = %s''', (visitor_id,))
                    conn.commit()  
                    return jsonify({"message": "Visitor deleted successfully."}), 200

                elif action == "leave":
                    established.execute('UPDATE visitors_apartment SET time_out = %s WHERE visit_id = %s', (formatted_time, visitor_id))
                    conn.commit()
                    return jsonify({"message": "Successfully left."}), 200

                else:
                    return jsonify({"message": "Invalid action."}), 400  

            except Exception as e:
                conn.rollback() 
                print("Error occurred:", e) 
                return jsonify({"message": f"An error occurred while processing your request: {str(e)}"}), 500
            
            finally:
                if established:
                    established.close() 

    except Exception as e:
        print("An error occurred while fetching data:", e)  # Log any errors during data fetching
        return jsonify({"message": "An error occurred while processing your request."}), 500

    return render_template("dashboard.html", room_details=room_details, lease_data=lease_data, utils=utils, visitors=visitors)




@app.route('/Maintenance', methods=['POST', 'GET'])
def usermaintenance():
    session.permanent = True
    maintenance_id = session.get('user_id')

    if maintenance_id is None:
        return redirect(url_for('authenticated.userlogin'))

    maintenance_data = []
    mainten = conn.cursor()  # Initialize cursor at the start

    if request.method == 'POST':
        # Validate form data
        mainten_issue = request.form.get('maintenance_issue')
        mainten_priority = request.form.get('priority')
        nowdate=date.today()
        status_pending='Pending'

        if not mainten_issue or not mainten_priority:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('usermaintenance'))

        filenames = []
        # Handle file uploads
        if 'attachments' in request.files:
            files = request.files.getlist('attachments')

            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    filenames.append(filename)

            print("Uploaded files:", filenames)

        mainten_filename = ','.join(filenames)

        try:
            mainten.execute('INSERT INTO maintenance (login_id, maintenance_issue, priority, filename,maintenancedate,status) VALUES (%s,%s,%s, %s, %s, %s)',
                            (maintenance_id, mainten_issue, mainten_priority, mainten_filename,nowdate,status_pending))
            conn.commit()
            flash('Maintenance request submitted successfully!', 'success')
            return redirect(url_for('usermaintenance'))
        except Exception as e:
            print(f"Error inserting maintenance data: {e}")
            conn.rollback()
            flash('An error occurred while submitting your request. Please try again.', 'danger')

    # Fetch maintenance data for GET request
    try:
        mainten.execute("""SELECT la.email, asu.name, asu.roomNumber
                           FROM loginapartment la
                           JOIN apartmentsingup asu ON la.loginid = asu.userid
                           WHERE la.loginid = %s""", (maintenance_id,))
        maintenance_data = mainten.fetchall()
    except Exception as e:
        print(f"Error fetching maintenance data: {e}")

    print("Fetched maintenance data:", maintenance_data) 

    return render_template("Maintenance.html", maintenance_data=maintenance_data)



@app.route('/Lease', methods=['POST', 'GET'])
def userlease():
    session.permanent = True
    lease_session = session.get('user_id')

    if lease_session is None:
        return redirect(url_for('authenticated.userlogin'))

    lease_con = conn.cursor()
    lease_con.execute("""
    SELECT 
        DATE_FORMAT(lease.lease_start, '%%m/%%d/%%Y') AS format_lease_start,
        DATE_FORMAT(lease.lease_end, '%%m/%%d/%%Y') AS format_lease_end,
        TIMESTAMPDIFF(MONTH, lease.lease_start, lease.lease_end) AS addmonth,
        lease.monthly,
        lease.status,
        
        -- Utility cost calculations
        (CASE WHEN utilities.water = 1 THEN 200 ELSE 0 END) AS water_cost,
        (CASE WHEN utilities.electricity = 1 THEN 500 ELSE 0 END) AS electricity_cost,
        (CASE WHEN utilities.internet = 1 THEN 300 ELSE 0 END) AS internet_cost,
        
        -- Total utility cost
        (CASE WHEN utilities.water = 1 THEN 200 ELSE 0 END) +
        (CASE WHEN utilities.electricity = 1 THEN 500 ELSE 0 END) +
        (CASE WHEN utilities.internet = 1 THEN 300 ELSE 0 END) AS total_utilities_cost,
        
        -- Overall cost
        lease.monthly + 
        ((CASE WHEN utilities.water = 1 THEN 200 ELSE 0 END) +
        (CASE WHEN utilities.electricity = 1 THEN 500 ELSE 0 END) +
        (CASE WHEN utilities.internet = 1 THEN 300 ELSE 0 END)) AS overall_cost

    FROM 
        lease_inform lease
    LEFT JOIN 
        utilities ON lease.login_id = utilities.login_id
    WHERE 
        lease.login_id = %s;
""", (lease_session,))

    lease_cred = lease_con.fetchall()
    print("Lease credentials:", lease_cred)

    today = datetime.today().date()


    lease_con.execute("SELECT  `start_date`, `end_date`, `monthly`, `approval` FROM `lease_request` WHERE login_Id=%s",(lease_session,))
    lease_req=lease_con.fetchall()


    if request.method == 'POST':
        sadate = datetime.today().date()
        endDate = request.form.get('endDate')
        comments = request.form.get('comments')
        monthly=request.form.get('mon_pay')
        downrequest=request.form.get('downpay')
        approval_value='Pending'

        try:
            lease_con.execute('''INSERT INTO `lease_request` 
                        (`login_Id`, `start_date`, `end_date`, `monthly`, `Downpayment`, `Comments`,approval) 
                        VALUES (%s, %s, %s, %s, %s, %s,%s)''',
                      (lease_session, sadate, endDate, monthly, downrequest, comments,approval_value))
            conn.commit()
            flash('Lease renewal request submitted successfully!', 'success')
        except Exception as e:
            print(f"Error inserting lease request: {e}")
            conn.rollback()
            flash('An error occurred while submitting your request. Please try again.', 'danger')

        return redirect(url_for('userlease'))


    return render_template("lease.html",lease_cred=lease_cred,today=today,lease_req=lease_req)




@app.route('/Emergency-Response')
def useremergency():
    return render_template("useremergency.html")


@app.route('/Profile', methods=['POST', 'GET'])
def user_profile():
    session.permanent = True
    profile_session = session.get('user_id')

    if profile_session is None:
        return redirect(url_for('authenticated.userlogin'))

    prof_exec = conn.cursor()

    try:
        if request.method == 'POST':
            # Handle user password update
            if "passwordupdate" in request.form:
                current_pass = request.form.get('currentPassword')
                new_pass = request.form.get('newPassword')
                confirm_pass = request.form.get('confirmPassword')

                # Check if any of the password fields are empty
                if not current_pass or not new_pass or not confirm_pass:
                    flash('All password fields are required.', 'danger')
                    return redirect(url_for('user_profile'))

                # Fetch the current password
                prof_exec.execute('SELECT password FROM loginapartment WHERE loginid=%s', (profile_session,))
                passelect = prof_exec.fetchone()

                if passelect is None or passelect['password'] is None:
                    flash('Current password not found, please retry.', 'danger')
                    return redirect(url_for('user_profile'))

                stored_password = passelect['password']

                # Verify the current password
                try:
                    if not ph.verify(stored_password, current_pass):
                        flash('Current password is incorrect, please retry.', 'danger')
                        return redirect(url_for('user_profile'))
                except VerifyMismatchError:
                    flash('Current password is incorrect, please retry.', 'danger')
                    return redirect(url_for('user_profile'))

                # Check if the new password and confirmation match
                if new_pass != confirm_pass:
                    flash('New password and confirmation do not match, please retry.', 'danger')
                    return redirect(url_for('user_profile'))

                # Hash the new password before storing it
                hashed_new_password = ph.hash(new_pass)
                prof_exec.execute('UPDATE loginapartment SET password = %s WHERE loginid = %s', 
                                  (hashed_new_password, profile_session))
                conn.commit()
                flash('Password updated successfully!', 'success')
                return redirect(url_for('user_profile'))

            # Handle user profile image upload
            if 'file' in request.files:
                file_prof = request.files['file']
                
                # Check if file is uploaded
                if file_prof and file_prof.filename:
                    filename = secure_filename(file_prof.filename)
                    file_prof.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    
                    # Update the database with the new image filename
                    update_query = '''
                        UPDATE apartmentsingup a
                        JOIN loginapartment l ON a.userid = l.loginid
                        SET a.ProfilePic = %s
                        WHERE l.loginid = %s
                    '''
                    prof_exec.execute(update_query, (filename, profile_session))
                    conn.commit()

                    # Return the URL of the new image
                    file_url = url_for('static', filename='uploads/' + filename)
                    return jsonify({"success": "Profile image updated successfully.", "file_url": file_url}), 200

            # Handle user profile information update
            if "userUpdate" in request.form:
                name = request.form.get('profname')
                address = request.form.get('profaddress')
                contact=request.form.get('profnumber')
                plate_number = request.form.get('plateno')
                email = request.form.get('profemail')

                if not is_valid_contact(contact):
                    flash(" Invalid contact Number",'danger')
                    return redirect(url_for('user_profile'))

                # Update profile information
                update_query = '''
                    UPDATE apartmentsingup a
                    JOIN loginapartment l ON a.userid = l.loginid
                    SET a.name = %s, a.address = %s,a.contact_number=%s, a.plate_number = %s, l.email = %s
                    WHERE l.loginid = %s
                '''
                
                prof_exec.execute(update_query, (name, address,contact, plate_number, email, profile_session))
                conn.commit()
                flash('Profile updated successfully!', 'success')
                return redirect(url_for('user_profile'))

        prof_exec.execute('''
            SELECT 
                a.name, 
                a.address, 
                a.plate_number,
                a.contact_number, 
                a.roomNumber,
                a.ProfilePic, 
                l.email
            FROM 
                apartmentsingup a
            JOIN 
                loginapartment l ON a.userid = l.loginid
            WHERE 
                l.loginid = %s;
        ''', (profile_session,))

        profileview = prof_exec.fetchall()

        return render_template('profile.html', profileview=profileview)

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"error": "An unexpected error occurred."}), 500

    finally:
        prof_exec.close() 






@app.route("/Visitors-Form", methods=['POST', 'GET'])
def visitorform():
    with conn.cursor() as dict_visitors:
        if request.method == 'POST':
            visit_name = request.form.get('visitor_name')
            visit_email = request.form.get('visitor_email')
            visit_room = request.form.get('visiting_room')
            visit_date = request.form.get('visit_date')
            visit_time=request.form.get('timeInput')
            visit_reason = request.form.get('visit_reason')
            mark_as = 1

            
            if visit_time:
                hour = int(visit_time.split(':')[0])
                minute = visit_time.split(':')[1]    
                period = "AM" if hour < 12 else "PM"

                # Convert 24-hour time to 12-hour format
                hour_12 = hour % 12 or 12
                formatted_time = f"{hour_12}:{minute} {period}"

            print("sa time input")

            # Fetch existing room numbers
            dict_visitors.execute('SELECT roomNumber FROM apartmentsingup')
            rawlist = dict_visitors.fetchall()

            try:
                visit_date_obj = datetime.strptime(visit_date, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
                return redirect(url_for('visitorform'))
            
            if visit_date_obj < datetime.today().date():
                flash('Date Invalid.', 'danger')
                return redirect(url_for('visitorform'))

            # Check if rawlist is empty
            if not rawlist:
                flash('No rooms available for visitors.', 'error')
                return redirect(url_for('visitorform'))

            # Create a set of existing rooms
            existing_rooms = {room['roomNumber'] for room in rawlist}

            # Check if the visited room exists
            if visit_room not in existing_rooms:
                flash('This room does not exist', 'danger')
                return redirect(url_for('visitorform'))

            # Insert the visitor data into the database
            try:
                dict_visitors.execute("""
                    INSERT INTO visitors_apartment (visitor_name, visitor_email, visited_room, visited_date,time_in, visit_reason,confirmation)
                    VALUES (%s, %s, %s, %s, %s,%s,%s)
                """, (visit_name, visit_email, visit_room, visit_date,formatted_time, visit_reason,"PENDING"))

                dict_visitors.execute("""
                    INSERT INTO apartmentanalytics (today, has_active) 
                    VALUES (%s, %s)
                """, (visit_date, mark_as))

                conn.commit()
                flash('Visitor form submitted successfully!', 'success')
            except Exception as e:
                conn.rollback()
                flash(f'Error occurred: {str(e)}', 'error') 

            return redirect(url_for('visitorform'))

    return render_template('visitors.html')


if __name__ == '__main__':
    app.run(debug=True)
