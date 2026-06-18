from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS

import random
import requests
from datetime import datetime

from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)

app = Flask(__name__)
CORS(app)

# =========================
# CONFIG
# =========================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'secret123'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

FONNTE_TOKEN = 'AT6MUTqfshTFbRJeTNMg'

def format_phone(phone):
    phone = phone.replace('+', '').replace(' ', '')

    if phone.startswith('0'):
        phone = '62' + phone[1:]

    return phone

# =========================
# JWT DEBUGGING
# =========================

@jwt.invalid_token_loader
def invalid_token_callback(error):

    print("\n====================")
    print("JWT INVALID TOKEN")
    print(error)
    print("====================\n")

    return jsonify({
        "msg": error
    }), 422


@jwt.unauthorized_loader
def missing_token_callback(error):

    print("\n====================")
    print("JWT MISSING TOKEN")
    print(error)
    print("====================\n")

    return jsonify({
        "msg": error
    }), 401


@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):

    print("\n====================")
    print("JWT EXPIRED")
    print(jwt_payload)
    print("====================\n")

    return jsonify({
        "msg": "Token expired"
    }), 401

# =========================
# MODEL USER
# =========================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    owner_name = db.Column(db.String(100))

    owner_phone = db.Column(
        db.String(15),
        unique=True,
        nullable=False
    )

    workshop_name = db.Column(db.String(100))
    workshop_phone = db.Column(db.String(15))

    password = db.Column(
        db.String(255),
        nullable=False
    )

    is_verified = db.Column(
        db.Boolean,
        default=False
    )

