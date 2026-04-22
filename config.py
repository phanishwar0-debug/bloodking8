import sqlite3
import os
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def hash_password(password):
    """Consistent password hashing function"""
    return hashlib.sha256(password.encode()).hexdigest()

class EmailConfig:
    def __init__(self):
        # Email configuration - UPDATE THESE WITH YOUR CREDENTIALS
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = "fanishwarthannrru@gmail.com"  # ⬅️ CHANGE THIS
        self.sender_password = "biog ilnc nggp uygm"  # ⬅️ CHANGE THIS
        self.enabled = True  # Set to True after configuring email credentials
        
        # Test connection on initialization
        if self.enabled:
            self.test_connection()
    
    def test_connection(self):
        """Test email configuration and connection"""
        if not self.enabled:
            print("📧 Email system: Running in SIMULATION MODE")
            print("   To enable real emails, set enabled=True and configure credentials")
            return True
            
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.quit()
            print("✅ Email configuration: SUCCESS - Real emails will be sent")
            return True
        except Exception as e:
            print(f"❌ Email configuration: FAILED - {e}")
            print("   Switching to simulation mode")
            self.enabled = False
            return False
    
    def send_email(self, recipient_email, subject, message):
        """Send email to recipient"""
        if not self.enabled:
            # Simulation mode - just print the email details
            print(f"📧 [SIMULATION] Email to: {recipient_email}")
            print(f"   Subject: {subject}")
            print(f"   Message preview: {message[:100]}...")
            return True
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            
            # Add message body
            msg.attach(MIMEText(message, 'html'))
            
            # Create server connection
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            
            # Send email
            text = msg.as_string()
            server.sendmail(self.sender_email, recipient_email, text)
            server.quit()
            
            print(f"✅ Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email to {recipient_email}: {e}")
            return False

class DatabaseConfig:
    def __init__(self):
        self.database_path = 'blood_donation.db'
        self.init_database()
    
    def get_connection(self):
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            return conn
        except Exception as e:
            print(f"❌ SQLite connection error: {e}")
            return None
    
    def init_database(self):
        """Initialize SQLite database with tables"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Create tables
        tables = [
            # Admin table
            """
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # Blood Banker table
            """
            CREATE TABLE IF NOT EXISTS blood_banker (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                bank_name TEXT NOT NULL,
                license_number TEXT UNIQUE,
                address TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # Hospital table
            """
            CREATE TABLE IF NOT EXISTS hospital (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                license_number TEXT UNIQUE,
                address TEXT,
                phone TEXT,
                specialties TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # Donor table
            """
            CREATE TABLE IF NOT EXISTS donor (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                blood_group TEXT NOT NULL CHECK(blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
                age INTEGER NOT NULL,
                gender TEXT NOT NULL CHECK(gender IN ('Male', 'Female', 'Other')),
                weight REAL,
                phone TEXT,
                address TEXT,
                last_donation_date DATE,
                is_available BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # Blood Inventory table
            """
            CREATE TABLE IF NOT EXISTS blood_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                blood_group TEXT NOT NULL CHECK(blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
                quantity_ml INTEGER NOT NULL,
                donor_id INTEGER,
                blood_banker_id INTEGER,
                collection_date DATE NOT NULL,
                expiry_date DATE NOT NULL,
                status TEXT DEFAULT 'Available' CHECK(status IN ('Available', 'Used', 'Expired')),
                blockchain_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (donor_id) REFERENCES donor(id) ON DELETE SET NULL,
                FOREIGN KEY (blood_banker_id) REFERENCES blood_banker(id) ON DELETE SET NULL
            )
            """,
            # Patient table
            """
            CREATE TABLE IF NOT EXISTS patient (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                hospital_id INTEGER,
                blood_group TEXT NOT NULL CHECK(blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
                age INTEGER,
                gender TEXT CHECK(gender IN ('Male', 'Female', 'Other')),
                required_quantity_ml INTEGER NOT NULL,
                urgency_level TEXT DEFAULT 'Medium' CHECK(urgency_level IN ('Low', 'Medium', 'High', 'Critical')),
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Approved', 'Rejected', 'Completed')),
                requested_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hospital_id) REFERENCES hospital(id) ON DELETE SET NULL
            )
            """,
            # Email Alerts table
            """
            CREATE TABLE IF NOT EXISTS email_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_type TEXT NOT NULL CHECK(sender_type IN ('admin', 'hospital', 'system')),
                sender_id INTEGER,
                recipient_type TEXT NOT NULL CHECK(recipient_type IN ('donor', 'blood_bank', 'hospital', 'all')),
                recipient_email TEXT,
                subject TEXT NOT NULL,
                message TEXT NOT NULL,
                blood_group TEXT,
                status TEXT DEFAULT 'Sent' CHECK(status IN ('Sent', 'Failed')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # System Logs table
            """
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                log_type TEXT NOT NULL CHECK(log_type IN ('info', 'warning', 'error', 'success')),
                module TEXT NOT NULL,
                message TEXT NOT NULL,
                user_id INTEGER,
                user_type TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            # --- NEW TABLES ADDED BELOW ---

            # Blood Requests table
            """
            CREATE TABLE IF NOT EXISTS blood_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hospital_id INTEGER,
                blood_group TEXT NOT NULL CHECK(blood_group IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')),
                quantity_ml INTEGER NOT NULL,
                urgency_level TEXT DEFAULT 'Medium' CHECK(urgency_level IN ('Low', 'Medium', 'High', 'Critical')),
                message TEXT,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Approved', 'Rejected', 'Completed')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hospital_id) REFERENCES hospital(id) ON DELETE SET NULL
            )
            """,
            
            # Donor Interests table
            """
            CREATE TABLE IF NOT EXISTS donor_interests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donor_id INTEGER UNIQUE,
                interest_status TEXT CHECK(interest_status IN ('interested', 'not_interested')),
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (donor_id) REFERENCES donor(id) ON DELETE CASCADE
            )
            """,
            
            # Donor Appointments table
            """
            CREATE TABLE IF NOT EXISTS donor_appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                donor_id INTEGER,
                appointment_date DATE NOT NULL,
                appointment_time TEXT NOT NULL,
                location TEXT NOT NULL,
                message TEXT,
                status TEXT DEFAULT 'Scheduled' CHECK(status IN ('Scheduled', 'Confirmed', 'Completed', 'Cancelled')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (donor_id) REFERENCES donor(id) ON DELETE CASCADE
            )
            """,
            
            # --- END OF NEW TABLES ---
        ]
        
        for table_sql in tables:
            try:
                cursor.execute(table_sql)
            except Exception as e:
                print(f"Table creation warning: {e}")
        
        # Insert default data
        self.insert_default_data(cursor)
        
        conn.commit()
        conn.close()
        print("✅ SQLite database initialized successfully!")
    
    def insert_default_data(self, cursor):
        """Insert default data into tables"""
        
        # Insert default admin
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO admin (username, password, email) 
                VALUES ('admin', ?, 'admin@blooddonation.com')
            """, ('admin123',)) # Hashing is not used here for the default admin password 'admin123', consider changing this to use hash_password('admin123')
        except Exception as e:
            print(f"Admin insertion warning: {e}")
        
        # Insert sample blood bankers for testing (optional - can be removed if needed)
        sample_blood_bankers = [
            ('City Blood Bank', 'banker@bloodbank.com', 'banker123', 'City Blood Center', 'BB001', '+1234567890', '123 Blood Bank St, City'),
        ]
        
        for banker in sample_blood_bankers:
            try:
                # Use hash_password for sample accounts
                cursor.execute("""
                    INSERT OR IGNORE INTO blood_banker (name, email, password, bank_name, license_number, phone, address)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (banker[0], banker[1], hash_password(banker[2]), banker[3], banker[4], banker[5], banker[6]))
            except Exception as e:
                print(f"Blood banker insertion warning: {e}")
        
        # Insert sample hospitals for testing (optional - can be removed if needed)
        sample_hospitals = [
            ('City General Hospital', 'hospital@medical.com', 'hospital123', 'HOSP001', '+1234567892', '789 Hospital Rd, City', 'General Medicine, Surgery, Emergency'),
        ]
        
        for hospital in sample_hospitals:
            try:
                # Use hash_password for sample accounts
                cursor.execute("""
                    INSERT OR IGNORE INTO hospital (name, email, password, license_number, phone, address, specialties)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (hospital[0], hospital[1], hash_password(hospital[2]), hospital[3], hospital[4], hospital[5], hospital[6]))
            except Exception as e:
                print(f"Hospital insertion warning: {e}")
        
        # NO SAMPLE DONORS - Users will register themselves
        
        # NO SAMPLE BLOOD INVENTORY - Will be created when donors donate blood
        
        # NO SAMPLE PATIENTS - Will be created when hospitals add patients
        
        print("✅ Default data inserted successfully (No sample donors)!")

    def get_database_stats(self):
        """Get database statistics for admin dashboard"""
        conn = self.get_connection()
        if not conn:
            return {}
        
        try:
            cursor = conn.cursor()
            stats = {}
            
            # Count records in each table - ADDED blood_requests
            tables = ['admin', 'blood_banker', 'hospital', 'donor', 'blood_inventory', 'patient', 'email_alerts', 'blood_requests']
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                stats[f'{table}_count'] = cursor.fetchone()[0]
            
            # Blood inventory by group
            cursor.execute("""
                SELECT blood_group, SUM(quantity_ml) as total 
                FROM blood_inventory 
                WHERE status = 'Available' 
                GROUP BY blood_group
            """)
            stats['blood_inventory'] = [
                {'blood_group': row[0], 'total': row[1] or 0} 
                for row in cursor.fetchall()
            ]
            
            # Recent email stats
            cursor.execute("""
                SELECT status, COUNT(*) 
                FROM email_alerts 
                WHERE DATE(created_at) = DATE('now') 
                GROUP BY status
            """)
            email_stats = cursor.fetchall()
            stats['emails_today'] = {row[0]: row[1] for row in email_stats}
            
            return stats
            
        except Exception as e:
            print(f"Error getting database stats: {e}")
            return {}
        finally:
            conn.close()

