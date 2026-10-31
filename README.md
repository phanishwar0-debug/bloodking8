# 🩸 BloodChain – Blood Donation Management System

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
