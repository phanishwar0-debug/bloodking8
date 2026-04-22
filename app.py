from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from datetime import datetime, timedelta
import hashlib
import json
import threading

app = Flask(__name__)
app.secret_key = 'blood_chain_secret_key_2024_secure'

# Import the SQLite config
from config import db_config, hash_password, email_config

# Blockchain Implementation
class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }

class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        
    def create_genesis_block(self):
        return Block(0, str(datetime.now()), {"message": "Genesis Block", "type": "genesis"}, "0")
    
    def get_latest_block(self):
        return self.chain[-1]
    
    def add_block(self, data):
        latest_block = self.get_latest_block()
        new_block = Block(
            index=len(self.chain),
            timestamp=str(datetime.now()),
            data=data,
            previous_hash=latest_block.hash
        )
        self.chain.append(new_block)
        return new_block.hash
    
    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]
            
            if current_block.hash != current_block.calculate_hash():
                return False
            
            if current_block.previous_hash != previous_block.hash:
                return False
        return True
    
    def get_all_blocks(self):
        return [block.to_dict() for block in self.chain]

    def get_chain_length(self):
        return len(self.chain)

# Initialize blockchain
blood_donation_blockchain = Blockchain()

# Helper functions
def get_db_connection():
    return db_config.get_connection()

def get_today_date():
    return datetime.now().strftime('%Y-%m-%d')

# Email Alert Functions
def send_bulk_emails(recipients, subject, message):
    """Send emails to multiple recipients in background"""
    def send_emails():
        success_count = 0
        failed_count = 0
        
        for recipient in recipients:
            if email_config.send_email(recipient['email'], subject, message):
                success_count += 1
                # Log successful email (assuming sender_id 1 for admin)
                log_email_alert('admin', 1, 'donor', recipient['email'], subject, message, recipient.get('blood_group'))
            else:
                failed_count += 1
                # Log failed email
                log_email_alert('admin', 1, 'donor', recipient['email'], subject, message, recipient.get('blood_group'), 'Failed')
        
        print(f"📧 Email campaign completed: {success_count} sent, {failed_count} failed")
    
    # Run in background thread
    thread = threading.Thread(target=send_emails)
    thread.daemon = True
    thread.start()
    
    return len(recipients)

def log_email_alert(sender_type, sender_id, recipient_type, recipient_email, subject, message, blood_group=None, status='Sent'):
    """Log email alert in database"""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO email_alerts (sender_type, sender_id, recipient_type, recipient_email, subject, message, blood_group, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sender_type, sender_id, recipient_type, recipient_email, subject, message, blood_group, status))
            conn.commit()
        except Exception as e:
            print(f"❌ Failed to log email alert: {e}")
        finally:
            conn.close()

