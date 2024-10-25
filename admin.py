from flask import Blueprint, request, render_template, flash, redirect, url_for, session,jsonify,current_app
from datetime import datetime
from flask_cors import CORS
from werkzeug.utils import secure_filename
import pymysql
import os
import logging
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError



logging.basicConfig(level=logging.DEBUG)


def connection_establish():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='apartment',
        cursorclass=pymysql.cursors.DictCursor
    )

admins=Blueprint('admins',__name__)
UPLOAD_FOLDER = os.path.join('static','uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
CORS(admins)
ph = PasswordHasher()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Admin Area
@admins.route('/Admin/user-Profile', methods=['POST', 'GET'])
def Admin_Profile():
    admin_session = session.get('user_id')
    con_adminprof = connection_establish()
    cursor_prof = con_adminprof.cursor()

    if admin_session is None:
        return redirect(url_for('authenticated.userlogin'))

    if request.method == 'POST':
        print("Admin Entered POST method.")

        if "password_admin" in request.form:
            admin_current = request.form.get('admincurrentPassword')
            admin_new = request.form.get('adminnewPassword')
            admin_retype = request.form.get('adminconfirmPassword')
            cursor_prof.execute('SELECT `password` FROM `loginapartment` WHERE loginid=%s', (admin_session,))
            admin_fetcher = cursor_prof.fetchone()

            print("Profile input data:", admin_current, admin_new, admin_retype)

            if admin_fetcher is None:
                flash('Current password not found, please retry', 'danger')
                return redirect(url_for('admins.Admin_Profile'))

            admin_stored_password = admin_fetcher['password']

            try:
                # Verify the current password
                ph.verify(admin_stored_password, admin_current)
            except VerifyMismatchError:
                flash('Current Password mismatch, please retry', 'danger')
                return redirect(url_for('admins.Admin_Profile'))

            if admin_new and admin_retype:
                if admin_new != admin_retype:
                    flash('Password mismatch, please retry', 'danger')
                    return redirect(url_for('admins.Admin_Profile'))

                else:
                    # Hash the new password before storing it
                    hashed_new_password = ph.hash(admin_new)
                    cursor_prof.execute('UPDATE loginapartment SET password = %s WHERE loginid = %s', (hashed_new_password, admin_session))
                    con_adminprof.commit()
                    flash('Password updated successfully!', 'success')
                    return redirect(url_for('admins.Admin_Profile'))

        if "admin_changes" in request.form:
            admin_name = request.form.get('admin_name')
            admin_email = request.form.get('admin_email')
            admin_address = request.form.get('admin_address')
            admin_val = request.form.get('admin_value')

            cursor_prof.execute("""UPDATE apartmentsingup a
                JOIN loginapartment l ON a.userid = l.loginid
                SET a.name = %s, a.address = %s, l.email = %s, l.uservalue = %s
                WHERE l.loginid = %s""", (admin_name, admin_address, admin_email, admin_val, admin_session))
            con_adminprof.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('admins.Admin_Profile'))

    cursor_prof.execute('''
        SELECT 
            a.name, 
            a.address,  
            l.email,
            l.uservalue
        FROM 
            apartmentsingup a
        JOIN 
            loginapartment l ON a.userid = l.loginid
        WHERE 
            l.loginid = %s
    ''', (admin_session,))
    admin_profile = cursor_prof.fetchall()
    print("Profile data:", admin_profile)

    return render_template('adminprofile.html', admin_profile=admin_profile)



