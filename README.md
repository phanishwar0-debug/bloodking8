# 🩸 BlockChain – Blood Donation Management System

A Flask-based web application that connects **donors, hospitals, and blood banks**, with a **blockchain ledger** that records key blood-donation events and **automated email alerts** for urgent blood requirements.

🔗 **Repository:** https://github.com/phanishwar0-debug/bloodking8

---

## ✨ Features

- **Multi-role system** – separate portals for Admin, Blood Banks, Hospitals, and Donors
- **Blockchain ledger** – SHA-256 hash-linked blocks record registrations and transactions, with chain-validation support
- **Urgent blood request alerts** – hospitals can raise requests; matching blood banks and donors with the same blood group are emailed automatically
- **Admin dashboard** – live statistics for donors, blood banks, hospitals, patients, and available blood inventory by group
- **Bulk email campaigns** – send alerts to all donors, a specific blood group, all blood banks, or all hospitals (sent in a background thread)
- **Donor appointments** – admin can schedule donation appointments and email the details to interested donors
- **Interested-donor filtering** – filter by age, gender, and blood group
- **Email logs** – every alert is logged with its status (Sent / Failed)
- **Blood inventory tracking** – available quantity (ml) per blood group
- **Management panels** – view and delete hospitals, blood bankers, and patients

## 🛠️ Tech Stack

| Layer      | Technology                         |
|------------|------------------------------------|
| Backend    | Python, Flask                      |
| Database   | SQLite (`blood_donation.db`)       |
| Frontend   | HTML (Jinja2 templates), CSS, JS   |
| Security   | SHA-256 password hashing, Flask sessions |
| Ledger     | Custom SHA-256 blockchain          |
| Email      | SMTP (configured in `config.py`)   |

## 📁 Project Structure

```
bloodking8/
├── app.py               # Main Flask application (routes, blockchain, email alerts)
├── blockchain.py        # Blockchain implementation
├── config.py            # Database, password hashing, and email configuration
├── init_database.py     # Creates database tables
├── reset_database.py    # Resets the database
├── requirements.txt     # Python dependencies
├── blood_donation.db    # SQLite database
├── database/            # Database-related files
├── static/              # CSS, JS, images
├── templates/           # HTML templates
└── .gitignore
```

## 📸 Screenshots

### Home Page
Role-based entry point for Administrators, Blood Banks, Blood Donors, and Hospitals.

<p align="center">
  <img src="screenshots/home.png" alt="BloodChain Home Page" width="500">
</p>

### Admin Dashboard
Live statistics, quick email alerts, blood inventory summary, and management shortcuts.

<p align="center">
  <img src="screenshots/admin-dashboard.png" alt="Admin Dashboard" width="500">
</p>

### Blood Bank Dashboard
Available blood, inventory by blood group with stock status, and quick actions.

<p align="center">
  <img src="screenshots/blood-bank-dashboard.png" alt="Blood Bank Dashboard" width="500">
</p>

### Blood Bank Login & Registration

| Login | Registration |
|:-----:|:------------:|
| <img src="screenshots/blood-bank-login.png" alt="Blood Bank Login" width="400"> | <img src="screenshots/blood-bank-registration.png" alt="Blood Bank Registration" width="400"> |

### Donor Login & Registration

| Login | Registration |
|:-----:|:------------:|
| <img src="screenshots/donor-login.png" alt="Donor Login" width="400"> | <img src="screenshots/donor-registration.png" alt="Donor Registration" width="400"> |

### Donor Profile
Personal details, donation history with blockchain hash, availability response, and donation totals.

<p align="center">
  <img src="screenshots/donor-profile.png" alt="Donor Profile" width="500">
</p>

### Hospital Login & Registration

| Login | Registration |
|:-----:|:------------:|
| <img src="screenshots/hospital-login.png" alt="Hospital Login" width="400"> | <img src="screenshots/hospital-registration.png" alt="Hospital Registration" width="400"> |

### Hospital Dashboard
Quick access to patient registration, blood inventory, donor search, and emergency contacts.

<p align="center">
  <img src="screenshots/hospital-dashboard.png" alt="Hospital Dashboard" width="500">
</p>

### Register Patient & Send Blood Request

| Register New Patient | Send Blood Request to Admin |
|:--------------------:|:---------------------------:|
| <img src="screenshots/register-patient.png" alt="Register New Patient" width="400"> | <img src="screenshots/blood-request.png" alt="Send Blood Request" width="400"> |

### Blood Donation Form
Donors submit a donation with a health questionnaire; each donation is recorded on the blockchain.

<p align="center">
  <img src="screenshots/donate-blood.png" alt="Blood Donation Form" width="500">
</p>

### Blood Inventory
Stock by blood group, per-unit details with expiry dates and blockchain hashes, and inventory statistics.

<p align="center">
  <img src="screenshots/blood-inventory.png" alt="Blood Inventory" width="500">
</p>

### Donor Management
Filter donors by age, blood group, gender, and availability, and send emails to selected donors.

<p align="center">
  <img src="screenshots/blood-donors.png" alt="Blood Donors List" width="500">
</p>

### Patient Records
Track patients requiring blood, with urgency level and request status.

<p align="center">
  <img src="screenshots/patient-records.png" alt="Patient Records" width="500">
</p>

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/phanishwar0-debug/bloodking8.git
cd bloodking8

# 2. (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize the database
python init_database.py

# 5. Run the application
python app.py
```

Then open **http://127.0.0.1:5000** in your browser (Flask's default address).

### Resetting the database

```bash
python reset_database.py
```

> ⚠️ This clears existing data.

## ⚙️ Configuration

Edit `config.py` to set up:

- **Database** – SQLite connection settings
- **Email (SMTP)** – sender email and app password used for sending alerts

Use an app-specific password (for example, a Gmail App Password) rather than your real account password.

## 👥 User Roles

| Role           | What they can do                                                                 |
|----------------|----------------------------------------------------------------------------------|
| **Admin**      | View dashboard stats, send email alerts, schedule appointments, manage users, view email logs |
| **Blood Bank** | Register/login, view blood inventory and donor counts                            |
| **Hospital**   | Register/login, manage patients, raise urgent blood requests                     |
| **Donor**      | Register, set availability, express interest in donating                         |

## 🔗 Blockchain

Each important event (such as blood bank registration) is stored as a block containing:

- `index`, `timestamp`, `data`
- `previous_hash` and its own SHA-256 `hash`

The chain can be validated at any time: if any block's data is altered, its hash no longer matches and the chain is flagged as invalid.

## 🔒 Security Notes

Before deploying this project publicly, please:

- Change the default admin credentials in `app.py`
- Move `app.secret_key` and email credentials into environment variables
- Add `.env` and sensitive files to `.gitignore`
- Replace plain SHA-256 password hashing with `bcrypt` or `werkzeug.security`
- Run with `debug=False` in production

## 🗺️ Future Improvements

- Password hashing with salt (bcrypt)
- SMS notifications
- Donor eligibility and last-donation tracking
- Map-based nearby blood bank search
- Docker support and cloud deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

## 📄 License

This project is open source. Add a `LICENSE` file (for example, MIT) to specify the terms.

## 👤 Author

**phanishwar0-debug** – [GitHub Profile](https://github.com/phanishwar0-debug)

---

⭐ If you found this project useful, please give it a star!