def send_blood_request_alert(hospital_id, patient_name, blood_group, quantity, urgency):
    """Send blood request alerts to matching blood banks and donors"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Get hospital info
        cursor.execute("SELECT name FROM hospital WHERE id = ?", (hospital_id,))
        hospital = cursor.fetchone()
        hospital_name = hospital[0] if hospital else "Unknown Hospital"
        
        # Prepare email content
        subject = f"🚨 URGENT: Blood Required - {blood_group}"
        message = f"""
        <html>
        <body>
            <h2 style="color: #dc3545;">🚨 URGENT BLOOD REQUEST</h2>
            <p><strong>Hospital:</strong> {hospital_name}</p>
            <p><strong>Patient:</strong> {patient_name}</p>
            <p><strong>Blood Group Required:</strong> <span style="color: #dc3545; font-weight: bold;">{blood_group}</span></p>
            <p><strong>Quantity Needed:</strong> {quantity} ml</p>
            <p><strong>Urgency Level:</strong> {urgency}</p>
            <p><strong>Request Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <hr>
            <p style="color: #6c757d;">This is an automated alert from BloodChain System.</p>
            <p style="color: #6c757d;">Please respond immediately if you can help.</p>
        </body>
        </html>
        """
        
        # Send to blood banks
        cursor.execute("SELECT email, name FROM blood_banker")
        blood_banks = cursor.fetchall()
        
        for bank in blood_banks:
            bank_email, bank_name = bank
            # No need to modify 'message' for bank, as hospital contact is implicit in the alert
            if email_config.send_email(bank_email, subject, message):
                log_email_alert('hospital', hospital_id, 'blood_bank', bank_email, subject, message, blood_group)
        
        # Send to donors with matching blood group
        cursor.execute("SELECT email, name FROM donor WHERE blood_group = ? AND is_available = 1", (blood_group,))
        matching_donors = cursor.fetchall()
        
        for donor in matching_donors:
            donor_email, donor_name = donor
            donor_message = message + f"""
            <p><strong>Dear {donor_name},</strong></p>
            <p>Your blood group matches the urgent requirement. If you're available and eligible to donate, please contact the hospital immediately or visit your nearest blood bank.</p>
            <p style="color: #dc3545; font-weight: bold;">Your donation can save a life!</p>
            """
            if email_config.send_email(donor_email, subject, donor_message):
                log_email_alert('hospital', hospital_id, 'donor', donor_email, subject, donor_message, blood_group)
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to send blood request alerts: {e}")
        return False
    finally:
        conn.close()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# ==============================================================================
# ADMIN ROUTES
# ==============================================================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Default admin credentials
        if username == 'admin' and password == 'admin123':
            session['admin_id'] = 1
            session['admin_username'] = 'admin'
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials!', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    stats = {}
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get statistics
            cursor.execute("SELECT COUNT(*) as count FROM donor")
            stats['total_donors'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as count FROM blood_banker")
            stats['total_blood_bankers'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as count FROM hospital")
            stats['total_hospitals'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as count FROM patient")
            stats['total_patients'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT blood_group, SUM(quantity_ml) as total FROM blood_inventory WHERE status = 'Available' GROUP BY blood_group")
            blood_data = cursor.fetchall()
            stats['blood_inventory'] = [{'blood_group': row[0], 'total': row[1] or 0} for row in blood_data]
            
        except Exception as e:
            print(f"Error fetching stats: {e}")
            stats = {
                'total_donors': 0,
                'total_blood_bankers': 0,
                'total_hospitals': 0,
                'total_patients': 0,
                'blood_inventory': []
            }
        finally:
            conn.close()
    
    return render_template('admin_dashboard.html', stats=stats, email_config=email_config)

@app.route('/admin/send_alerts', methods=['GET', 'POST'])
def admin_send_alerts():
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        alert_type = request.form['alert_type']
        blood_group = request.form.get('blood_group', '')
        subject = request.form['subject']
        message = request.form['message']
        
        conn = get_db_connection()
        if not conn:
            flash('Database connection failed!', 'error')
            return render_template('admin_send_alerts.html')
        
        try:
            cursor = conn.cursor()
            
            # Get recipients based on alert type
            if alert_type == 'all_donors':
                cursor.execute("SELECT email, name, blood_group FROM donor WHERE is_available = 1")
                recipients = [{'email': row[0], 'name': row[1], 'blood_group': row[2]} for row in cursor.fetchall()]
                filter_desc = "all available donors"
            elif alert_type == 'specific_blood_group':
                cursor.execute("SELECT email, name, blood_group FROM donor WHERE blood_group = ? AND is_available = 1", (blood_group,))
                recipients = [{'email': row[0], 'name': row[1], 'blood_group': row[2]} for row in cursor.fetchall()]
                filter_desc = f"donors with blood group {blood_group}"
            elif alert_type == 'blood_banks':
                cursor.execute("SELECT email, name FROM blood_banker")
                recipients = [{'email': row[0], 'name': row[1]} for row in cursor.fetchall()]
                filter_desc = "all blood banks"
            elif alert_type == 'hospitals':
                cursor.execute("SELECT email, name FROM hospital")
                recipients = [{'email': row[0], 'name': row[1]} for row in cursor.fetchall()]
                filter_desc = "all hospitals"
            else:
                flash('Invalid alert type!', 'error')
                return render_template('admin_send_alerts.html')
            
            if not recipients:
                flash('No recipients found for the selected criteria!', 'warning')
                return render_template('admin_send_alerts.html')
            
            # Send emails in background
            total_recipients = send_bulk_emails(recipients, subject, message)
            
            flash(f'✅ Alert sent to {total_recipients} {filter_desc}! Emails are being processed in background.', 'success')
            return redirect(url_for('admin_dashboard'))
            
        except Exception as e:
            flash(f'Failed to send alerts: {str(e)}', 'error')
        finally:
            conn.close()
    
    return render_template('admin_send_alerts.html')

@app.route('/admin/email_logs')
def admin_email_logs():
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    email_logs = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ea.*,
                        CASE
                            WHEN ea.sender_type = 'admin' THEN 'System Admin'
                            WHEN ea.sender_type = 'hospital' THEN h.name
                            ELSE ea.sender_type
                        END as sender_name,
                        CASE
                            WHEN ea.recipient_type = 'donor' THEN d.name
                            WHEN ea.recipient_type = 'blood_bank' THEN bb.name
                            ELSE ea.recipient_type
                        END as recipient_name
                FROM email_alerts ea
                LEFT JOIN hospital h ON ea.sender_id = h.id AND ea.sender_type = 'hospital'
                LEFT JOIN donor d ON ea.recipient_email = d.email AND ea.recipient_type = 'donor'
                LEFT JOIN blood_banker bb ON ea.recipient_email = bb.email AND ea.recipient_type = 'blood_bank'
                ORDER BY ea.created_at DESC
                LIMIT 100
            """)
            logs = cursor.fetchall()
            for log in logs:
                email_logs.append({
                    'id': log[0],
                    'sender_type': log[1],
                    'sender_name': log[9] if len(log) > 9 and log[9] else 'N/A', # Added check for index existence and None
                    'recipient_type': log[3],
                    'recipient_email': log[4],
                    'recipient_name': log[10] if len(log) > 10 and log[10] else 'N/A', # Added check for index existence and None
                    'subject': log[5],
                    'blood_group': log[7],
                    'status': log[8],
                    'created_at': log[9] if len(log) > 9 and log[9] else 'N/A'
                })
        except Exception as e:
            print(f"Error fetching email logs: {e}")
        finally:
            conn.close()
    
    return render_template('admin_email_logs.html', email_logs=email_logs)


# ------------------------------------------------------------------------------
# NEW ADMIN MANAGEMENT ROUTES
# ------------------------------------------------------------------------------

# Admin Hospital Management
@app.route('/admin/hospitals')
def admin_hospitals():
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    hospitals = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM hospital ORDER BY created_at DESC")
            hospital_rows = cursor.fetchall()
            for row in hospital_rows:
                hospitals.append({
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'license_number': row[4],
                    'phone': row[5],
                    'address': row[6],
                    'specialties': row[7],
                    'created_at': row[8]
                })
        except Exception as e:
            print(f"Error fetching hospitals: {e}")
        finally:
            conn.close()
    
    return render_template('admin_hospitals.html', hospitals=hospitals)

@app.route('/admin/delete_hospital/<int:hospital_id>')
def delete_hospital(hospital_id):
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Delete hospital and associated patients (and possibly blood requests)
            cursor.execute("DELETE FROM patient WHERE hospital_id = ?", (hospital_id,))
            cursor.execute("DELETE FROM blood_requests WHERE hospital_id = ?", (hospital_id,))
            cursor.execute("DELETE FROM hospital WHERE id = ?", (hospital_id,))
            conn.commit()
            flash('Hospital deleted successfully!', 'success')
        except Exception as e:
            flash(f'Failed to delete hospital: {str(e)}', 'error')
        finally:
            conn.close()
    
    return redirect(url_for('admin_hospitals'))

# Admin Blood Bankers Management
@app.route('/admin/blood_bankers')
def admin_blood_bankers():
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    blood_bankers = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM blood_banker ORDER BY created_at DESC")
            banker_rows = cursor.fetchall()
            for row in banker_rows:
                blood_bankers.append({
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'bank_name': row[4],
                    'license_number': row[5],
                    'phone': row[6],
                    'address': row[7],
                    'created_at': row[8]
                })
        except Exception as e:
            print(f"Error fetching blood bankers: {e}")
        finally:
            conn.close()
    
    return render_template('admin_blood_bankers.html', blood_bankers=blood_bankers)

@app.route('/admin/delete_blood_banker/<int:banker_id>')
def delete_blood_banker(banker_id):
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM blood_banker WHERE id = ?", (banker_id,))
            conn.commit()
            flash('Blood banker deleted successfully!', 'success')
        except Exception as e:
            flash(f'Failed to delete blood banker: {str(e)}', 'error')
        finally:
            conn.close()
    
    return redirect(url_for('admin_blood_bankers'))

# Admin Patients Management
@app.route('/admin/patients')
def admin_patients():
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    patients = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, h.name as hospital_name
                FROM patient p
                LEFT JOIN hospital h ON p.hospital_id = h.id
                ORDER BY p.requested_date DESC
            """)
            patient_rows = cursor.fetchall()
            for row in patient_rows:
                
                requested_date_str = row[9]
                formatted_date = requested_date_str

                if requested_date_str:
                    try:
                        dt_object = datetime.strptime(requested_date_str, '%Y-%m-%d %H:%M:%S')
                        formatted_date = dt_object.strftime('%Y-%m-%d %H:%M')
                    except ValueError:
                        pass # Keep original string if parsing fails
                        
                patients.append({
                    'id': row[0],
                    'name': row[1],
                    'hospital_id': row[2],
                    'blood_group': row[3],
                    'age': row[4],
                    'gender': row[5],
                    'required_quantity_ml': row[6],
                    'urgency_level': row[7],
                    'status': row[8],
                    'requested_date': formatted_date,
                    'hospital_name': row[10] if row[10] else 'Unknown Hospital'
                })
        except Exception as e:
            print(f"Error fetching patients: {e}")
        finally:
            conn.close()
    
    return render_template('admin_patients.html', patients=patients)

@app.route('/admin/delete_patient/<int:patient_id>')
def delete_patient(patient_id):
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM patient WHERE id = ?", (patient_id,))
            conn.commit()
            flash('Patient deleted successfully!', 'success')
        except Exception as e:
            flash(f'Failed to delete patient: {str(e)}', 'error')
        finally:
            conn.close()
    
    return redirect(url_for('admin_patients'))

# Admin Interested Donors
@app.route('/admin/interested_donors')
def admin_interested_donors():
    if 'admin_id' not in session:
        flash('Please login as admin first!', 'error')
        return redirect(url_for('admin_login'))
    
    conn = get_db_connection()
    donors = []
    # Filters
    min_age = request.args.get('min_age', 18, type=int)
    max_age = request.args.get('max_age', 65, type=int)
    gender = request.args.get('gender', '')
    blood_group = request.args.get('blood_group', '')

    if conn:
        try:
            cursor = conn.cursor()
            
            # Build query
            query = """
                SELECT d.*, di.interest_status, di.updated_at
                FROM donor d
                LEFT JOIN donor_interests di ON d.id = di.donor_id
                WHERE d.is_available = 1
                AND di.interest_status = 'interested'
                AND d.age BETWEEN ? AND ?
            """
            params = [min_age, max_age]
            
            if gender:
                query += " AND d.gender = ?"
                params.append(gender)
            
            if blood_group:
                query += " AND d.blood_group = ?"
                params.append(blood_group)
            
            query += " ORDER BY di.updated_at DESC"
            
            cursor.execute(query, params)
            donor_rows = cursor.fetchall()
            for row in donor_rows:
                donors.append({
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'blood_group': row[4],
                    'age': row[5],
                    'gender': row[6],
                    'weight': row[7],
                    'phone': row[8],
                    'address': row[9],
                    'is_available': row[11],
                    # Fields from donor_interests table (indexes 12, 13, 14 from original query)
                    'is_interested': row[12],
                    'interest_status': row[13],
                    'updated_at': row[14]
                })
        except Exception as e:
            print(f"Error fetching interested donors: {e}")
        finally:
            conn.close()
    
    return render_template('admin_interested_donors.html',
                           donors=donors,
                           filters={
                               'min_age': min_age,
                               'max_age': max_age,
                               'gender': gender,
                               'blood_group': blood_group
                           })

# Send Appointment to Donor (API endpoint)
@app.route('/admin/send_appointment/<int:donor_id>', methods=['POST'])
def send_appointment(donor_id):
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Please login as admin first!'})
    
    appointment_date = request.json.get('appointment_date')
    appointment_time = request.json.get('appointment_time')
    location = request.json.get('location')
    message = request.json.get('message', '')
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get donor details
            cursor.execute("SELECT name, email, blood_group FROM donor WHERE id = ?", (donor_id,))
            donor = cursor.fetchone()
            
            if not donor:
                return jsonify({'success': False, 'message': 'Donor not found!'})
            
            donor_name, donor_email, blood_group = donor
            
            # Send appointment email
            subject = f"📅 Blood Donation Appointment - {appointment_date}"
            email_message = f"""
            <html>
            <body>
                <h2 style="color: #007bff;">BLOOD DONATION APPOINTMENT</h2>
                <p><strong>Dear {donor_name},</strong></p>
                <p>Thank you for your interest in blood donation! We have scheduled an appointment for you.</p>
                
                <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <h4 style="color: #28a745;">Appointment Details:</h4>
                    <p><strong>Date:</strong> {appointment_date}</p>
                    <p><strong>Time:</strong> {appointment_time}</p>
                    <p><strong>Location:</strong> {location}</p>
                    <p><strong>Blood Group:</strong> <span style="color: #dc3545; font-weight: bold;">{blood_group}</span></p>
                </div>
                
                <p><strong>Additional Information:</strong></p>
                <p>{message}</p>
                
                <hr>
                <p style="color: #6c757d;">
                    <strong>Please remember to:</strong><br>
                    - Get adequate sleep the night before<br>
                    - Eat a healthy meal before donating<br>
                    - Drink plenty of water<br>
                    - Bring a valid ID
                </p>
                
                <p>If you need to reschedule, please contact us at least 24 hours in advance.</p>
                
                <p style="color: #dc3545; font-weight: bold;">Your donation can save up to 3 lives!</p>
                
                <p>Thank you for your lifesaving contribution!</p>
                <p><em>BloodChain Management Team</em></p>
            </body>
            </html>
            """
            
            if email_config.send_email(donor_email, subject, email_message):
                # Log the appointment
                cursor.execute("""
                    INSERT INTO donor_appointments
                    (donor_id, appointment_date, appointment_time, location, message, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (donor_id, appointment_date, appointment_time, location, message, 'Scheduled'))
                
                conn.commit()
                return jsonify({'success': True, 'message': 'Appointment sent successfully!'})
            else:
                return jsonify({'success': False, 'message': 'Failed to send email!'})
                
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error: {str(e)}'})
        finally:
            conn.close()
    
    return jsonify({'success': False, 'message': 'Database connection failed!'})