@admins.route('/Admin-Dashboard', methods=['POST', 'GET'])
def Admin_dashboard():
    con_admin = connection_establish()
    throw_data = con_admin.cursor()

    if request.method == 'GET':
        print("Received GET request for Admin Dashboard.")
        throw_data.execute(""" 
            SELECT 
                a.userid, 
                a.name, 
                a.address, 
                a.plate_number, 
                a.roomNumber,
                a.ProfilePic, 
                l.email
            FROM 
                apartmentsingup a 
            JOIN 
                loginapartment l ON a.userid = l.loginid
        """)
        
        data = throw_data.fetchall()
        print("Raw data from DB:", data)

        users = [
            {
                'userid': row['userid'],
                'name': row['name'],
                'address': row['address'],
                'plate_number': row['plate_number'],
                'roomNumber': row['roomNumber'],
                'ProfilePic':row['ProfilePic'],
                'email': row['email']
            }
            for row in data
        ]
        
        print("Formatted user data:", users)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            print("AJAX request detected. Returning JSON.")
            return jsonify(users)
        else:
            print("Rendering HTML with user data.")
            return render_template("Admin.html", users=users)

    if request.method == 'POST':
        data = request.json
        print("Received POST request with data:", data)  
        
        action = data.get('action')

        if action == 'add':
            hashed_password = ph.hash(data['password'])
            try:
                throw_data.execute(
                    "INSERT INTO apartmentsingup (name, address, plate_number, roomNumber) VALUES (%s, %s, %s, %s)",
                    (data['name'], data['address'], data['plate_number'], data['roomNumber'])
                )
                login_id = throw_data.lastrowid
                throw_data.execute(
                    "INSERT INTO loginapartment (loginid, email, password) VALUES (%s, %s, %s)",
                    (login_id, data['email'], hashed_password)
                )
                con_admin.commit()
                return jsonify({'status': 'Data added'}), 201
            except Exception as e:
                con_admin.rollback()
                print("Error while adding user:", e)
                return jsonify({'status': 'Error', 'message': str(e)}), 500

        elif action == 'update':
            print("Updating user:", data)
            try:
                if 'password' in data and data['password']:
                    hashed_password = ph.hash(data['password'])
                    throw_data.execute(
                        "UPDATE loginapartment SET email = %s, password = %s WHERE loginid = %s",
                        (data['email'], hashed_password, data['userid'])
                    )
                else:
                    throw_data.execute(
                        "UPDATE loginapartment SET email = %s WHERE loginid = %s",
                        (data['email'], data['userid'])
                    )

                throw_data.execute(
                    "UPDATE apartmentsingup SET name = %s, address = %s, plate_number = %s, roomNumber = %s WHERE userid = %s",
                    (data['name'], data['address'], data['plate_number'], data['roomNumber'], data['userid'])
                )
                con_admin.commit()
                print("User updated successfully.")
                return jsonify({'status': 'Data updated'}), 200
            except Exception as e:
                con_admin.rollback()
                print("Error while updating user:", e)
                return jsonify({'status': 'Error', 'message': str(e)}), 500

        elif action == 'delete':
            print("Deleting user with ID:", data['userid'])
            try:
                throw_data.execute("DELETE FROM loginapartment WHERE loginid = %s", (data['userid'],))
                throw_data.execute("DELETE FROM apartmentsingup WHERE userid = %s", (data['userid'],))
                con_admin.commit()
                print("User deleted successfully.")
                return jsonify({'status': 'Data deleted'}), 200
            except Exception as e:
                con_admin.rollback()
                print("Error while deleting user:", e)
                return jsonify({'status': 'Error', 'message': str(e)}), 500

        elif action == 'view_utilities':
            print("Fetching utilities for user ID:", data['userid'])
            throw_data.execute(
                "SELECT login_id, water, electricity, parking, internet FROM utilities WHERE login_id = %s",
                (data['userid'],)
            )
            utility_data = throw_data.fetchone()
            
            if utility_data:
                utilities = {
                    'login_id': utility_data['login_id'],
                    'water': utility_data['water'],
                    'electricity': utility_data['electricity'],
                    'parking': utility_data['parking'],
                    'internet': utility_data['internet']
                }
                return jsonify(utilities), 200
            else:
                print("No utilities found for user ID:", data['userid'])
                return jsonify({'login_id': data['userid'], 'water': 0, 'electricity': 0, 'parking': 0, 'internet': 0}), 200

        elif action == 'update_utilities':
            print("Updating utilities for user ID:", data['userid'])
            try:
                throw_data.execute(
                    "SELECT * FROM utilities WHERE login_id = %s",
                    (data['userid'],)
                )
                existing_utilities = throw_data.fetchone()
                
                if existing_utilities:
                    throw_data.execute(
                        """UPDATE utilities SET 
                        water = %s, 
                        electricity = %s, 
                        parking = %s, 
                        internet = %s 
                        WHERE login_id = %s""",
                        (data['water'], data['electricity'], data['parking'], data['internet'], data['userid'])
                    )
                    print("Utilities updated successfully.")
                else:
                    throw_data.execute(
                        """INSERT INTO utilities (login_id, water, electricity, parking, internet) 
                        VALUES (%s, %s, %s, %s, %s)""",
                        (data['userid'], data['water'], data['electricity'], data['parking'], data['internet'])
                    )
                    print("Utilities inserted successfully.")
                
                con_admin.commit()
                return jsonify({'status': 'Utilities updated/inserted successfully'}), 200
            except Exception as e:
                con_admin.rollback()  # Rollback on error
                print("Error while updating utilities:", e)
                return jsonify({'status': 'Error', 'message': str(e)}), 500

    print("Rendering HTML for initial load")





