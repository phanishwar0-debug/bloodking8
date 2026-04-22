CREATE DATABASE IF NOT EXISTS blood_donation_blockchain;
USE blood_donation_blockchain;

-- Admin Table
CREATE TABLE admin (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Blood Banker Table
CREATE TABLE blood_banker (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    bank_name VARCHAR(100) NOT NULL,
    license_number VARCHAR(50) UNIQUE,
    address TEXT,
    phone VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hospital Table
CREATE TABLE hospital (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    license_number VARCHAR(50) UNIQUE,
    address TEXT,
    phone VARCHAR(15),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Donor Table
CREATE TABLE donor (
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
);

-- Blood Inventory Table
CREATE TABLE blood_inventory (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blood_group ENUM('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-') NOT NULL,
    quantity_ml INT NOT NULL,
    donor_id INT,
    blood_banker_id INT,
    collection_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    status ENUM('Available', 'Used', 'Expired') DEFAULT 'Available',
    blockchain_hash VARCHAR(255),
    FOREIGN KEY (donor_id) REFERENCES donor(id),
    FOREIGN KEY (blood_banker_id) REFERENCES blood_banker(id)
);

-- Patient Table
CREATE TABLE patient (
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
    FOREIGN KEY (hospital_id) REFERENCES hospital(id)
);

-- Blood Transaction Table
CREATE TABLE blood_transaction (
    id INT PRIMARY KEY AUTO_INCREMENT,
    blood_inventory_id INT,
    patient_id INT,
    hospital_id INT,
    quantity_ml INT NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    blockchain_hash VARCHAR(255),
    FOREIGN KEY (blood_inventory_id) REFERENCES blood_inventory(id),
    FOREIGN KEY (patient_id) REFERENCES patient(id),
    FOREIGN KEY (hospital_id) REFERENCES hospital(id)
);

-- Insert default admin
INSERT INTO admin (username, password, email) VALUES 
('admin', 'admin123', 'admin@blooddonation.com');