# ------------------------------------------------------------------------------
# NEW EMAIL API ROUTES
# ------------------------------------------------------------------------------

@app.route('/admin/send_donor_emails', methods=['POST'])
def send_donor_emails():
    """API endpoint for admin to send bulk personalized emails to selected donors."""
    if 'admin_id' not in session:
        return jsonify({'success': False, 'message': 'Please login as admin first!'})
    
    # Get data from JSON payload
    donor_ids = request.json.get('donor_ids', [])
    subject = request.json.get('subject', '')
    message = request.json.get('message', '') # Expects {donor_name} placeholder
    
    if not donor_ids or not subject or not message:
        return jsonify({'success': False, 'message': 'Missing required fields!'})
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed!'})
    
    try:
        cursor = conn.cursor()
        
        # Validate and convert donor IDs to a tuple of integers for a secure SQL query
        try:
            donor_ids_int = [int(id) for id in donor_ids]
            if not donor_ids_int:
                return jsonify({'success': False, 'message': 'No valid donor IDs provided.'})
            donor_ids_tuple = tuple(donor_ids_int)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid donor ID format.'})
            
        placeholders = ','.join('?' * len(donor_ids_tuple))
        
        # Fetch donor details: id, name, email
        cursor.execute(f"SELECT id, name, email, blood_group FROM donor WHERE id IN ({placeholders})", donor_ids_tuple)
        donors = cursor.fetchall()
        
        if not donors:
            return jsonify({'success': False, 'message': 'No matching donors found.'})

        # Prepare recipients list for background sending
        recipients = []
        
        for donor in donors:
            donor_id, donor_name, donor_email, blood_group = donor
            # Personalize the message with the donor's name
            personalized_message = message.replace('{donor_name}', donor_name)
            
            recipients.append({
                'email': donor_email, 
                'name': donor_name, 
                'blood_group': blood_group,
                'subject': subject,
                'message': personalized_message
            })

        # Helper function for threaded email sending (logs within the thread)
        def send_personalized_emails_in_background(emails_to_send, admin_id):
            conn_bg = get_db_connection()
            if not conn_bg:
                print("❌ Background thread: Failed to connect to database for logging.")
                return

            success_count = 0
            failed_count = 0
            
            for email_data in emails_to_send:
                # Use the personalized message for the email body
                if email_config.send_email(email_data['email'], email_data['subject'], email_data['message']):
                    success_count += 1
                    # Note: We must fetch the blood_group from the email_data dict if needed for log_email_alert
                    log_email_alert('admin', admin_id, 'donor', email_data['email'], email_data['subject'], email_data['message'], email_data.get('blood_group'), 'Sent')
                else:
                    failed_count += 1
                    log_email_alert('admin', admin_id, 'donor', email_data['email'], email_data['subject'], email_data['message'], email_data.get('blood_group'), 'Failed')
            
            conn_bg.close()
            print(f"📧 Personalized Email campaign completed: {success_count} sent, {failed_count} failed")
        
        # Run in a background thread
        thread = threading.Thread(target=send_personalized_emails_in_background, args=(recipients, session['admin_id']))
        thread.daemon = True
        thread.start()
        
        total_recipients = len(recipients)
        return jsonify({
            'success': True, 
            'message': f'Emails to {total_recipients} donors are being processed in the background.'
        })
        
    except Exception as e:
        print(f"❌ Error in send_donor_emails route: {e}")
        return jsonify({'success': False, 'message': f'Error processing request: {str(e)}'})
    finally:
        if conn:
            conn.close()

# ==============================================================================
# BLOOD BANKER ROUTES
# ==============================================================================

# Blood Bank Registration
@app.route('/blood_banker/register', methods=['GET', 'POST'])
def blood_banker_registration():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        bank_name = request.form['bank_name']
        license_number = request.form['license_number']
        phone = request.form['phone']
        address = request.form['address']
        
        print(f"🔸 Attempting to register blood bank: {bank_name}, {email}")
        
        conn = get_db_connection()
        if conn is None:
            flash('❌ Database connection failed.', 'error')
            return render_template('blood_banker_registration.html')
        
        try:
            cursor = conn.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT id FROM blood_banker WHERE email = ?", (email,))
            existing_banker = cursor.fetchone()
            
            if existing_banker:
                flash('❌ Email already registered. Please use a different email.', 'error')
                return render_template('blood_banker_registration.html')
            
            # Check if license number already exists
            cursor.execute("SELECT id FROM blood_banker WHERE license_number = ?", (license_number,))
            existing_license = cursor.fetchone()
            
            if existing_license:
                flash('❌ License number already registered.', 'error')
                return render_template('blood_banker_registration.html')
            
            # Insert new blood banker
            cursor.execute("""
                INSERT INTO blood_banker (name, email, password, bank_name, license_number, phone, address)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, email, hash_password(password), bank_name, license_number, phone, address))
            
            # Get the inserted banker ID
            banker_id = cursor.lastrowid
            
            # Add to blockchain
            block_data = {
                'type': 'blood_bank_registration',
                'banker_id': banker_id,
                'bank_name': bank_name,
                'email': email,
                'license_number': license_number,
                'timestamp': str(datetime.now())
            }
            blockchain_hash = blood_donation_blockchain.add_block(block_data)
            
            conn.commit()
            print(f"✅ Blood bank registered successfully: {bank_name} (ID: {banker_id})")
            
            flash('✅ Blood bank registration successful! You can now login.', 'success')
            return redirect(url_for('blood_banker_login'))
            
        except sqlite3.IntegrityError as e:
            flash('❌ Registration failed. Email or license number already exists.', 'error')
            print(f"❌ Integrity error: {e}")
        except Exception as e:
            flash(f'❌ Registration failed: {str(e)}', 'error')
            print(f"❌ Registration error: {e}")
        finally:
            conn.close()
    
    return render_template('blood_banker_registration.html')

@app.route('/blood_banker/login', methods=['GET', 'POST'])
def blood_banker_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM blood_banker WHERE email = ? AND password = ?",
                             (email, hash_password(password)))
                banker = cursor.fetchone()
                
                if banker:
                    session['banker_id'] = banker[0]
                    session['banker_name'] = banker[1]
                    session['banker_bank_name'] = banker[4]
                    flash('Blood banker login successful!', 'success')
                    return redirect(url_for('blood_banker_dashboard'))
                else:
                    flash('Invalid blood banker credentials!', 'error')
            except Exception as e:
                flash(f'Login error: {str(e)}', 'error')
            finally:
                conn.close()
        else:
            flash('Database connection failed!', 'error')
    
    return render_template('blood_banker_login.html')

@app.route('/blood_banker/dashboard')
def blood_banker_dashboard():
    if 'banker_id' not in session:
        flash('Please login as blood banker first!', 'error')
        return redirect(url_for('blood_banker_login'))
    
    conn = get_db_connection()
    stats = {}
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT blood_group, SUM(quantity_ml) as total FROM blood_inventory WHERE status = 'Available' GROUP BY blood_group")
            blood_data = cursor.fetchall()
            stats['blood_inventory'] = [{'blood_group': row[0], 'total': row[1] or 0} for row in blood_data]
            
            cursor.execute("SELECT COUNT(*) as count FROM donor")
            stats['total_donors'] = cursor.fetchone()[0]
            
        except Exception as e:
            print(f"Error fetching banker stats: {e}")
            stats = {
                'blood_inventory': [],
                'total_donors': 0
            }
        finally:
            conn.close()
    
    return render_template('blood_banker.html', stats=stats)


# ==============================================================================
# HOSPITAL ROUTES
# ==============================================================================

# Hospital Registration
@app.route('/hospital/register', methods=['GET', 'POST'])
def hospital_registration():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        license_number = request.form['license_number']
        phone = request.form['phone']
        address = request.form['address']
        specialties = request.form.get('specialties', '')
        
        print(f"🔸 Attempting to register hospital: {name}, {email}")
        
        conn = get_db_connection()
        if conn is None:
            flash('❌ Database connection failed.', 'error')
            return render_template('hospital_registration.html')
        
        try:
            cursor = conn.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT id FROM hospital WHERE email = ?", (email,))
            existing_hospital = cursor.fetchone()
            
            if existing_hospital:
                flash('❌ Email already registered. Please use a different email.', 'error')
                return render_template('hospital_registration.html')
            
            # Check if license number already exists
            cursor.execute("SELECT id FROM hospital WHERE license_number = ?", (license_number,))
            existing_license = cursor.fetchone()
            
            if existing_license:
                flash('❌ License number already registered.', 'error')
                return render_template('hospital_registration.html')
            
            # Insert new hospital
            cursor.execute("""
                INSERT INTO hospital (name, email, password, license_number, phone, address, specialties)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, email, hash_password(password), license_number, phone, address, specialties))
            
            # Get the inserted hospital ID
            hospital_id = cursor.lastrowid
            
            # Add to blockchain
            block_data = {
                'type': 'hospital_registration',
                'hospital_id': hospital_id,
                'hospital_name': name,
                'email': email,
                'license_number': license_number,
                'timestamp': str(datetime.now())
            }
            blockchain_hash = blood_donation_blockchain.add_block(block_data)
            
            conn.commit()
            print(f"✅ Hospital registered successfully: {name} (ID: {hospital_id})")
            
            flash('✅ Hospital registration successful! You can now login.', 'success')
            return redirect(url_for('hospital_login'))
            
        except sqlite3.IntegrityError as e:
            flash('❌ Registration failed. Email or license number already exists.', 'error')
            print(f"❌ Integrity error: {e}")
        except Exception as e:
            flash(f'❌ Registration failed: {str(e)}', 'error')
            print(f"❌ Registration error: {e}")
        finally:
            conn.close()
    
    return render_template('hospital_registration.html')

@app.route('/hospital/login', methods=['GET', 'POST'])
def hospital_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM hospital WHERE email = ? AND password = ?",
                             (email, hash_password(password)))
                hospital = cursor.fetchone()
                
                if hospital:
                    session['hospital_id'] = hospital[0]
                    session['hospital_name'] = hospital[1]
                    flash('Hospital login successful!', 'success')
                    return redirect(url_for('hospital_dashboard'))
                else:
                    flash('Invalid hospital credentials!', 'error')
            except Exception as e:
                flash(f'Login error: {str(e)}', 'error')
            finally:
                conn.close()
        else:
            flash('Database connection failed!', 'error')
    
    return render_template('hospital_login.html')

@app.route('/hospital/dashboard')
def hospital_dashboard():
    if 'hospital_id' not in session:
        flash('Please login as hospital first!', 'error')
        return redirect(url_for('hospital_login'))
    
    return render_template('hospital.html')