@admins.route('/Apartments', methods=['GET', 'POST'])
def Admin_Apartment():
    con = connection_establish()
    cursor = con.cursor()

    if request.method == 'GET':
        room_id = request.args.get('room_id')
        if room_id:
            cursor.execute("SELECT * FROM room_avail WHERE room_id = %s", (room_id,))
            apartment = cursor.fetchone()
            if apartment:
                return jsonify(apartment), 200
        
        # Fetch all apartments
        cursor.execute(""" 
            SELECT r.room_id, r.Unit_name, r.RoomNumber, r.room_floor, r.room_size, r.Room_Img, 
                   o.Last_inspect, o.condition_status 
            FROM room_avail r 
            LEFT JOIN apartment_occupancy o ON r.room_id = o.Apartment_id
        """)
        apartments = cursor.fetchall()

        apartment_list = [{'room_id': apt['room_id'], 'Unit_name': apt['Unit_name'], 'RoomNumber': apt['RoomNumber'], 
                           'room_floor': apt['room_floor'], 'room_size': apt['room_size'], 'Room_Img': apt['Room_Img'], 
                           'Last_inspect': apt['Last_inspect'], 'condition_status': apt['condition_status']} 
                          for apt in apartments]

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(apartment_list), 200

        return render_template("ApartmentList.html", apartmentlist=apartment_list)
    
    if request.method == 'POST':
        action = request.form.get('action')
        room_id = request.form.get('room_id')

        if action == 'deleteapartment' and room_id:
            print("Deleting room ID:", room_id)
            try:
                # Execute deletion commands
                cursor.execute("DELETE FROM apartment_occupancy WHERE Apartment_id = %s", (room_id,))
                cursor.execute("DELETE FROM room_avail WHERE room_id = %s", (room_id,))
                con.commit() 
                return jsonify({'message': 'Apartment deleted successfully'}), 200 
            except Exception as e:
                con.rollback() 
                return jsonify({'error': str(e)}), 500

        elif action == 'addapartment':
            # Handle adding a new apartment
            unit_name = request.form.get('Unit_name')
            room_number = request.form.get('RoomNumber')
            room_floor = request.form.get('room_floor')
            room_size = request.form.get('room_size')
            last_inspect = request.form.get('Last_inspect')
            condition_status = request.form.get('condition_status')

            room_img = None  # Default value for room image

            # Handle image upload
            if 'Room_Img' in request.files:
                file = request.files['Room_Img']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    room_img = os.path.join(filename)

            try:
                cursor.execute("""
                    INSERT INTO room_avail (Unit_name, RoomNumber, room_floor, room_size, Room_Img) 
                    VALUES (%s, %s, %s, %s, %s)
                """, (unit_name, room_number, room_floor, room_size, room_img))
                room_id = cursor.lastrowid

                cursor.execute("""
                    INSERT INTO apartment_occupancy (Apartment_id, Last_inspect, condition_status) 
                    VALUES (%s, %s, %s)
                """, (room_id, last_inspect, condition_status))

                con.commit()
                return jsonify({'message': 'Apartment added successfully', 'room_id': room_id}), 200
            except Exception as e:
                con.rollback()  # Roll back in case of error
                return jsonify({'error': str(e)}), 500  # Return error message in JSON

        elif action == 'updateapartment' and room_id:
            # Fetch existing apartment details
            cursor.execute("SELECT Room_Img FROM room_avail WHERE room_id = %s", (room_id,))
            existing_image = cursor.fetchone()
            cursor.execute("SELECT Last_inspect, condition_status FROM apartment_occupancy WHERE Apartment_id = %s", (room_id,))
            existing_apartment = cursor.fetchone()

            if not existing_apartment:
                return jsonify({'message': 'Apartment not found'}), 404

            existing_last_inspect = existing_apartment['Last_inspect']
            existing_condition_status = existing_apartment['condition_status']

            # Handle updating existing apartment details
            unit_name = request.form.get('Unit_name')
            room_number = request.form.get('RoomNumber')
            room_floor = request.form.get('room_floor')
            room_size = request.form.get('room_size')
            date_inspect = request.form.get('Last_inspect')
            condition_status = request.form.get('condition_status')

            # Handle image upload
            room_img = existing_image['Room_Img'] if existing_image else None  # Keep existing image by default

            if 'Room_Img' in request.files:
                file = request.files['Room_Img']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    room_img = os.path.join(filename)

            # Set the Last_inspect and condition_status to the new values or keep the existing ones if not provided
            if not date_inspect:
                date_inspect = existing_last_inspect
            if not condition_status:
                condition_status = existing_condition_status

            try:
                cursor.execute("""
                    UPDATE room_avail 
                    SET Unit_name = %s, RoomNumber = %s, room_floor = %s, room_size = %s, Room_Img = %s 
                    WHERE room_id = %s
                """, (unit_name, room_number, room_floor, room_size, room_img, room_id))

                cursor.execute("""
                    UPDATE apartment_occupancy 
                    SET Last_inspect = %s, condition_status = %s 
                    WHERE Apartment_id = %s
                """, (date_inspect, condition_status, room_id))

                con.commit()
                return jsonify({'message': 'Apartment updated successfully'}), 200
            except Exception as e:
                con.rollback()  # Roll back in case of error
                return jsonify({'error': str(e)}), 500  # Return error message in JSON



    return jsonify({'error': 'Invalid request'}), 400





