import mysql.connector
from mysql.connector import Error

def create_database_and_tables():
    try:
        # Connect to MySQL without specifying database
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='123456789'  # Use your MySQL password here
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Create database
            cursor.execute("CREATE DATABASE IF NOT EXISTS blood_donation_blockchain")
            print("✅ Database created successfully")
            
            # Use the database
            cursor.execute("USE blood_donation_blockchain")
            
            # Create tables
            tables_sql = [
                """
                CREATE TABLE IF NOT EXISTS admin (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    email VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS blood_banker (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    bank_name VARCHAR(100) NOT NULL,
                    license_number VARCHAR(50) UNIQUE,
                    address TEXT,
                    phone VARCHAR(15),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS hospital (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    license_number VARCHAR(50) UNIQUE,
                    address TEXT,
                    phone VARCHAR(15),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS donor (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    blood_group ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
                    age INT NOT NULL,
                    gender ENUM('Male', 'Female', 'Other') NOT NULL,
                    weight DECIMAL(5,2),
                    phone VARCHAR(15),
                    address TEXT,
                    last_donation_date DATE,
                    is_available BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS blood_inventory (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    blood_group ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
                    quantity_ml INT NOT NULL,
                    donor_id INT,
                    blood_banker_id INT,
                    collection_date DATE NOT NULL,
                    expiry_date DATE NOT NULL,
                    status ENUM('Available', 'Used', 'Expired') DEFAULT 'Available',
                    blockchain_hash VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (donor_id) REFERENCES donor(id) ON DELETE SET NULL,
                    FOREIGN KEY (blood_banker_id) REFERENCES blood_banker(id) ON DELETE SET NULL
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS patient (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(100) NOT NULL,
                    hospital_id INT,
                    blood_group ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
                    age INT,
                    gender ENUM('Male', 'Female', 'Other'),
                    required_quantity_ml INT NOT NULL,
                    urgency_level ENUM('Low', 'Medium', 'High', 'Critical') DEFAULT 'Medium',
                    status ENUM('Pending', 'Approved', 'Rejected', 'Completed') DEFAULT 'Pending',
                    requested_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (hospital_id) REFERENCES hospital(id) ON DELETE SET NULL
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS blood_transaction (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    blood_inventory_id INT,
                    patient_id INT,
                    hospital_id INT,
                    quantity_ml INT NOT NULL,
                    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    blockchain_hash VARCHAR(255),
                    FOREIGN KEY (blood_inventory_id) REFERENCES blood_inventory(id) ON DELETE SET NULL,
                    FOREIGN KEY (patient_id) REFERENCES patient(id) ON DELETE SET NULL,
                    FOREIGN KEY (hospital_id) REFERENCES hospital(id) ON DELETE SET NULL
                )
                """
            ]
            
            for sql in tables_sql:
                cursor.execute(sql)
            
            # Insert default admin
            cursor.execute("""
                INSERT IGNORE INTO admin (username, password, email) 
                VALUES ('admin', 'admin123', 'admin@blooddonation.com')
            """)
            
            # Insert sample blood banker
            cursor.execute("""
                INSERT IGNORE INTO blood_banker (name, email, password, bank_name, license_number, phone) 
                VALUES ('City Blood Bank', 'banker@bloodbank.com', 'banker123', 'City Blood Center', 'BB12345', '+1234567890')
            """)
            
            # Insert sample hospital
            cursor.execute("""
                INSERT IGNORE INTO hospital (name, email, password, license_number, phone) 
                VALUES ('City General Hospital', 'hospital@medical.com', 'hospital123', 'HOSP12345', '+1234567891')
            """)
            
            connection.commit()
            print("✅ All tables created successfully")
            print("✅ Sample data inserted successfully")
            
    except Error as e:
        print(f"❌ Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("✅ Database connection closed")

if __name__ == "__main__":
    create_database_and_tables()