@app.route('/feed/patient', methods=['GET', 'POST'])
def feed_patient():
    if 'hospital_id' not in session:
        flash('Please login as hospital first!', 'error')
        return redirect(url_for('hospital_login'))
    
    if request.method == 'POST':
        name = request.form['name']
        blood_group = request.form['blood_group']
        age = request.form['age']
        gender = request.form['gender']
        required_quantity = request.form['required_quantity']
        urgency_level = request.form['urgency_level']
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO patient (name, hospital_id, blood_group, age, gender, required_quantity_ml, urgency_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (name, session['hospital_id'], blood_group, int(age), gender, int(required_quantity), urgency_level))
                
                patient_id = cursor.lastrowid
                conn.commit()
                
                # Send blood request alerts
                if urgency_level in ['High', 'Critical']:
                    # Run in background thread
                    def send_alerts():
                        send_blood_request_alert(
                            session['hospital_id'],
                            name,
                            blood_group,
                            required_quantity,
                            urgency_level
                        )
                    
                    thread = threading.Thread(target=send_alerts)
                    thread.daemon = True
                    thread.start()
                    
                    flash('Patient details added successfully! Blood request alerts have been sent to matching donors and blood banks.', 'success')
                else:
                    flash('Patient details added successfully!', 'success')
                
                return redirect(url_for('view_patients'))
            except Exception as e:
                flash(f'Failed to add patient: {str(e)}', 'error')
                print(f"❌ Patient registration error: {e}")
            finally:
                conn.close()
        else:
            flash('Database connection failed!', 'error')
    
    return render_template('feed_patient.html')


# Hospital Blood Request to Admin
@app.route('/hospital/send_blood_request', methods=['GET', 'POST'])
def hospital_send_blood_request():
    if 'hospital_id' not in session:
        flash('Please login as hospital first!', 'error')
        return redirect(url_for('hospital_login'))
    
    if request.method == 'POST':
        blood_group = request.form['blood_group']
        quantity = request.form['quantity']
        urgency_level = request.form['urgency_level']
        message = request.form['message']
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Get hospital info
                cursor.execute("SELECT name FROM hospital WHERE id = ?", (session['hospital_id'],))
                hospital = cursor.fetchone()
                hospital_name = hospital[0] if hospital else "Unknown Hospital"
                
                # Create blood request record
                cursor.execute("""
                    INSERT INTO blood_requests
                    (hospital_id, blood_group, quantity_ml, urgency_level, message, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (session['hospital_id'], blood_group, quantity, urgency_level, message, 'Pending'))
                
                request_id = cursor.lastrowid
                
                # Send email to admin
                subject = f"🚨 Blood Request from {hospital_name} - {blood_group}"
                email_message = f"""
                <html>
                <body>
                    <h2 style="color: #dc3545;">NEW BLOOD REQUEST</h2>
                    <p><strong>Hospital:</strong> {hospital_name}</p>
                    <p><strong>Blood Group Required:</strong> <span style="color: #dc3545; font-weight: bold;">{blood_group}</span></p>
                    <p><strong>Quantity Needed:</strong> {quantity} ml</p>
                    <p><strong>Urgency Level:</strong> {urgency_level}</p>
                    <p><strong>Additional Message:</strong> {message}</p>
                    <p><strong>Request Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <hr>
                    <p style="color: #6c757d;">Please review this request in the admin dashboard.</p>
                </body>
                </html>
                """
                
                # Send to admin (you can add multiple admin emails)
                admin_emails = ['admin@blooddonation.com']  # Add more admin emails as needed
                for admin_email in admin_emails:
                    if email_config.send_email(admin_email, subject, email_message):
                        log_email_alert('hospital', session['hospital_id'], 'admin', admin_email, subject, email_message, blood_group)
                
                conn.commit()
                flash('Blood request sent to admin successfully!', 'success')
                return redirect(url_for('hospital_dashboard'))
                
            except Exception as e:
                flash(f'Failed to send blood request: {str(e)}', 'error')
                print(f"❌ Blood request error: {e}")
            finally:
                conn.close()
        else:
            flash('Database connection failed!', 'error')
    
    return render_template('hospital_send_request.html')


# ==============================================================================
# DONOR ROUTES
# ==============================================================================

@app.route('/donor/register', methods=['GET', 'POST'])
def donor_registration():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        blood_group = request.form['blood_group']
        age = request.form['age']
        gender = request.form['gender']
        weight = request.form['weight']
        phone = request.form['phone']
        address = request.form['address']
        
        print(f"🔸 Attempting to register donor: {name}, {email}")
        
        conn = get_db_connection()
        if conn is None:
            flash('❌ Database connection failed.', 'error')
            return render_template('donor_registration.html')
        
        try:
            cursor = conn.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT id FROM donor WHERE email = ?", (email,))
            existing_donor = cursor.fetchone()
            
            if existing_donor:
                flash('❌ Email already registered. Please use a different email or login.', 'error')
                return render_template('donor_registration.html')
            
            # Insert new donor
            cursor.execute("""
                INSERT INTO donor (name, email, password, blood_group, age, gender, weight, phone, address)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, email, hash_password(password), blood_group, int(age), gender, float(weight), phone, address))
            
            # Get the inserted donor ID
            donor_id = cursor.lastrowid
            
            # Add to blockchain
            block_data = {
                'type': 'donor_registration',
                'donor_id': donor_id,
                'donor_name': name,
                'email': email,
                'blood_group': blood_group,
                'timestamp': str(datetime.now())
            }
            blockchain_hash = blood_donation_blockchain.add_block(block_data)
            
            conn.commit()
            print(f"✅ Donor registered successfully: {name} (ID: {donor_id})")
            
            flash('✅ Registration successful! You can now login.', 'success')
            return redirect(url_for('donor_login'))
            
        except sqlite3.IntegrityError as e:
            flash('❌ Email already exists. Please use a different email.', 'error')
            print(f"❌ Integrity error: {e}")
        except Exception as e:
            flash(f'❌ Registration failed: {str(e)}', 'error')
            print(f"❌ Registration error: {e}")
        finally:
            conn.close()
    
    return render_template('donor_registration.html')

@app.route('/donor/login', methods=['GET', 'POST'])
def donor_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM donor WHERE email = ? AND password = ?",
                             (email, hash_password(password)))
                donor = cursor.fetchone()
                
                if donor:
                    session['donor_id'] = donor[0]
                    session['donor_name'] = donor[1]
                    flash('Login successful!', 'success')
                    return redirect(url_for('donor_details'))
                else:
                    flash('Invalid email or password!', 'error')
            except Exception as e:
                flash(f'Login error: {str(e)}', 'error')
            finally:
                conn.close()
        else:
            flash('Database connection failed!', 'error')
    
    return render_template('donor_login.html')

@app.route('/donor/details')
def donor_details():
    if 'donor_id' not in session:
        flash('Please login as donor first!', 'error')
        return redirect(url_for('donor_login'))
    
    conn = get_db_connection()
    donor_info = None
    donation_history = []
    
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get donor information
            cursor.execute("SELECT * FROM donor WHERE id = ?", (session['donor_id'],))
            donor_row = cursor.fetchone()
            if donor_row:
                donor_info = {
                    'id': donor_row[0],
                    'name': donor_row[1],
                    'email': donor_row[2],
                    'blood_group': donor_row[4],
                    'age': donor_row[5],
                    'gender': donor_row[6],
                    'weight': donor_row[7],
                    'phone': donor_row[8],
                    'address': donor_row[9],
                    'is_available': donor_row[11]
                }
            
            # Get donation history
            cursor.execute("SELECT * FROM blood_inventory WHERE donor_id = ? ORDER BY collection_date DESC", (session['donor_id'],))
            donations = cursor.fetchall()
            for donation in donations:
                donation_history.append({
                    'id': donation[0],
                    'blood_group': donation[1],
                    'quantity_ml': donation[2],
                    'collection_date': donation[5],
                    'expiry_date': donation[6],
                    'status': donation[7],
                    'blockchain_hash': donation[8]
                })
            
        except Exception as e:
            print(f"Error fetching donor details: {e}")
        finally:
            conn.close()
    
    return render_template('donor_details.html', donor=donor_info, donations=donation_history)

@app.route('/provide_blood', methods=['GET', 'POST'])
def provide_blood():
    if 'donor_id' not in session:
        flash('Please login as donor first!', 'error')
        return redirect(url_for('donor_login'))
    
    if request.method == 'POST':
        blood_group = request.form['blood_group']
        quantity = request.form['quantity']
        collection_date = request.form['collection_date']
        
        # Calculate expiry date (42 days from collection)
        expiry_date = (datetime.strptime(collection_date, '%Y-%m-%d') + timedelta(days=42)).strftime('%Y-%m-%d')
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # Add to blood inventory
                cursor.execute("""
                    INSERT INTO blood_inventory (blood_group, quantity_ml, donor_id, collection_date, expiry_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (blood_group, int(quantity), session['donor_id'], collection_date, expiry_date))
                
                # Add to blockchain
                block_data = {
                    'type': 'blood_donation',
                    'donor_id': session['donor_id'],
                    'donor_name': session['donor_name'],
                    'blood_group': blood_group,
                    'quantity_ml': quantity,
                    'collection_date': collection_date,
                    'expiry_date': expiry_date,
                    'timestamp': str(datetime.now())
                }
                blockchain_hash = blood_donation_blockchain.add_block(block_data)
                
                # Update blockchain hash in database
                inventory_id = cursor.lastrowid
                cursor.execute("UPDATE blood_inventory SET blockchain_hash = ? WHERE id = ?",
                             (blockchain_hash, inventory_id))
                
                conn.commit()
                flash('Blood donation recorded successfully on blockchain!', 'success')
                return redirect(url_for('donor_details'))
                
            except Exception as e:
                flash(f'Donation failed: {str(e)}', 'error')
                print(f"❌ Donation error: {e}")
            finally:
                conn.close()
        else:
            flash('Database connection failed!', 'error')
    
    return render_template('provide_blood.html')

# Donor Interest System (API endpoint)
@app.route('/donor/express_interest', methods=['POST'])
def donor_express_interest():
    if 'donor_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first!'})
    
    # Expecting JSON payload: {'interest': 'interested' or 'not_interested'}
    interest = request.json.get('interest')
    
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Update donor availability status in the main table
            is_available_int = 1 if interest == 'interested' else 0
            cursor.execute("UPDATE donor SET is_available = ? WHERE id = ?", (is_available_int, session['donor_id']))
            
            # Log/update interest in donor_interests table
            cursor.execute("""
                INSERT OR REPLACE INTO donor_interests
                (donor_id, interest_status, updated_at)
                VALUES (?, ?, ?)
            """, (session['donor_id'], interest, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            conn.commit()
            
            # If interested, send notification to admin (optional, can be done asynchronously)
            if interest == 'interested':
                cursor.execute("SELECT name, email, blood_group FROM donor WHERE id = ?", (session['donor_id'],))
                donor = cursor.fetchone()
                if donor:
                    subject = f"🎯 New Interested Donor - {donor[0]}"
                    message = f"""
                    <html>
                    <body>
                        <h2 style="color: #28a745;">NEW INTERESTED DONOR</h2>
                        <p><strong>Donor Name:</strong> {donor[0]}</p>
                        <p><strong>Blood Group:</strong> <span style="color: #dc3545; font-weight: bold;">{donor[2]}</span></p>
                        <p><strong>Email:</strong> {donor[1]}</p>
                        <p><strong>Expressed Interest:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <hr>
                        <p style="color: #6c757d;">This donor is available for blood donation appointments. Check /admin/interested_donors.</p>
                    </body>
                    </html>
                    """
                    admin_emails = ['admin@blooddonation.com']
                    # Send in background to avoid blocking the API response
                    threading.Thread(target=send_bulk_emails, args=([{'email': ae} for ae in admin_emails], subject, message)).start()

            
            return jsonify({'success': True, 'message': f'Thank you for your response! ({interest})', 'new_status': is_available_int})
            
        except Exception as e:
            print(f"❌ Donor interest error: {e}")
            return jsonify({'success': False, 'message': f'Error: {str(e)}'})
        finally:
            conn.close()
    
    return jsonify({'success': False, 'message': 'Database connection failed!'})

# ==============================================================================
# GENERAL VIEW ROUTES
# ==============================================================================

@app.route('/view/donors')
def view_donors():
    conn = get_db_connection()
    donors = []
    if conn:
        try:
            cursor = conn.cursor()
            
            # Get filter parameters
            min_age = request.args.get('min_age', '', type=str)
            max_age = request.args.get('max_age', '', type=str)
            blood_group = request.args.get('blood_group', '')
            gender = request.args.get('gender', '')
            availability = request.args.get('availability', '')
            
            # Build query with filters
            query = "SELECT id, name, blood_group, age, gender, phone, is_available FROM donor WHERE 1=1"
            params = []
            
            if min_age:
                query += " AND age >= ?"
                params.append(int(min_age))
            
            if max_age:
                query += " AND age <= ?"
                params.append(int(max_age))
            
            if blood_group:
                query += " AND blood_group = ?"
                params.append(blood_group)
            
            if gender:
                query += " AND gender = ?"
                params.append(gender)
            
            if availability:
                if availability == 'available':
                    query += " AND is_available = 1"
                elif availability == 'not_available':
                    query += " AND is_available = 0"
            
            query += " ORDER BY name ASC"
            
            cursor.execute(query, params)
            donor_rows = cursor.fetchall()
            for row in donor_rows:
                donors.append({
                    'id': row[0],
                    'name': row[1],
                    'blood_group': row[2],
                    'age': row[3],
                    'gender': row[4],
                    'phone': row[5],
                    'is_available': row[6]
                })
        except Exception as e:
            print(f"Error fetching donors: {e}")
        finally:
            conn.close()
    
    return render_template('view_donors.html', donors=donors)

@app.route('/view/blood')
def view_blood():
    conn = get_db_connection()
    blood_inventory = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT bi.*, d.name as donor_name
                FROM blood_inventory bi
                LEFT JOIN donor d ON bi.donor_id = d.id
                WHERE bi.status = 'Available'
                ORDER BY bi.expiry_date ASC
            """)
            blood_rows = cursor.fetchall()
            for row in blood_rows:
                blood_inventory.append({
                    'id': row[0],
                    'blood_group': row[1],
                    'quantity_ml': row[2],
                    'donor_id': row[3],
                    'collection_date': row[5],
                    'expiry_date': row[6],
                    'status': row[7],
                    'blockchain_hash': row[8],
                    'donor_name': row[9] if row[9] else 'Unknown'
                })
        except Exception as e:
            print(f"Error fetching blood inventory: {e}")
        finally:
            conn.close()
    
    return render_template('view_blood.html', blood_inventory=blood_inventory)