@admins.route('/Admin-Maintenance', methods=['GET', 'POST'])
def Admin_Maintenance():
    maintenanceconn = connection_establish()
    executer = maintenanceconn.cursor()

    if request.method == 'GET':
        # Fetch maintenance records from the database
        executer.execute("""
            SELECT 
                m.maintain_id, 
                m.login_id, 
                m.maintenance_issue, 
                m.priority, 
                m.filename, 
                m.maintenancedate, 
                a.roomNumber,
                m.status
            FROM 
                maintenance m
            JOIN 
                loginapartment la ON m.login_id = la.loginid
            JOIN 
                apartmentsingup a ON la.loginid = a.userid
        """)
        
        maintenance_raw = executer.fetchall()

        maintenance_list = [{
            'maintain_id': mainlist['maintain_id'],
            'login_id': mainlist['login_id'],
            'maintenance_issue': mainlist['maintenance_issue'],
            'priority': mainlist['priority'],
            'filename': mainlist['filename'],
            'maintenancedate': mainlist['maintenancedate'],
            'roomNumber': mainlist['roomNumber'],
            'status': mainlist['status']  # Ensure the status is fetched correctly
        } for mainlist in maintenance_raw]

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(maintenance_list)

    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_maintenance':
            maintain_id = request.form.get('maintain_id')
            new_status = request.form.get('status')

            executer.execute("""
                UPDATE `maintenance` 
                SET `status` = %s 
                WHERE `maintain_id` = %s
            """, (new_status, maintain_id))
            maintenanceconn.commit()

            return jsonify({'message': 'Status updated successfully'})

        elif action == 'delete':
            maintain_id = request.form.get('maintain_id')

            executer.execute("""
                DELETE FROM `maintenance` 
                WHERE `maintain_id` = %s
            """, (maintain_id,))
            maintenanceconn.commit()

            return jsonify({'message': 'Maintenance record deleted successfully'})  # Return a response

    return render_template("Admin_umaintenance.html", maintenance_list=maintenance_list)




