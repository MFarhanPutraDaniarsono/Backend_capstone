import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Mengizinkan koneksi dari aplikasi Flutter (HP/Browser)

# ================= CONFIG (Neon Database) =================
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_zS0AWJPD2Hcn@ep-silent-bar-aof30ey6-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# ================= MODEL DATABASE =================
class Owner(db.Model):
    __tablename__ = 'owners'
    id = db.Column(db.Integer, primary_key=True)
    nama_pemilik = db.Column(db.String(100), nullable=False)
    nomor_hp = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    nama_bengkel = db.Column(db.String(100), default='Bandung Jaya')
    alamat_bengkel = db.Column(db.Text, default='Belum diatur')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ================= API ENDPOINTS =================

# 1. API REGISTER (TER-UPDATE)
@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validasi input kosong
        if not data.get('nama_pemilik') or not data.get('nomor_hp') or not data.get('password'):
            return jsonify({"success": False, "message": "Semua kolom wajib diisi!"}), 400

        # Cek apakah nomor HP sudah terdaftar di database Neon
        user_exists = Owner.query.filter_by(nomor_hp=data['nomor_hp']).first()
        if user_exists:
            return jsonify({"success": False, "message": "Nomor HP sudah terdaftar!"}), 400
            
        # Enkripsi password sebelum disimpan
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
        
        new_owner = Owner(
            nama_pemilik=data['nama_pemilik'],
            nomor_hp=data['nomor_hp'],
            password=hashed_password
        )
        
        db.session.add(new_owner)
        db.session.commit()
        
        # FIX: Kembalikan payload data user gres untuk Auto-Login di Flutter
        return jsonify({
            "success": True, 
            "message": "Pendaftaran akun pemilik berhasil!",
            "data": {
                "nama_pemilik": new_owner.nama_pemilik,
                "nomor_hp": new_owner.nomor_hp,
                "nama_bengkel": new_owner.nama_bengkel,
                "alamat_bengkel": new_owner.alamat_bengkel
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# 2. API LOGIN
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('nomor_hp') or not data.get('password'):
            return jsonify({"success": False, "message": "Nomor HP dan password wajib diisi!"}), 400

        owner = Owner.query.filter_by(nomor_hp=data['nomor_hp']).first()
        
        # Validasi akun dan kecocokan hash password
        if owner and bcrypt.check_password_hash(owner.password, data['password']):
            return jsonify({
                "success": True,
                "message": "Login berhasil!",
                "data": {
                    "nama_pemilik": owner.nama_pemilik,
                    "nomor_hp": owner.nomor_hp,
                    "nama_bengkel": owner.nama_bengkel,
                    "alamat_bengkel": owner.alamat_bengkel
                }
            }), 200
            
        return jsonify({"success": False, "message": "Nomor HP atau password salah!"}), 400
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 3. API UPDATE DATA BENGKEL (PROFIL)
@app.route('/api/profil/bengkel', methods=['PUT'])
def update_bengkel():
    try:
        data = request.get_json()
        # Mencari berdasarkan nomor_hp yang dikirim dari Flutter
        owner = Owner.query.filter_by(nomor_hp=data.get('nomor_hp')).first()
        
        if not owner:
            return jsonify({"success": False, "message": "Akun pemilik tidak ditemukan!"}), 404
            
        owner.nama_bengkel = data.get('nama_bengkel', owner.nama_bengkel)
        owner.alamat_bengkel = data.get('alamat_bengkel', owner.alamat_bengkel)
        
        db.session.commit()
        return jsonify({"success": True, "message": "Data bisnis bengkel berhasil diperbarui!"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

# ================= RUN SERVER =================
if __name__ == '__main__':
    # Membuat tabel secara otomatis di Neon jika belum ada
    with app.app_context():
        db.create_all()
        
    # Dijalanankan di host 0.0.0.0 agar bisa diakses HP lewat kabel/Wi-Fi lokal
    app.run(host='0.0.0.0', port=5000, debug=True)