@app.route('/view/patients')
def view_patients():
    conn = get_db_connection()
    patients = []
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.*, h.name as hospital_name
                FROM patient p
                LEFT JOIN hospital h ON p.hospital_id = h.id
                ORDER BY p.requested_date DESC
            """)
            patient_rows = cursor.fetchall()
            for row in patient_rows:
                
                # --- FIX FOR 'str object' has no attribute 'strptime' ---
                requested_date_str = row[9]
                formatted_date = requested_date_str

                if requested_date_str:
                    try:
                        # Attempt to parse the date string (e.g., 'YYYY-MM-DD HH:MM:SS')
                        dt_object = datetime.strptime(requested_date_str, '%Y-%m-%d %H:%M:%S')
                        # Format it to a display string (e.g., '2025-11-17 10:45')
                        formatted_date = dt_object.strftime('%Y-%m-%d %H:%M')
                    except ValueError:
                        # Keep the original string if parsing fails
                        pass

                patients.append({
                    'id': row[0],
                    'name': row[1],
                    'hospital_id': row[2],
                    'blood_group': row[3],
                    'age': row[4],
                    'gender': row[5],
                    'required_quantity_ml': row[6],
                    'urgency_level': row[7],
                    'status': row[8],
                    'requested_date': formatted_date, # <-- Passing the formatted string
                    'hospital_name': row[10] if row[10] else 'Unknown Hospital'
                })
        except Exception as e:
            print(f"Error fetching patients: {e}")
        finally:
            conn.close()
    
    return render_template('view_patients.html', patients=patients)

# ==============================================================================
# API/UTILITY ROUTES
# ==============================================================================

@app.route('/blockchain/explorer')
def blockchain_explorer():
    if 'admin_id' not in session:
        flash('Admin access required!', 'error')
        return redirect(url_for('admin_login'))
    
    blocks = blood_donation_blockchain.get_all_blocks()
    return render_template('blockchain_explorer.html', blocks=blocks, chain_length=blood_donation_blockchain.get_chain_length())

@app.route('/api/blockchain/verify')
def verify_blockchain():
    is_valid = blood_donation_blockchain.is_chain_valid()
    return jsonify({
        'valid': is_valid,
        'chain_length': blood_donation_blockchain.get_chain_length(),
        'timestamp': str(datetime.now())
    })

@app.route('/api/stats')
def get_system_stats():
    conn = get_db_connection()
    stats = {}
    if conn:
        try:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM donor")
            stats['total_donors'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as count FROM blood_banker")
            stats['total_blood_bankers'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as count FROM hospital")
            stats['total_hospitals'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as count FROM patient")
            stats['total_patients'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) as count FROM blood_inventory WHERE status = 'Available'")
            stats['available_blood_units'] = cursor.fetchone()[0]
            
        except Exception as e:
            print(f"Error fetching stats: {e}")
        finally:
            conn.close()
    
    return jsonify(stats)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('index'))

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

# Context processor
@app.context_processor
def inject_today_date():
    return {'today': get_today_date()}

if __name__ == '__main__':
    print("🚀 Starting BloodChain Application...")
    print("📍 Access the application at: http://localhost:5000")
    print("🔑 Admin Login: admin / admin123")
    print("🏥 Hospital Registration: /hospital/register")
    print("🩸 Blood Bank Registration: /blood_banker/register")
    print("❤️ Donor Registration: /donor/register")
    print("📧 Email Alerts: Admin can send alerts to all users")
    print("🚨 Automatic Alerts: Hospitals trigger alerts for critical blood needs")
    print("=" * 50)
    app.run(debug=True, host='localhost', port=5000)