@admins.route('/Lease_management', methods=['GET'])
def Admin_lease():
    lease_con = connection_establish()
    lease_Exec = lease_con.cursor()

    try:
        # Fetch lease information
        lease_Exec.execute("""
            SELECT 
                li.leaseid, 
                li.login_id, 
                li.lease_start, 
                li.lease_end, 
                li.monthly, 
                li.deposite, 
                li.status, 
                a.name 
            FROM 
                lease_inform li
            JOIN 
                apartmentsingup a ON li.login_id = a.userid
        """)
        lease_data = lease_Exec.fetchall()
        datalease_show = [
            {
                'leaseid': lease_all['leaseid'],
                'lease_start': lease_all['lease_start'].isoformat(),
                'lease_end': lease_all['lease_end'].isoformat(),
                'monthly': lease_all['monthly'],
                'deposite': lease_all['deposite'],
                'status': lease_all['status'],
                'name': lease_all['name']
            }
            for lease_all in lease_data
        ]

        # Fetch lease requests with apartment names
        lease_Exec.execute("""
            SELECT 
                lr.leaseRec_id,
                lr.login_Id, 
                lr.start_date, 
                lr.end_date, 
                lr.Comments, 
                lr.approval, 
                a.name 
            FROM 
                lease_request lr
            JOIN 
                apartmentsingup a ON lr.login_Id = a.userid
            WHERE 
                lr.approval = 0  -- Assuming 0 means pending
        """)
        lease_mail = lease_Exec.fetchall()
        email_recieve = [
            {
                'leaseRec_id': mailed['leaseRec_id'],
                'login_Id': mailed['login_Id'],
                'start_date': mailed['start_date'].isoformat(),
                'end_date': mailed['end_date'].isoformat(),
                'Comments': mailed['Comments'],
                'approval': mailed['approval'],
                'name': mailed['name']
            }
            for mailed in lease_mail
        ]

        # Calculate unread count (number of pending lease requests)
        unread_count = len(email_recieve)

        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(
                datalease_show=datalease_show, 
                email_recieve=email_recieve,
                unreadCount=unread_count
            ), 200

        # Render template for standard GET requests
        return render_template(
            'Admin_lease.html', 
            datalease_show=datalease_show, 
            email_recieve=email_recieve
        )
    
    except Exception as e:
        print(f'Error in Admin_lease: {str(e)}')
        return jsonify({'error': 'Internal Server Error'}), 500

    finally:
        lease_Exec.close()
        lease_con.close()


@admins.route('/update_approval', methods=['POST'])
def update_approval():
    lease_con = connection_establish()
    lease_Exec = lease_con.cursor()
    
    try:
        data = request.get_json()
        lease_id = data.get('lease_id')
        approval_status = data.get('approval_status')
        lease_start = data.get('lease_start')
        lease_end = data.get('lease_end')
        action = data.get('action')
    
        if action in ['approve', 'decline']:
            # Fetch the lease request to ensure it exists
            lease_Exec.execute("SELECT * FROM lease_request WHERE leaseRec_id = %s", (lease_id,))
            lease_request = lease_Exec.fetchone()
    
            if not lease_request:
                return jsonify({'error': 'Lease request does not exist.'}), 400
    
            if action == 'approve':
                # Extract 'monthly' and 'Downpayment' from lease_request
                monthly = lease_request.get('monthly', 0)
                downpayment = lease_request.get('Downpayment', 0)  # Ensure correct field name
                
                # Insert or update the lease in lease_inform
                lease_Exec.execute("""
                    INSERT INTO lease_inform (login_id, lease_start, lease_end, monthly, deposite, status) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        lease_start = VALUES(lease_start), 
                        lease_end = VALUES(lease_end),
                        monthly = VALUES(monthly),
                        deposite = VALUES(deposite),
                        status = VALUES(status)
                """, (lease_request['login_Id'], lease_start, lease_end, monthly, downpayment, 'Approved'))
    
            # Delete the lease request after processing
            lease_Exec.execute("DELETE FROM lease_request WHERE leaseRec_id = %s", (lease_id,))
    
            lease_con.commit()
            return jsonify({"message": "Lease request processed successfully."}), 200
    
        elif action == 'delete-lease':
            # Delete the lease from lease_inform
            lease_Exec.execute("DELETE FROM lease_inform WHERE leaseid = %s", (lease_id,))
            lease_con.commit()
            return jsonify({"message": "Lease deleted successfully."}), 200
    
        else:
            return jsonify({'error': 'Invalid action specified.'}), 400
    
    except Exception as e:
        lease_con.rollback()
        print(f'Error in update_approval: {str(e)}')  # Log the error for debugging
        return jsonify({'error': 'Internal Server Error'}), 500
    
    finally:
        lease_Exec.close()
        lease_con.close()





