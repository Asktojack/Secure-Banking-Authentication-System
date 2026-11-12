# 🔐 Secure Banking Authentication System

### Multi-Factor Authentication and Suspicious Transaction Detection for Banking Applications

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-black)
![MySQL](https://img.shields.io/badge/Database-MySQL-orange)
![HTML](https://img.shields.io/badge/Frontend-HTML5-red)
![CSS](https://img.shields.io/badge/Styling-CSS3-blue)
![JavaScript](https://img.shields.io/badge/Language-JavaScript-yellow)

## 📌 About the Project

The **Secure Banking Authentication System** is a Python Flask-based web application designed to improve banking security through Multi-Factor Authentication (MFA) and Suspicious Transaction Detection.

Traditional banking applications primarily depend on username and password authentication. This project introduces additional verification layers to strengthen account security and independently monitors banking transactions to identify potentially suspicious activities.

The system consists of two independent modules:

1. **Multi-Factor Authentication (MFA)**
2. **Suspicious Transaction Detection**

## 🎯 Project Objectives

- Improve banking application login security.
- Implement multiple authentication methods.
- Provide OTP-based user verification.
- Support configurable authentication sequences.
- Detect potentially suspicious banking transactions.
- Analyze geographical distance and transaction time differences.
- Generate alerts for transactions requiring additional verification.

## ✨ Key Features

### 1. Multi-Factor Authentication (MFA)

- Username and password authentication.
- SIM/device verification.
- Email OTP verification.
- SMS OTP verification.
- Authenticator application verification.
- Configurable verification sequence.
- OTP expiration mechanism.
- Session management.

### 2. Suspicious Transaction Detection

- Independent transaction monitoring.
- Location-based transaction comparison.
- Time-gap analysis.
- Travel feasibility evaluation.
- Risk score calculation.
- Low, medium and high-risk classification.
- Suspicious activity alerts.
- Additional transaction verification.

### 3. Banking Functionalities

- User registration and login.
- Banking dashboard.
- Profile management.
- Balance management.
- Deposit and withdrawal.
- Money transfer.
- Beneficiary management.
- Transaction history.
- Login history.
- Notifications.
- Forgot password and reset password.

## 🏗️ System Architecture

```text
                  USER
                    |
                    v
              FRONTEND LAYER
           HTML + CSS + JavaScript
                    |
                    v
               FLASK BACKEND
                    |
          +---------+---------+
          |                   |
          v                   v
    AUTHENTICATION       BANKING OPERATIONS
       MODULE                   |
          |                     v
          v                TRANSACTION
     MULTI-FACTOR           PROCESSING
   AUTHENTICATION                |
          |                     v
          v                RISK ANALYSIS
    OTP VERIFICATION             |
          |                     v
          |              SUSPICIOUS TRANSACTION
          |                   DETECTION
          |                     |
          +----------+----------+
                     |
                     v
                MYSQL DATABASE
```

## 🔑 Module 1: Multi-Factor Authentication

The MFA module provides multiple authentication layers to verify users before granting access to the banking application.

**Authentication Workflow:**

1. User enters username and password.
2. Application validates login credentials.
3. Additional device/SIM verification is performed as configured.
4. OTP verification is performed through supported channels.
5. Authenticator application verification is performed when configured.
6. Successful verification grants access to the banking dashboard.

## 🚨 Module 2: Suspicious Transaction Detection

This module independently evaluates banking transactions using geographical distance and time differences between consecutive transactions.

**Working Principle:**

- Collect previous transaction details.
- Collect current transaction details.
- Calculate the time difference.
- Compare geographical locations.
- Evaluate travel feasibility.
- Calculate a transaction risk score.
- Classify the transaction according to risk level.
- Generate an alert or request additional verification when necessary.

| Risk Level | Description |
|---|---|
| Low Risk | Lower calculated transaction risk |
| Medium Risk | Requires additional attention |
| High Risk | May require additional verification |

## 🛠️ Technologies Used

| Category | Technologies |
|---|---|
| Frontend | HTML5, CSS3, JavaScript |
| Backend | Python, Flask |
| Database | MySQL |
| Database Connectivity | MySQL Connector for Python |
| Email Service | Flask-Mail, Gmail SMTP |
| SMS Service | Twilio API |
| Authentication | OTP, Authenticator Application |
| Security | Werkzeug Password Hashing, Flask Sessions |
| Configuration | Python-dotenv |

## 📂 Project Structure

```text
secure.bank/
│
├── app.py
├── config.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
│
├── database/
│   └── banking.sql
│
├── models/
│   └── user.py
│
├── routes/
│   └── auth.py
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── authenticator.html
│   ├── transfer.html
│   ├── withdraw.html
│   ├── deposit.html
│   └── ...
│
└── utils/
    ├── authenticator.py
    ├── database.py
    ├── device.py
    ├── mail.py
    ├── otp.py
    ├── password.py
    ├── risk.py
    └── sms.py
```

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Asktojack/Secure-Banking-Authentication-System.git
```

### 2. Navigate to the Project Folder

```bash
cd Secure-Banking-Authentication-System
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate Virtual Environment

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 5. Install Required Packages

```bash
pip install -r requirements.txt
```

### 6. Configure MySQL Database

1. Start your MySQL server.
2. Open phpMyAdmin or MySQL Workbench.
3. Create the database configured in your `.env` file.
4. Import `database/banking.sql`.
5. Verify that the database tables are created successfully.

### 7. Configure Environment Variables

Create a `.env` file in the project root directory.

```env
SECRET_KEY=your_secret_key

DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_database_password
DB_NAME=secure.bank

MAIL_USERNAME=your_email
MAIL_PASSWORD=your_gmail_app_password

TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_NUMBER=your_twilio_phone_number

GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

**Important:** Replace the placeholder values with your own credentials. Never upload your `.env` file or expose API keys and passwords on GitHub.

### 8. Run the Application

```bash
python app.py
```

Open your browser:

```text
http://127.0.0.1:5000
```

## 🔒 Security Features

- Password hashing.
- Environment-based credential management.
- OTP-based verification.
- OTP expiration.
- Session management.
- Configurable authentication methods.
- Separate transaction-risk analysis.
- Git ignore protection for sensitive files.

## 🚀 Future Enhancements

- Machine-learning-based fraud detection.
- Advanced device fingerprinting.
- Real-time transaction monitoring.
- Improved location-based risk analysis.
- Push notification authentication.
- REST API integration.
- Advanced security monitoring.
- Cloud deployment.

## 🎓 Applications

- Banking application security.
- Multi-factor authentication systems.
- Financial transaction monitoring.
- Cybersecurity demonstrations.
- Academic research and development.
- Secure web application development.

## 👨‍💻 Developer

**Manoj SV**

**Project Title:** Multi-Factor Authentication and Suspicious Transaction Detection for Banking Applications

**GitHub:** [Asktojack](https://github.com/Asktojack)

**Repository:** [Secure Banking Authentication System](https://github.com/Asktojack/Secure-Banking-Authentication-System)

## 📜 Disclaimer

This project is developed for academic and educational purposes. It demonstrates authentication workflows and transaction-risk analysis. It is not a certified banking system and should not be used to process real financial transactions.

---

⭐ If you find this project useful, consider giving the repository a star!
