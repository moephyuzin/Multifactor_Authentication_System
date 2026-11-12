from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask import get_flashed_messages
import os
from flask_mail import Mail, Message
import random
from flask import session
import pyotp
import qrcode
import io
import base64
import requests
from flask import jsonify
import time
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# SQLite Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'database.db')

db = SQLAlchemy(app)

# ---------- User Model ----------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    otp = db.Column(db.String(6))
    is_verified = db.Column(db.Boolean, default=False)

# Flask-Mail Configuration (Use Mailtrap or Gmail SMTP)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'moephyuzin322@gmail.com'     
app.config['MAIL_PASSWORD'] = 'skwy gcam zuvj czlg'        
app.config['MAIL_DEFAULT_SENDER'] = 'moephyuzin322@gmail.com' 
mail = Mail(app)
# Secret key must match your app secret
s = URLSafeTimedSerializer(app.secret_key)


# ---------- Home ----------

@app.route('/')
def index():
    return render_template('home.html')


# ---------- Sign Up ----------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        recaptcha_response = request.form.get('g-recaptcha-response')
        secret_key = "6Ld-tjsrAAAAAANGGBhO9_P60ajqmhkj_3-f0Mgn"
        verify_url = "https://www.google.com/recaptcha/api/siteverify"

        payload = {'secret': secret_key, 'response': recaptcha_response}
        result = requests.post(verify_url, data=payload).json()

        if not result.get("success"):
            flash("reCAPTCHA verification failed. Please try again.", "error")
            return redirect(url_for('signup'))

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return redirect(url_for('signup'))

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash('Username or Email already exists!', 'error')
            return redirect(url_for('signup'))

        # Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # Save data in session
        session['temp_user'] = {
            'username': username,
            'email': email,
            'password': generate_password_hash(password),
            'otp': otp
        }

        # Send OTP to email
        msg = Message("Verify your email", recipients=[email])
        msg.body = f"Your OTP for account verification is: {otp}"
        try:
            mail.send(msg)
            flash('OTP has been sent to your email. Please Check!', 'success')
        except:
            flash('Failed to send email. Please try again.', 'error')

        return redirect(url_for('verify_signup'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password']

        recaptcha_response = request.form.get('g-recaptcha-response')
        secret_key = "6Ld-tjsrAAAAAANGGBhO9_P60ajqmhkj_3-f0Mgn"
        verify_url = "https://www.google.com/recaptcha/api/siteverify"

        payload = {'secret': secret_key, 'response': recaptcha_response}
        result = requests.post(verify_url, data=payload).json()

        if not result.get("success"):
            flash("reCAPTCHA verification failed. Please try again.", "error")
            return redirect(url_for('login'))

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            if not user.is_verified:
                flash('Please verify your email before logging in.', 'error')
                return redirect(url_for('signup'))

            # Generate OTP
            otp = str(random.randint(100000, 999999))

            # Store OTP and user_id in session
            session['otp'] = otp
            session['otp_timestamp'] = time.time()   # Save timestamp here
            session['user_id'] = user.id

            # Send OTP to user's email
            msg = Message("Login OTP Verification", recipients=[user.email])
            msg.body = f"Your login OTP is: {otp}"
            try:
                mail.send(msg)
                flash('OTP has been sent to your email. Please Check!', 'success')
            except:
                flash('Failed to send OTP. Try again.', 'error')

            return redirect(url_for('verify_login'))

        else:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')
    
@app.route('/forgetpassword', methods=['GET', 'POST'])
def forgetpassword():
    if request.method == 'POST':
        email = request.form['email'].strip()
        user = User.query.filter_by(email=email).first()

        if user:
            # Generate a secure token for password reset
            token = s.dumps(email, salt='password-reset-salt')
            reset_link = url_for('resetpassword', token=token, _external=True)
            
            msg = Message('Password Reset Request', recipients=[email])
            msg.body = f"""
            Hello {user.username},

            We received a request to reset your password. Click the link below to reset it:

            {reset_link}

            If you did not request this, please ignore this email.
            """
            try:
                mail.send(msg)
                flash('An email with password reset instructions has been sent to your inbox.', 'info')
            except:
                flash('Failed to send the reset email. Please try again later.', 'error')
        else:
            flash('No account found with that email address.', 'error')

    return render_template('forgetpassword.html')

@app.route('/resetpassword/<token>', methods=['GET', 'POST'])
def resetpassword(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('forgetpassword'))

    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
        else:
            user = User.query.filter_by(email=email).first()
            if user:
                user.password = generate_password_hash(password)
                db.session.commit()
                flash('Your password has been updated successfully.', 'success')
                return redirect(url_for('login'))
            else:
                flash('User not found.', 'error')

    return render_template('resetpassword.html', token=token)

@app.route('/verify-signup', methods=['GET', 'POST'])
def verify_signup():
    if request.method == 'POST':
        user_otp = request.form['otp']
        temp_user = session.get('temp_user', {})

        if not temp_user:
            flash('Session expired. Please sign up again.', 'error')
            return redirect(url_for('signup'))

        if user_otp == temp_user.get('otp'):
            new_user = User(
                username=temp_user['username'],
                email=temp_user['email'],
                password=temp_user['password'],
                is_verified=True
            )
            db.session.add(new_user)
            db.session.commit()
            session.pop('temp_user', None)
            flash('Email verified! Account created successfully.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid OTP. Please try again.', 'error')

    return render_template('verify.html')


@app.route('/verify-login', methods=['GET', 'POST'])
def verify_login():
    VALIDITY_PERIOD = 60  # seconds

    if request.method == 'GET':
        list(get_flashed_messages())
        if not session.get('otp') or not session.get('user_id'):
            flash('Session expired or invalid. Please login again.', 'error')
            return redirect(url_for('login'))
    
    # Calculate remaining time for countdown
    otp_time = session.get('otp_timestamp', 0)
    elapsed = time.time() - otp_time
    remaining_time = int(VALIDITY_PERIOD - elapsed) if elapsed < VALIDITY_PERIOD else 0

    if request.method == 'POST':
        user_otp = request.form['otp']
        session_otp = session.get('otp')
        user_id = session.get('user_id')

        if not user_otp or not session_otp or not user_id:
            flash('Session expired or invalid. Please login again.', 'error')
            return redirect(url_for('login'))

        # Check OTP expiration
        if time.time() - otp_time > VALIDITY_PERIOD:
            flash('OTP expired. Please resend OTP to get a new code.', 'error')
            return redirect(url_for('verify_login'))

        if user_otp == session_otp:
            session.pop('otp', None)
            session.pop('otp_timestamp', None)
            session['is_logged_in'] = True
            session['user_id'] = user_id
            flash('Login successful!', 'success')
            session.pop('welcome_flash_done', None)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid OTP. Please try again.', 'error')
            # Do NOT reset OTP timestamp or remaining_time here to keep timer running

    return render_template('verify.html', remaining_time=remaining_time)


# QR email
@app.route('/qr_email', methods=['GET', 'POST'])
def qr_email():
    if request.method == 'POST':
        email = request.form['email'].strip()
        user = User.query.filter_by(email=email).first()

        if user:
            session['qr_email'] = email
            return redirect(url_for('qr_code'))  # Proceed to QR display
        else:
            flash("Email not found. Please log in normally.", "error")
            return redirect(url_for('login'))

    return render_template('qr_email_input.html')

# QR code
@app.route('/qr_code')
def qr_code():
    email = session.get('qr_email')

    if not email:
        flash("No email in session. Please try again.", "error")
        return redirect(url_for('qr_email'))

    # Generate TOTP from shared or dynamic secret (here: dynamic per session)
    totp = pyotp.TOTP(pyotp.random_base32())
    session['totp_secret'] = totp.secret

    uri = totp.provisioning_uri(name=email, issuer_name="SecureQRLogin")
    qr = qrcode.make(uri)
    img_io = io.BytesIO()
    qr.save(img_io, 'PNG')
    img_io.seek(0)
    base64_img = base64.b64encode(img_io.read()).decode('ascii')

    return render_template('qr_code.html', qr_code=base64_img)

#QR_verify
@app.route('/qr_verify', methods=['POST'])
def qr_verify():
    user_code = request.form['totp_code']
    secret = session.get('totp_secret')
    email = session.get('qr_email')

    if not secret or not email:
        flash("Session expired. Please try again.", "error")
        return redirect(url_for('qr_email'))

    totp = pyotp.TOTP(secret)
    if totp.verify(user_code):
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("User not found.", "error")
            return redirect(url_for('login'))

        # Generate 6-digit OTP for email
        otp = str(random.randint(100000, 999999))

        # Store in session for email OTP verification
        session['otp'] = otp
        session['user_id'] = user.id
        session['qr_email'] = email  # Optional, for re-use
        session['otp_timestamp'] = time.time()

        # Send OTP to user's email
        msg = Message("Email OTP Verification", recipients=[user.email])
        msg.body = f"Your login email OTP is: {otp}"
        try:
            mail.send(msg)
            flash("OTP has been sent to your email. Please Check!", "success")
        except:
            flash("Failed to send email OTP. Please try again.", "error")
            return redirect(url_for('login'))

        # Redirect to existing email OTP verification
        return redirect(url_for('verify_login'))

    else:
        flash("Invalid QR code. Try again.", "error")
        return redirect(url_for('qr_code'))

@app.route('/dashboard')
def dashboard():
    if not session.get('user_id'):
        flash('Please log in to access the dashboard.', 'error')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', username=user.username)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

    
@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    if 'temp_user' in session:
        temp_user = session['temp_user']
        otp = str(random.randint(100000, 999999))
        session['temp_user']['otp'] = otp
        email = temp_user['email']
    else:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify(success=False), 400
        user = User.query.get(user_id)
        if not user:
            return jsonify(success=False), 400
        otp = str(random.randint(100000, 999999))
        session['otp'] = otp
        email = user.email

    session['otp_timestamp'] = time.time()  # Reset timestamp on resend

    msg = Message("New OTP code", recipients=[email])
    msg.body = f"Your new OTP code is: {otp}"
    try:
        mail.send(msg)
        return jsonify(success=True)
    except Exception as e:
        print("Error sending OTP:", e)
        return jsonify(success=False)


# ---------- Run ----------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