# =========================
# MODEL OTP
# =========================
class OTP(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    phone = db.Column(
        db.String(15),
        nullable=False
    )

    otp_code = db.Column(
        db.String(6),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    verified = db.Column(
        db.Boolean,
        default=False
    )

# =========================
# REGISTER
# =========================
@app.route('/register', methods=['POST'])
def register():

    data = request.get_json()

    owner_name = data.get('owner_name')
    owner_phone = data.get('owner_phone')

    workshop_name = data.get('workshop_name')
    workshop_phone = data.get('workshop_phone')

    password = data.get('password')

    if not owner_name or not owner_phone or not password:
        return jsonify({
            'message': 'Data tidak lengkap'
        }), 400

    owner_phone = format_phone(owner_phone)

    if workshop_phone:
        workshop_phone = format_phone(workshop_phone)

    user = User.query.filter_by(
        owner_phone=owner_phone
    ).first()

    if user:
        return jsonify({
            'message': 'Nomor sudah terdaftar'
        }), 400

    hashed_pw = bcrypt.generate_password_hash(
        password
    ).decode('utf-8')

    new_user = User(
        owner_name=owner_name,
        owner_phone=owner_phone,
        workshop_name=workshop_name,
        workshop_phone=workshop_phone,
        password=hashed_pw,
        is_verified=False
    )

    db.session.add(new_user)
    db.session.commit()

    otp = str(random.randint(100000, 999999))

    otp_data = OTP(
        phone=owner_phone,
        otp_code=otp
    )

    db.session.add(otp_data)
    db.session.commit()

    print(f'\nOTP untuk {owner_phone}: {otp}\n')

    try:
        url = 'https://api.fonnte.com/send'

        payload = {
            'target': owner_phone,
            'message': f'''
Kode OTP Anda: {otp}

Jangan berikan kode ini kepada siapa pun.
Kode berlaku selama 5 menit.
'''
        }

        headers = {
            'Authorization': FONNTE_TOKEN 
        }

        response = requests.post(
            url,
            data=payload,
            headers=headers
        )

        print(response.text)

    except Exception as e:
        print(f'Gagal mengirim WhatsApp: {e}')

    return jsonify({
        'message': 'Registrasi berhasil',
        'phone': owner_phone
    }), 201

# =========================
# LOGIN PASSWORD
# =========================
@app.route('/login', methods=['POST'])
def login():

    data = request.get_json()

    phone = data.get('phone')
    password = data.get('password')

    if not phone or not password:
        return jsonify({
            'message': 'Data tidak lengkap'
        }), 400

    phone = format_phone(phone)

    user = User.query.filter_by(
        owner_phone=phone
    ).first()

    if not user:
        return jsonify({
            'message': 'User tidak ditemukan'
        }), 404

    if not user.is_verified:
        return jsonify({
            'message': 'Nomor belum verifikasi OTP'
        }), 403

    if not bcrypt.check_password_hash(
        user.password,
        password
    ):
        return jsonify({
            'message': 'Password salah'
        }), 401

    token = create_access_token(
        identity=str(user.id)
    )

    return jsonify({
        'message': 'Login berhasil',
        'token': token,
        'user': {
            'id': user.id,
            'owner_name': user.owner_name,
            'owner_phone': user.owner_phone,
            'workshop_name': user.workshop_name,
            'workshop_phone': user.workshop_phone
        }
    }), 200

# =========================
# SEND OTP WHATSAPP
# =========================
@app.route('/send-otp', methods=['POST'])
def send_otp():

    data = request.get_json()

    phone = data.get('phone')

    if not phone:
        return jsonify({
            'message': 'Nomor wajib diisi'
        }), 400

    phone = format_phone(phone)

    user = User.query.filter_by(
        owner_phone=phone
    ).first()

    if not user:
        return jsonify({
            'message': 'User tidak ditemukan'
        }), 404

    otp = str(random.randint(100000, 999999))

    otp_data = OTP(
        phone=phone,
        otp_code=otp
    )

    db.session.add(otp_data)
    db.session.commit()

    print(f'\nOTP untuk {phone}: {otp}\n')

    try:
        url = 'https://api.fonnte.com/send'

        payload = {
            'target': phone,
            'message': f'''
Kode OTP Anda: {otp}

Jangan berikan kode ini kepada siapa pun.
'''
        }

        headers = {
            'Authorization': FONNTE_TOKEN
        }

        response = requests.post(
            url,
            data=payload,
            headers=headers
        )

        print(response.text)

    except Exception as e:
        print(f'Gagal mengirim WhatsApp: {e}')

    return jsonify({
        'message': 'OTP berhasil dikirim'
    }), 200

    # =====================
    # TESTING LOKAL
    # =====================
    print(f"\nOTP untuk {phone}: {otp}\n")

    # =====================
    # AKTIFKAN JIKA PAKAI FONNTE
    # =====================
    """
    url = "https://api.fonnte.com/send"

    payload = {
        "target": phone,
        "message": f"Kode OTP Anda adalah {otp}"
    }

    headers = {
        "Authorization": "TOKEN_FONNTE_KAMU"
    }

    requests.post(
        url,
        data=payload,
        headers=headers
    )
    """

    return jsonify({
        'message': 'OTP berhasil dikirim'
    })

# =========================
# VERIFY OTP
# =========================
@app.route('/verify-otp', methods=['POST'])
def verify_otp():

    data = request.get_json()

    phone = data.get('phone')
    otp = data.get('otp')

    if not phone or not otp:
        return jsonify({
            'message': 'Data tidak lengkap'
        }), 400

    phone = format_phone(phone)

    otp_data = OTP.query.filter_by(
        phone=phone,
        otp_code=otp,
        verified=False
    ).order_by(
        OTP.created_at.desc()
    ).first()

    if not otp_data:
        return jsonify({
            'message': 'OTP salah'
        }), 400

    otp_data.verified = True

    user = User.query.filter_by(
        owner_phone=phone
    ).first()

    if not user:
        return jsonify({
            'message': 'Nomor belum terdaftar'
        }), 404

    user.is_verified = True

    db.session.commit()

    token = create_access_token(
        identity=str(user.id)
    )

    return jsonify({
        'message': 'OTP valid',
        'token': token,
        'user': {
            'id': user.id,
            'owner_name': user.owner_name,
            'owner_phone': user.owner_phone,
            'workshop_name': user.workshop_name,
            'workshop_phone': user.workshop_phone
        }
    }), 200

# =========================
# PROFILE
# =========================

# =========================
# DEBUG HEADER
# =========================
@app.route('/debug-header', methods=['GET'])
def debug_header():

    auth_header = request.headers.get(
        "Authorization"
    )

    print("\n====================")
    print("AUTH HEADER")
    print(auth_header)
    print("====================\n")

    return jsonify({
        "authorization": auth_header
    }), 200


# =========================
# TEST TOKEN
# =========================
@app.route('/test-token', methods=['GET'])
@jwt_required()
def test_token():

    identity = get_jwt_identity()

    print("\n====================")
    print("JWT IDENTITY")
    print(identity)
    print("====================\n")

    return jsonify({
        "identity": identity
    }), 200

@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():

    user_id = get_jwt_identity()

    user = User.query.get(
        int(user_id)
    )

    if not user:
        return jsonify({
            'message': 'User tidak ditemukan'
        }), 404

    return jsonify({
        'user': {
            'id': user.id,
            'owner_name': user.owner_name,
            'owner_phone': user.owner_phone,
            'workshop_name': user.workshop_name,
            'workshop_phone': user.workshop_phone
        }
})

# =========================
# RUN
# =========================
if __name__ == '__main__':

    with app.app_context():
        db.create_all()

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )