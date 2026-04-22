import os
import sqlite3

def reset_database():
    # Delete existing database file
    if os.path.exists('blood_donation.db'):
        os.remove('blood_donation.db')
        print("✅ Old database deleted")
    
    # Recreate database
    conn = sqlite3.connect('blood_donation.db')
    cursor = conn.cursor()
    
    # Create tables
    tables = [
        # Admin table
        """
        CREATE TABLE admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        # Blood Banker table
        """
        CREATE TABLE blood_banker (
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
        CREATE TABLE hospital (
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
        CREATE TABLE donor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            blood_group TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
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
        CREATE TABLE blood_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blood_group TEXT NOT NULL,
            quantity_ml INTEGER NOT NULL,
            donor_id INTEGER,
            blood_banker_id INTEGER,
            collection_date DATE NOT NULL,
            expiry_date DATE NOT NULL,
            status TEXT DEFAULT 'Available',
            blockchain_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (donor_id) REFERENCES donor(id),
            FOREIGN KEY (blood_banker_id) REFERENCES blood_banker(id)
        )
        """,
        # Patient table
        """
        CREATE TABLE patient (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            hospital_id INTEGER,
            blood_group TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            required_quantity_ml INTEGER NOT NULL,
            urgency_level TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Pending',
            requested_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hospital_id) REFERENCES hospital(id)
        )
        """
    ]
    
    for table_sql in tables:
        try:
            cursor.execute(table_sql)
            print(f"✅ Table created successfully")
        except Exception as e:
            print(f"❌ Table creation error: {e}")
    
    # Insert default admin
    cursor.execute("INSERT INTO admin (username, password, email) VALUES ('admin', 'admin123', 'admin@blooddonation.com')")
    
    conn.commit()
    conn.close()
    print("✅ Database reset completed successfully!")

if __name__ == "__main__":
    reset_database()