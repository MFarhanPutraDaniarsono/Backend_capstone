import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS

    app = Flask(__name__)
CORS(app)

# =========================
# CONFIG (Neon Database)
# =========================
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_6ugBHKE1fiWz@ep-patient-cake-aokqq1ge.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# =========================
# MODEL: ACCOUNTS & PROFILES (EMAIL BASED)
# =========================
class Account(db.Model):
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_verified = db.Column(db.Boolean, default=True) # Otomatis aktif tanpa OTP
    
    # Hubungan One-to-One ke Profile
    profile = db.relationship('UserProfile', backref='account', uselist=False, cascade="all, delete-orphan")

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), unique=True, nullable=False)
    owner_name = db.Column(db.String(100))
    workshop_name = db.Column(db.String(100))
    workshop_phone = db.Column(db.String(15))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# =========================
# ENDPOINT: REGISTER
# =========================
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password')
    
    owner_name = data.get('owner_name', '')
    workshop_name = data.get('workshop_name', '')
    workshop_phone = data.get('workshop_phone', '')

    if not email or not password:
        return jsonify({'message': 'Email dan Password wajib diisi'}), 400

    # Cek ketersediaan email
    existing_account = Account.query.filter_by(email=email).first()
    if existing_account:
        return jsonify({'message': 'Email sudah terdaftar'}), 400

    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

    # 1. Simpan ke tabel Akun
    new_account = Account(email=email, password=hashed_pw, is_verified=True)
    db.session.add(new_account)
    db.session.flush()  # Ambil ID account sebelum commit

    # 2. Simpan ke tabel Profil
    new_profile = UserProfile(
        account_id=new_account.id,
        owner_name=owner_name,
        workshop_name=workshop_name,
        workshop_phone=workshop_phone if workshop_phone else None
    )
    db.session.add(new_profile)
    db.session.commit()

    return jsonify({
        'message': 'Registrasi berhasil, akun langsung aktif!',
        'email': email
    }), 201

# =========================
# ENDPOINT: LOGIN (MANUAL EMAIL)
# =========================
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email dan password tidak boleh kosong'}), 400

    account = Account.query.filter_by(email=email).first()

    if not account:
        return jsonify({'message': 'Email tidak ditemukan'}), 404

    if not bcrypt.check_password_hash(account.password, password):
        return jsonify({'message': 'Password salah'}), 401

    # Mengembalikan data user secara langsung (Bypass JWT token)
    profile_data = {}
    if account.profile:
        profile_data = {
            'owner_name': account.profile.owner_name,
            'workshop_name': account.profile.workshop_name,
            'workshop_phone': account.profile.workshop_phone
        }

    return jsonify({
        'message': 'Login berhasil',
        'user': {
            'id': account.id,
            'email': account.email,
            **profile_data
        }
    }), 200

# =========================
# ENDPOINT: PROFILE (MANUAL BY ID)
# =========================
@app.route('/profile/<int:user_id>', methods=['GET'])
def profile(user_id):
    account = Account.query.get(user_id)

    if not account:
        return jsonify({'message': 'User tidak ditemukan'}), 404

    profile_data = {}
    if account.profile:
        profile_data = {
            'owner_name': account.profile.owner_name,
            'workshop_name': account.profile.workshop_name,
            'workshop_phone': account.profile.workshop_phone
        }

    return jsonify({
        'user': {
            'id': account.id,
            'email': account.email,
            **profile_data
        }
    }), 200

# =========================
# RUN APPLICATION
# =========================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )