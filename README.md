Secure Account System
=====================
This project is a secure user registration and login web application built with Flask (Python). 
It incorporates multiple security features such as email verification with OTP, password strength validation,
Google reCAPTCHA, multi-factor authentication (MFA) using QR codes, and secure password reset functionality.

Features
===========
-User Registration: Users register with  email, and password.
-Password Validation: Enforces strong password rules (min 8 chars, uppercase, lowercase, digit, special char) with real-time feedback.
-Email Verification with OTP: Upon registration, users receive a one-time password (OTP) by email to verify their account.
-Login with OTP Verification: After login with email/password, a second OTP is sent via email for two-factor authentication.
-Multi-Factor Authentication with QR Code: Optionally use TOTP via authenticator apps for additional security.
-Google reCAPTCHA: Protects registration and login forms from bots and automated abuse.
-Password Rest: Users can reset their passwords via secure email links with expiring tokens.
-Session Management: Secure session handling with expiration and no caching of sensitive pages.
-Responsive and Clean UI: User-friendly forms with helpful validation messages and feedback.

Technology Stack
===================
-Python 3.x
-Flask 2.x
-Flask-SQLAlchemy (ORM for SQLite)
-Flask-Mail (SMTP email integration)
-Werkzeug (Password hashing with PBKDF2)
-pyotp (Time-based OTP generation)
-qrcode (QR code generation)
-Google reCAPTCHA v2
-SQLite Database

Requirements
==============
Flask==2.3.2
Flask-SQLAlchemy==3.0.5
Flask-Mail==0.9.1
requests==2.31.0
pyotp==2.8.0
qrcode[pil]==7.4.2
Werkzeug==2.3.6

Setup and Installation
=======================

1. Clone the repository
2. Create and activate a Python virtual environment:
        python3 -m venv venv
        venv\Scripts\activate     # Windows
        source venv/bin/activate  # Linux/macOS
    Note: if you are running this for the first time, you need to delete venv which is already exist in this folder before creating and activating an environment.
3.Install dependencies:
        pip install -r requirements.txt
4.Configure Email and reCAPTCHA
    Edit the app.py file and update the following configurations with your email credentials and reCAPTCHA secret:  
        app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
        app.config['MAIL_PASSWORD'] = 'your-email-password'
        secret_key = "your-google-recaptcha-secret-key"
5.Register your domain with Google reCAPTCHA and update the site and secret keys in the application accordingly.
6.The app uses SQLite; database file is auto-created on first run.
7.Running the app:
        python app.py
    Access at http://127.0.0.1:5000.

Usage
======
-Navigate to the home page.
-Sign up with your username, email, and strong password.
-Complete the reCAPTCHA challenge.
-Verify your email by entering the OTP sent to your inbox.
-Log in with email and password.
-Enter the OTP sent to your email to complete login.
-Optionally use QR code-based MFA for enhanced security.
-Use the "Forgot Password" link to reset your password securely.


Security Notes
=================
-Passwords are hashed using PBKDF2 with SHA256 and unique salts.
-Email verification with OTP prevents fake account creation.
-Login OTP and QR-based TOTP provide multi-factor authentication.
-Google reCAPTCHA protects against automated bot attacks.
-Password reset links use time-limited secure tokens.
-Sessions are secured and sensitive pages disable caching.