# Initialize configurations
db_config = DatabaseConfig()
email_config = EmailConfig()

# Helper function to log system activities
def log_system_activity(log_type, module, message, user_id=None, user_type=None, ip_address=None):
    """Log system activities for audit trail"""
    conn = db_config.get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO system_logs (log_type, module, message, user_id, user_type, ip_address)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (log_type, module, message, user_id, user_type, ip_address))
            conn.commit()
        except Exception as e:
            print(f"Failed to log system activity: {e}")
        finally:
            conn.close()

# Test function to verify email configuration
def test_email_configuration():
    """Test email configuration and provide setup instructions"""
    print("\n" + "="*60)
    print("📧 EMAIL CONFIGURATION TEST")
    print("="*60)
    
    if email_config.enabled:
        print("✅ Email system is ENABLED")
        print(f"   SMTP Server: {email_config.smtp_server}:{email_config.smtp_port}")
        print(f"   Sender Email: {email_config.sender_email}")
        
        # Test connection
        try:
            server = smtplib.SMTP(email_config.smtp_server, email_config.smtp_port)
            server.starttls()
            server.login(email_config.sender_email, email_config.sender_password)
            server.quit()
            print("✅ SMTP Connection: SUCCESS")
            print("   Real emails will be sent to recipients")
        except Exception as e:
            print(f"❌ SMTP Connection: FAILED - {e}")
            print("   Emails will be simulated instead")
    else:
        print("🔄 Email system is in SIMULATION MODE")
        print("   Emails will be printed to console instead of being sent")
        print("\nTo enable real emails:")
        print("1. Set enabled=True in EmailConfig")
        print("2. Update sender_email with your Gmail address")
        print("3. Update sender_password with your Gmail App Password")
        print("4. Make sure 2-factor authentication is enabled in your Google account")
        print("5. Generate an App Password from Google Account settings")
    
    print("="*60 + "\n")

# Run email configuration test on import
if __name__ == "__main__":
    test_email_configuration()
else:
    # Only show brief status when imported
    if email_config.enabled:
        print("✅ Email system: ENABLED (real emails)")
    else:
        print("📧 Email system: SIMULATION MODE (console output)")