@admins.route('/Emergency_Records', methods=['GET', 'POST'])
def Admin_Emergency():
    emergency_conn = connection_establish()
    exec_emergency = emergency_conn.cursor()
    try:
        if request.method == "GET":
            exec_emergency.execute("SELECT * FROM emergency_records")
            handle_emergency = exec_emergency.fetchall()

            listed_emergency = [{
                'emergency_id': a['emergency_id'],
                'disaster': a['disaster'],
                'happen_date': a['happen_date'],
                'Unitroom': a['Unitroom'],
                'description': a['description'],
                'status_completion': a['status_completion']
            } for a in handle_emergency]

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(listed_emergency), 200

        if request.method == "POST":
            req_emergency = request.form.get('emergency_id')
            req_stat = request.form.get('status_completion')
            action = request.form.get('action')

            if action == 'delete_emergency':
                exec_emergency.execute("DELETE FROM emergency_records WHERE emergency_id=%s", (req_emergency,))
                emergency_conn.commit()
                return jsonify({'message': 'Emergency deleted successfully.'}), 200

            elif action == "add_emergency":
                disaster = request.form.get('disaster')
                happen_date = request.form.get('happen_date')
                unitroom = request.form.get('Unitroom')
                description = request.form.get('description')

                exec_emergency.execute(
                    "INSERT INTO emergency_records (disaster, happen_date, Unitroom, description, status_completion) VALUES (%s, %s, %s, %s, %s)",
                    (disaster, happen_date, unitroom, description, 'Pending')  # Default status
                )
                emergency_conn.commit()
                return jsonify({'message': 'Added new emergency record.'}), 200

            elif action == "status_comp":
                exec_emergency.execute(
                    "UPDATE emergency_records SET status_completion=%s WHERE emergency_id=%s",
                    (req_stat, req_emergency)
                )
                emergency_conn.commit()
                return jsonify({'message': 'Status updated successfully.'}), 200

    except Exception as e:
        return f"An error occurred: {str(e)}", 500

    return render_template('EmergencyRec.html')



@admins.route('/Visitor-Engagement', methods=['POST', 'GET'])
def visitorlogs():
    visitor_conn = connection_establish()
    exec_visitors = visitor_conn.cursor()
    try:
        if request.method == 'GET':
            exec_visitors.execute("SELECT * FROM visitors_apartment")
            review_visitors = exec_visitors.fetchall()
            
            visitor_list = [
                {
                    'visit_id': visit_val['visit_id'],
                    'visitor_name': visit_val['visitor_name'],
                    'visitor_email': visit_val['visitor_email'],
                    'visited_room': visit_val['visited_room'],
                    'visited_date': visit_val['visited_date'],
                    'visit_reason': visit_val['visit_reason']
                } 
                for visit_val in review_visitors
            ]
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(visitor_list), 200

            exec_visitors.execute("""
                SELECT 
                    MIN(`today`) AS start_date,
                    MAX(`today`) AS end_date,
                    COUNT(*) AS weekly_count 
                FROM 
                    `apartmentanalytics` 
                WHERE 
                    `today` >= DATE_SUB(CURDATE(), INTERVAL 12 WEEK) 
                GROUP BY 
                    YEAR(`today`), WEEK(`today`, 1) 
                ORDER BY 
                    start_date;
            """)
            counted_graph = exec_visitors.fetchall()

            formatted_graph = [
                {
                    'start_date': datetime.strftime(row['start_date'], '%m/%d/%Y'),
                    'end_date': datetime.strftime(row['end_date'], '%m/%d/%Y'),
                    'weekly_count': row['weekly_count']
                }
                for row in counted_graph
            ]
            
            return render_template('adminanalytics.html', visitor_list=visitor_list, counted_graph=formatted_graph)
    
    except Exception as e:
        return f"An error occurred: {str(e)}", 500
    
    finally:
        exec_visitors.close()
        visitor_conn.close()

@admins.route('/Visitor-Engagement/delete', methods=['POST'])
def delete_visitor():
    visitor_conn = connection_establish()
    exec_visitors = visitor_conn.cursor()
    visit_id = request.form.get('visit_id')
    try:
        exec_visitors.execute("DELETE FROM visitors_apartment WHERE visit_id = %s", (visit_id,))
        visitor_conn.commit()  # Commit the change to the database
        return jsonify({'message': 'Visitor deleted successfully.'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        exec_visitors.close()
        visitor_conn.close()


