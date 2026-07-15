import os
import random
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ================= CONFIG (Neon Database, Token Fonnte & Path Absolut) =================
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_zS0AWJPD2Hcn@ep-silent-bar-aof30ey6-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Token WhatsApp Gateway (Fonnte)
FONNTE_TOKEN = 'AT6MUTqfshTFbRJeTNMg'

# Menggunakan Path Absolut agar Flask tidak tersesat saat melayani file foto ke HP
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'profile_pics')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

PRODUCT_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'product_pics')
os.makedirs(PRODUCT_UPLOAD_FOLDER, exist_ok=True)
app.config['PRODUCT_UPLOAD_FOLDER'] = PRODUCT_UPLOAD_FOLDER

KARYAWAN_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'karyawan_pics')
os.makedirs(KARYAWAN_UPLOAD_FOLDER, exist_ok=True)
app.config['KARYAWAN_UPLOAD_FOLDER'] = KARYAWAN_UPLOAD_FOLDER

ABSENSI_UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads', 'absensi_pics')
os.makedirs(ABSENSI_UPLOAD_FOLDER, exist_ok=True)
app.config['ABSENSI_UPLOAD_FOLDER'] = ABSENSI_UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ================= MODEL DATABASE =================

class OtpRecord(db.Model):
    __tablename__ = 'otp_records'
    id = db.Column(db.Integer, primary_key=True)
    nomor_hp = db.Column(db.String(20), nullable=False)
    otp_code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Owner(db.Model):
    __tablename__ = 'owners'
    id = db.Column(db.Integer, primary_key=True)
    nama_pemilik = db.Column(db.String(100), nullable=False)
    nomor_hp = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    nama_bengkel = db.Column(db.String(100), default='Bandung Jaya')
    alamat_bengkel = db.Column(db.Text, default='Belum diatur')
    nomor_hp_bengkel = db.Column(db.String(20), default='')
    url_foto_profil = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    nomor_hp_owner = db.Column(db.String(20), db.ForeignKey('owners.nomor_hp'), nullable=False)
    nama_kategori = db.Column(db.String(100), nullable=False)
    products = db.relationship('Product', backref='category', lazy=True, cascade="all, delete-orphan")

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    nomor_hp_owner = db.Column(db.String(20), db.ForeignKey('owners.nomor_hp'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    nama_produk = db.Column(db.String(150), nullable=False)
    harga_jual = db.Column(db.Integer, default=0)
    harga_beli = db.Column(db.Integer, default=0)
    stok = db.Column(db.Integer, default=0)
    kode_produk = db.Column(db.String(50), default='')
    catatan = db.Column(db.Text, default='')
    lokasi_rak = db.Column(db.String(50), default='')
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade="all, delete-orphan")

class ProductImage(db.Model):
    __tablename__ = 'product_images'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    url_foto = db.Column(db.Text, nullable=False)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    nomor_hp_owner = db.Column(db.String(20), db.ForeignKey('owners.nomor_hp'), nullable=False)
    nama_pelanggan = db.Column(db.String(100), nullable=False)
    nomor_telepon = db.Column(db.String(20), default='')
    plat_nomor = db.Column(db.String(20), default='')
    merek_motor = db.Column(db.String(50), default='') 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    vehicles = db.relationship('Vehicle', backref='customer', lazy=True, cascade="all, delete-orphan")

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)
    merk = db.Column(db.String(50), nullable=False)
    tipe = db.Column(db.String(50), default='')
    no_polisi = db.Column(db.String(20), default='')
    tahun = db.Column(db.String(10), default='')

class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    nomor_hp_owner = db.Column(db.String(20), db.ForeignKey('owners.nomor_hp'), nullable=False)
    nama = db.Column(db.String(100), nullable=False)
    posisi = db.Column(db.String(50), nullable=False) # 'Montir' or 'Admin'
    foto_path = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    attendances = db.relationship('Attendance', backref='employee', lazy=True, cascade="all, delete-orphan")

class Attendance(db.Model):
    __tablename__ = 'attendances'
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    waktu = db.Column(db.DateTime, default=datetime.utcnow)
    tipe = db.Column(db.String(20), nullable=False) # 'Masuk' or 'Pulang'
    foto_absen_path = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(100), nullable=False)
    kecocokan = db.Column(db.String(20), nullable=False)
    is_late = db.Column(db.Boolean, default=False)

class CashBook(db.Model):
    __tablename__ = 'cash_book'
    id = db.Column(db.Integer, primary_key=True)
    nomor_hp_owner = db.Column(db.String(20), db.ForeignKey('owners.nomor_hp'), nullable=False)
    tanggal = db.Column(db.DateTime, default=datetime.utcnow)
    tipe = db.Column(db.String(20), nullable=False) # 'Pemasukan' atau 'Pengeluaran'
    jumlah = db.Column(db.Integer, nullable=False)
    keterangan = db.Column(db.Text, default='')

# --- TABEL BARU UNTUK SERVIS & TRANSAKSI ---
class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    no_trx = db.Column(db.String(50), nullable=False)
    nomor_hp_owner = db.Column(db.String(20), db.ForeignKey('owners.nomor_hp'), nullable=False)
    
    # Info Kendaraan & Pelanggan
    nama_pelanggan = db.Column(db.String(100), default='Umum')
    merek_tipe_motor = db.Column(db.String(100), default='')
    plat_nomor = db.Column(db.String(20), default='')
    keluhan = db.Column(db.Text, default='')
    kilometer = db.Column(db.Integer, default=0)
    garansi = db.Column(db.String(50), default='')
    
    # Tagihan & Status
    total_tagihan = db.Column(db.Integer, default=0)
    status_transaksi = db.Column(db.String(50), default='Antrian') # Antrian, Dikerjakan, Selesai, dll
    status_pembayaran = db.Column(db.String(50), default='Belum Lunas') # Belum Lunas, Bayar Setengah, Lunas
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship('TransactionItem', backref='transaction', lazy=True, cascade="all, delete-orphan")

class TransactionItem(db.Model):
    __tablename__ = 'transaction_items'
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    tipe_item = db.Column(db.String(20), nullable=False) # 'Produk' atau 'Jasa'
    nama_item = db.Column(db.String(150), nullable=False)
    harga = db.Column(db.Integer, default=0)
    qty = db.Column(db.Integer, default=1)
    subtotal = db.Column(db.Integer, default=0)


# ================= API ENDPOINTS SYSTEM =================

@app.route('/api/request-otp', methods=['POST'])
def request_otp():
    try:
        data = request.get_json()
        nomor_hp = data.get('nomor_hp')
        
        if not nomor_hp:
            return jsonify({"success": False, "message": "Nomor HP wajib diisi!"}), 400
            
        if Owner.query.filter_by(nomor_hp=nomor_hp).first():
            return jsonify({"success": False, "message": "Nomor HP sudah terdaftar!"}), 400
            
        otp = str(random.randint(100000, 999999))
        
        OtpRecord.query.filter_by(nomor_hp=nomor_hp).delete()
        
        new_otp = OtpRecord(nomor_hp=nomor_hp, otp_code=otp)
        db.session.add(new_otp)
        db.session.commit()
        
        headers = {'Authorization': FONNTE_TOKEN}
        payload = {
            'target': nomor_hp,
            'message': f'*BMA VERIFIKASI*\n\nKode OTP pendaftaran Anda adalah: *{otp}*.\n\nJangan berikan kode ini kepada siapapun.',
            'countryCode': '62'
        }
        response = requests.post('https://api.fonnte.com/send', headers=headers, data=payload)
        
        if response.status_code == 200:
            return jsonify({"success": True, "message": "Kode OTP telah dikirim ke WhatsApp Anda!"}), 200
        else:
            return jsonify({"success": False, "message": "Gagal mengirim pesan WA dari sistem gateway."}), 500

    except Exception as e:
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        nomor_hp = data.get('nomor_hp')
        otp_input = data.get('otp_code')
        nama = data.get('nama_pemilik')
        password = data.get('password')
        
        if not all([nomor_hp, otp_input, nama, password]):
            return jsonify({"success": False, "message": "Semua data dan kode OTP wajib diisi!"}), 400
            
        valid_otp = OtpRecord.query.filter_by(nomor_hp=nomor_hp, otp_code=otp_input).first()
        if not valid_otp:
            return jsonify({"success": False, "message": "Kode OTP salah atau sudah kadaluarsa!"}), 400
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_owner = Owner(nama_pemilik=nama, nomor_hp=nomor_hp, password=hashed_password)
        db.session.add(new_owner)
        
        db.session.delete(valid_otp)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Verifikasi OTP sukses! Pendaftaran berhasil!"}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        owner = Owner.query.filter_by(nomor_hp=data.get('nomor_hp')).first()
        if owner and bcrypt.check_password_hash(owner.password, data.get('password', '')):
            return jsonify({
                "success": True,
                "data": {
                    "nama_pemilik": owner.nama_pemilik, "nomor_hp": owner.nomor_hp,
                    "nama_bengkel": owner.nama_bengkel, "alamat_bengkel": owner.alamat_bengkel,
                    "nomor_hp_bengkel": owner.nomor_hp_bengkel, "url_foto_profil": owner.url_foto_profil
                }
            }), 200
        return jsonify({"success": False, "message": "Nomor HP atau password salah!"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/update-profil', methods=['POST', 'PUT'])
def update_profil():
    try:
        data = request.get_json()
        nomor_hp = data.get('nomor_hp')
        owner = Owner.query.filter_by(nomor_hp=nomor_hp).first()
        
        if not owner:
            return jsonify({"success": False, "message": "Akun pemilik tidak ditemukan!"}), 404
        
        owner.nama_pemilik = data.get('nama_pemilik', owner.nama_pemilik)
        owner.nama_bengkel = data.get('nama_bengkel', owner.nama_bengkel)
        owner.alamat_bengkel = data.get('alamat_bengkel', owner.alamat_bengkel)
        owner.nomor_hp_bengkel = data.get('nomor_hp_bengkel', owner.nomor_hp_bengkel)
        
        db.session.commit()
        return jsonify({"success": True, "message": "Data bisnis berhasil diperbarui!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/upload-foto', methods=['POST'])
def upload_foto():
    try:
        nomor_hp = request.form.get('nomor_hp')
        owner = Owner.query.filter_by(nomor_hp=nomor_hp).first()
        
        if not owner:
            return jsonify({"success": False, "message": "Akun tidak ditemukan!"}), 404
            
        if 'foto' not in request.files:
            return jsonify({"success": False, "message": "Tidak ada file foto yang dikirim!"}), 400
            
        file = request.files['foto']
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            import time
            timestamp = int(time.time())
            filename_unik = f"profile_{nomor_hp}_{timestamp}.{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_unik))
            
            owner.url_foto_profil = f"/uploads/profile_pics/{filename_unik}"
            db.session.commit()
            
            return jsonify({"success": True, "message": "Foto profil berhasil diunggah!", "url_foto_profil": owner.url_foto_profil}), 200
            
        return jsonify({"success": False, "message": "Format file tidak didukung!"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/kategori', methods=['GET'])
def get_kategori():
    no_hp = request.args.get('nomor_hp')
    categories = Category.query.filter_by(nomor_hp_owner=no_hp).all()
    return jsonify({"success": True, "data": [{"id": c.id, "nama_kategori": c.nama_kategori} for c in categories]}), 200

@app.route('/api/kategori', methods=['POST'])
def add_kategori():
    data = request.get_json()
    new_cat = Category(nomor_hp_owner=data.get('nomor_hp'), nama_kategori=data.get('nama_kategori'))
    db.session.add(new_cat)
    db.session.commit()
    return jsonify({"success": True, "message": "Kategori berhasil disimpan"}), 201

@app.route('/api/produk', methods=['GET'])
def get_produk():
    try:
        no_hp = request.args.get('nomor_hp')
        products = Product.query.filter_by(nomor_hp_owner=no_hp).all()
        data = []
        for p in products:
            fotos = ProductImage.query.filter_by(product_id=p.id).all()
            list_foto = [img.url_foto for img in fotos]
            nama_kat = p.category.nama_kategori if p.category else "Tanpa Kategori"

            data.append({
                "id": p.id, "category_id": p.category_id, "nama_kategori": nama_kat,
                "nama_produk": p.nama_produk, "harga_jual": p.harga_jual, "harga_beli": p.harga_beli,
                "stok": p.stok, "kode_produk": p.kode_produk, "catatan": p.catatan, 
                "lokasi_rak": p.lokasi_rak, "fotos": list_foto  
            })
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/produk', methods=['POST'])
def add_produk():
    try:
        no_hp = request.form.get('nomor_hp')
        cat_id_raw = request.form.get('category_id')
        nama = request.form.get('nama_produk')
        
        harga_jual = int(request.form.get('harga_jual', 0)) if request.form.get('harga_jual', '').isdigit() else 0
        harga_beli = int(request.form.get('harga_beli', 0)) if request.form.get('harga_beli', '').isdigit() else 0
        stok = int(request.form.get('stok', 0)) if request.form.get('stok', '').isdigit() else 0
        
        if not no_hp or not nama or not cat_id_raw:
            return jsonify({"success": False, "message": "Nama produk dan Kategori wajib diisi!"}), 400
            
        new_prod = Product(
            nomor_hp_owner=no_hp, category_id=int(cat_id_raw), nama_produk=nama, 
            harga_jual=harga_jual, harga_beli=harga_beli, stok=stok, 
            kode_produk=request.form.get('kode_produk', ''), catatan=request.form.get('catatan', ''), lokasi_rak=request.form.get('lokasi_rak', '')
        )
        db.session.add(new_prod)
        db.session.flush() 
        
        if 'fotos' in request.files:
            files = request.files.getlist('fotos')
            for index, file in enumerate(files):
                if file and allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    filename_unik = f"prod_{new_prod.id}_{index}.{ext}"
                    file.save(os.path.join(app.config['PRODUCT_UPLOAD_FOLDER'], filename_unik))
                    db.session.add(ProductImage(product_id=new_prod.id, url_foto=f"/uploads/product_pics/{filename_unik}"))
                    
        db.session.commit()
        return jsonify({"success": True, "message": "Produk & Foto berhasil disimpan"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/produk/<int:id>', methods=['POST'])
def update_produk(id):
    try:
        no_hp = request.form.get('nomor_hp')
        cat_id_raw = request.form.get('category_id')
        nama = request.form.get('nama_produk')
        
        harga_jual = int(request.form.get('harga_jual', 0)) if request.form.get('harga_jual', '').isdigit() else 0
        harga_beli = int(request.form.get('harga_beli', 0)) if request.form.get('harga_beli', '').isdigit() else 0
        stok = int(request.form.get('stok', 0)) if request.form.get('stok', '').isdigit() else 0
        
        prod = Product.query.get(id)
        if not prod:
            return jsonify({"success": False, "message": "Produk tidak ditemukan!"}), 404
            
        prod.category_id = int(cat_id_raw)
        prod.nama_produk = nama
        prod.harga_jual = harga_jual
        prod.harga_beli = harga_beli
        prod.stok = stok
        prod.kode_produk = request.form.get('kode_produk', '')
        prod.catatan = request.form.get('catatan', '')
        prod.lokasi_rak = request.form.get('lokasi_rak', '')
        
        if 'fotos' in request.files:
            old_pics = ProductImage.query.filter_by(product_id=prod.id).all()
            for pic in old_pics:
                try:
                    file_path = os.path.join(BASE_DIR, pic.url_foto.lstrip('/'))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass
                db.session.delete(pic)
            
            files = request.files.getlist('fotos')
            for index, file in enumerate(files):
                if file and allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    filename_unik = f"prod_{prod.id}_{index}.{ext}"
                    file.save(os.path.join(app.config['PRODUCT_UPLOAD_FOLDER'], filename_unik))
                    db.session.add(ProductImage(product_id=prod.id, url_foto=f"/uploads/product_pics/{filename_unik}"))
                    
        db.session.commit()
        return jsonify({"success": True, "message": "Produk berhasil diperbarui"}), 200
    except Exception as e:
        db.session.rollback()
        print("Error update produk:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/pelanggan', methods=['GET'])
def get_pelanggan():
    try:
        no_hp = request.args.get('nomor_hp')
        customers = Customer.query.filter_by(nomor_hp_owner=no_hp).order_by(Customer.nama_pelanggan.asc()).all()
        data = []
        for c in customers:
            vehicle_list = []
            for v in c.vehicles:
                vehicle_list.append({
                    "id": v.id,
                    "merk": v.merk,
                    "tipe": v.tipe,
                    "no_polisi": v.no_polisi,
                    "tahun": v.tahun
                })
            data.append({
                "id": c.id, 
                "nama_pelanggan": c.nama_pelanggan, 
                "nomor_telepon": c.nomor_telepon,
                "plat_nomor": c.plat_nomor, 
                "merek_motor": c.merek_motor,
                "vehicles": vehicle_list
            })
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/pelanggan', methods=['POST'])
def add_pelanggan():
    try:
        data = request.get_json()
        no_hp = data.get('nomor_hp')
        nama = data.get('nama_pelanggan')
        phone = data.get('nomor_telepon', '')
        vehicles_data = data.get('vehicles', [])

        if not no_hp or not nama:
            return jsonify({"success": False, "message": "Nama pelanggan wajib diisi!"}), 400

        # Untuk kompatibilitas ke belakang: ambil kendaraan pertama
        merek_motor = ''
        plat_nomor = ''
        if vehicles_data:
            first_veh = vehicles_data[0]
            merk = first_veh.get('merk', '')
            tipe = first_veh.get('tipe', '')
            merek_motor = f"{merk} {tipe}".strip()
            plat_nomor = first_veh.get('no_polisi', '')

        new_cust = Customer(
            nomor_hp_owner=no_hp, 
            nama_pelanggan=nama, 
            nomor_telepon=phone, 
            plat_nomor=plat_nomor, 
            merek_motor=merek_motor
        )
        db.session.add(new_cust)
        db.session.flush() # Dapatkan ID pelanggan baru

        for v in vehicles_data:
            new_veh = Vehicle(
                customer_id=new_cust.id,
                merk=v.get('merk', ''),
                tipe=v.get('tipe', ''),
                no_polisi=v.get('no_polisi', ''),
                tahun=str(v.get('tahun', ''))
            )
            db.session.add(new_veh)

        db.session.commit()
        return jsonify({"success": True, "message": "Pelanggan berhasil ditambahkan!"}), 201
    except Exception as e:
        db.session.rollback()
        print("Error add pelanggan:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/pelanggan/<int:id>', methods=['PUT'])
def update_pelanggan(id):
    try:
        data = request.get_json()
        cust = Customer.query.get(id)
        if not cust:
            return jsonify({"success": False, "message": "Pelanggan tidak ditemukan!"}), 404

        cust.nama_pelanggan = data.get('nama_pelanggan', cust.nama_pelanggan)
        cust.nomor_telepon = data.get('nomor_telepon', cust.nomor_telepon)

        # Update kendaraan: hapus yang lama, masukkan yang baru
        vehicles_data = data.get('vehicles', [])
        Vehicle.query.filter_by(customer_id=cust.id).delete()

        # Untuk kompatibilitas ke belakang: ambil kendaraan pertama
        merek_motor = ''
        plat_nomor = ''
        if vehicles_data:
            first_veh = vehicles_data[0]
            merk = first_veh.get('merk', '')
            tipe = first_veh.get('tipe', '')
            merek_motor = f"{merk} {tipe}".strip()
            plat_nomor = first_veh.get('no_polisi', '')

        cust.merek_motor = merek_motor
        cust.plat_nomor = plat_nomor

        for v in vehicles_data:
            new_veh = Vehicle(
                customer_id=cust.id,
                merk=v.get('merk', ''),
                tipe=v.get('tipe', ''),
                no_polisi=v.get('no_polisi', ''),
                tahun=str(v.get('tahun', ''))
            )
            db.session.add(new_veh)

        db.session.commit()
        return jsonify({"success": True, "message": "Pelanggan berhasil diperbarui!"}), 200
    except Exception as e:
        db.session.rollback()
        print("Error update pelanggan:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/pelanggan/<int:id>', methods=['DELETE'])
def delete_pelanggan(id):
    try:
        cust = Customer.query.get(id)
        if not cust:
            return jsonify({"success": False, "message": "Pelanggan tidak ditemukan!"}), 404

        db.session.delete(cust)
        db.session.commit()
        return jsonify({"success": True, "message": "Pelanggan berhasil dihapus!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


# ================= ENDPOINT SERVIS & TRANSAKSI (BARU) =================

@app.route('/api/transaksi', methods=['POST'])
def buat_transaksi():
    try:
        data = request.get_json()
        nomor_hp_owner = data.get('nomor_hp_owner')
        
        if not nomor_hp_owner:
            return jsonify({"success": False, "message": "Nomor HP Owner wajib ada!"}), 400

        # Generate Nomor Transaksi (Contoh: TRX/260706/00001)
        tanggal_sekarang = datetime.now()
        prefix = f"TRX/{tanggal_sekarang.strftime('%y%m%d')}/"
        count_hari_ini = Transaction.query.filter(Transaction.no_trx.like(f"{prefix}%")).count()
        no_trx_baru = f"{prefix}{(count_hari_ini + 1):05d}"

        # Buat Header Transaksi
        new_trx = Transaction(
            no_trx=no_trx_baru,
            nomor_hp_owner=nomor_hp_owner,
            nama_pelanggan=data.get('nama_pelanggan', 'Umum'),
            merek_tipe_motor=data.get('merek_tipe_motor', ''),
            plat_nomor=data.get('plat_nomor', ''),
            keluhan=data.get('keluhan', ''),
            kilometer=int(data.get('kilometer', 0)),
            garansi=data.get('garansi', ''),
            total_tagihan=data.get('total_tagihan', 0),
            status_transaksi=data.get('status_transaksi', 'Antrian'),
            status_pembayaran=data.get('status_pembayaran', 'Belum Lunas')
        )
        db.session.add(new_trx)
        db.session.flush() # Flush untuk mendapatkan id transaksi baru

        # Masukkan Item (Produk/Jasa)
        items = data.get('items', [])
        for item in items:
            item_id = item.get('id')
            tipe_item = item.get('tipe', 'Jasa')
            qty = item.get('qty', 1)
            
            # Otomatis kurangi stok produk jika id barang dikirim
            if tipe_item == 'Produk' and item_id is not None:
                product = Product.query.get(item_id)
                if product:
                    product.stok = max(0, product.stok - qty)

            new_item = TransactionItem(
                transaction_id=new_trx.id,
                tipe_item=tipe_item,
                nama_item=item.get('nama', ''),
                harga=item.get('harga', 0),
                qty=qty,
                subtotal=item.get('subtotal', 0)
            )
            db.session.add(new_item)

        db.session.commit()
        return jsonify({
            "success": True, 
            "message": "Transaksi berhasil dibuat!",
            "data": {"no_trx": no_trx_baru}
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/transaksi', methods=['GET'])
def get_transaksi():
    try:
        no_hp = request.args.get('nomor_hp')
        transaksis = Transaction.query.filter_by(nomor_hp_owner=no_hp).order_by(Transaction.created_at.desc()).all()
        
        data_result = []
        for t in transaksis:
            # Ambil item detail
            items_data = [{
                "tipe": item.tipe_item,
                "nama": item.nama_item,
                "harga": item.harga,
                "qty": item.qty,
                "subtotal": item.subtotal
            } for item in t.items]

            data_result.append({
                "id": t.id,
                "no_trx": t.no_trx,
                "tanggal": t.created_at.strftime('%d %b %Y, %H:%M'),
                "nama_pelanggan": t.nama_pelanggan,
                "merek_tipe_motor": t.merek_tipe_motor,
                "plat_nomor": t.plat_nomor,
                "keluhan": t.keluhan,
                "kilometer": t.kilometer if hasattr(t, 'kilometer') else 0,
                "garansi": t.garansi if hasattr(t, 'garansi') else '',
                "total_tagihan": t.total_tagihan,
                "status_transaksi": t.status_transaksi,
                "status_pembayaran": t.status_pembayaran,
                "items": items_data
            })
            
        return jsonify({"success": True, "data": data_result}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/transaksi/<int:id>/status', methods=['PUT'])
def update_status_transaksi(id):
    try:
        data = request.get_json()
        trx = Transaction.query.get(id)
        if not trx:
            return jsonify({"success": False, "message": "Transaksi tidak ditemukan"}), 404

        if 'status_transaksi' in data:
            trx.status_transaksi = data['status_transaksi']
        if 'status_pembayaran' in data:
            trx.status_pembayaran = data['status_pembayaran']

        db.session.commit()
        return jsonify({"success": True, "message": "Status berhasil diperbarui!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/karyawan', methods=['GET'])
def get_karyawan():
    try:
        no_hp = request.args.get('nomor_hp')
        employees = Employee.query.filter_by(nomor_hp_owner=no_hp).order_by(Employee.nama.asc()).all()
        data = [{
            "id": e.id,
            "nama": e.nama,
            "posisi": e.posisi,
            "fotoPath": e.foto_path,
            "createdAt": e.created_at.isoformat()
        } for e in employees]
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/karyawan', methods=['POST'])
def add_karyawan():
    try:
        no_hp = request.form.get('nomor_hp')
        nama = request.form.get('nama')
        posisi = request.form.get('posisi')
        
        if not all([no_hp, nama, posisi]):
            return jsonify({"success": False, "message": "Nama, Posisi, dan Nomor HP Owner wajib diisi!"}), 400
            
        if 'foto' not in request.files:
            return jsonify({"success": False, "message": "File foto wajah wajib diunggah!"}), 400
            
        file = request.files['foto']
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            import time
            timestamp = int(time.time())
            filename_unik = f"emp_{no_hp}_{timestamp}.{ext}"
            file_path_relative = f"/uploads/karyawan_pics/{filename_unik}"
            file.save(os.path.join(app.config['KARYAWAN_UPLOAD_FOLDER'], filename_unik))
            
            new_emp = Employee(
                nomor_hp_owner=no_hp,
                nama=nama,
                posisi=posisi,
                foto_path=file_path_relative
            )
            db.session.add(new_emp)
            db.session.commit()
            
            return jsonify({"success": True, "message": "Karyawan berhasil didaftarkan!"}), 201
            
        return jsonify({"success": False, "message": "Format file tidak didukung!"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/karyawan/<int:id>', methods=['DELETE'])
def delete_karyawan(id):
    try:
        emp = Employee.query.get(id)
        if not emp:
            return jsonify({"success": False, "message": "Karyawan tidak ditemukan!"}), 404
            
        try:
            file_path = os.path.join(BASE_DIR, emp.foto_path.lstrip('/'))
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
            
        db.session.delete(emp)
        db.session.commit()
        return jsonify({"success": True, "message": "Data karyawan berhasil dihapus!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/absensi', methods=['GET'])
def get_absensi():
    try:
        no_hp = request.args.get('nomor_hp')
        employees = Employee.query.filter_by(nomor_hp_owner=no_hp).all()
        emp_ids = [e.id for e in employees]
        
        if not emp_ids:
            return jsonify({"success": True, "data": []}), 200
            
        attendances = Attendance.query.filter(Attendance.employee_id.in_(emp_ids)).order_by(Attendance.waktu.desc()).all()
        data = [{
            "id": a.id,
            "karyawanId": a.employee_id,
            "namaKaryawan": a.employee.nama,
            "posisi": a.employee.posisi,
            "waktu": a.waktu.isoformat(),
            "tipe": a.tipe,
            "fotoAbsenPath": a.foto_absen_path,
            "fotoDaftarPath": a.employee.foto_path,
            "status": a.status,
            "kecocokan": a.kecocokan,
            "isLate": a.is_late
        } for a in attendances]
        return jsonify({"success": True, "data": data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/absensi', methods=['POST'])
def add_absensi():
    try:
        employee_id = request.form.get('karyawan_id')
        tipe = request.form.get('tipe')
        status = request.form.get('status')
        kecocokan = request.form.get('kecocokan')
        is_late = request.form.get('is_late') == 'true'
        waktu_str = request.form.get('waktu')
        
        if not all([employee_id, tipe, status, kecocokan]):
            return jsonify({"success": False, "message": "Data absensi kurang lengkap!"}), 400
            
        if 'foto' not in request.files:
            return jsonify({"success": False, "message": "Foto absensi wajib diunggah!"}), 400
            
        file = request.files['foto']
        if file and allowed_file(file.filename):
            ext = file.filename.rsplit('.', 1)[1].lower()
            import time
            timestamp = int(time.time())
            filename_unik = f"att_{employee_id}_{timestamp}.{ext}"
            file_path_relative = f"/uploads/absensi_pics/{filename_unik}"
            file.save(os.path.join(app.config['ABSENSI_UPLOAD_FOLDER'], filename_unik))
            
            waktu_dt = datetime.fromisoformat(waktu_str) if waktu_str else datetime.utcnow()
            
            new_att = Attendance(
                employee_id=int(employee_id),
                waktu=waktu_dt,
                tipe=tipe,
                foto_absen_path=file_path_relative,
                status=status,
                kecocokan=kecocokan,
                is_late=is_late
            )
            db.session.add(new_att)
            db.session.commit()
            
            return jsonify({"success": True, "message": "Absensi berhasil dicatat!"}), 201
            
        return jsonify({"success": False, "message": "Format file tidak didukung!"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/absensi', methods=['DELETE'])
def clear_absensi():
    try:
        no_hp = request.args.get('nomor_hp')
        employees = Employee.query.filter_by(nomor_hp_owner=no_hp).all()
        emp_ids = [e.id for e in employees]
        
        if emp_ids:
            atts = Attendance.query.filter(Attendance.employee_id.in_(emp_ids)).all()
            for a in atts:
                try:
                    file_path = os.path.join(BASE_DIR, a.foto_absen_path.lstrip('/'))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except:
                    pass
            Attendance.query.filter(Attendance.employee_id.in_(emp_ids)).delete(synchronize_session=False)
            db.session.commit()
            
        return jsonify({"success": True, "message": "Semua riwayat absensi berhasil dihapus!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/buku-kas', methods=['GET'])
def get_buku_kas():
    try:
        no_hp = request.args.get('nomor_hp')
        
        cash_book_entries = CashBook.query.filter_by(nomor_hp_owner=no_hp).all()
        service_transactions = Transaction.query.filter_by(nomor_hp_owner=no_hp, status_pembayaran='Lunas').all()
        
        results = []
        for c in cash_book_entries:
            results.append({
                "id": f"cb-{c.id}",
                "is_manual": True,
                "manual_id": c.id,
                "tanggal": c.tanggal.isoformat(),
                "tipe": c.tipe,
                "jumlah": c.jumlah,
                "keterangan": c.keterangan
            })
            
        for t in service_transactions:
            results.append({
                "id": f"trx-{t.id}",
                "is_manual": False,
                "manual_id": None,
                "tanggal": t.created_at.isoformat(),
                "tipe": "Pemasukan",
                "jumlah": t.total_tagihan,
                "keterangan": f"Servis {t.merek_tipe_motor} - Nopol: {t.plat_nomor} ({t.nama_pelanggan})"
            })
            
        results.sort(key=lambda x: x['tanggal'], reverse=True)
        return jsonify({"success": True, "data": results}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/buku-kas', methods=['POST'])
def add_buku_kas():
    try:
        data = request.get_json()
        no_hp = data.get('nomor_hp')
        tipe = data.get('tipe')
        jumlah = int(data.get('jumlah', 0))
        keterangan = data.get('keterangan', '')
        tanggal_str = data.get('tanggal')
        
        if not no_hp or not tipe or jumlah <= 0:
            return jsonify({"success": False, "message": "Nomor HP, Tipe kas, dan Jumlah Kas wajib diisi valid!"}), 400
            
        tanggal_dt = datetime.fromisoformat(tanggal_str) if tanggal_str else datetime.utcnow()
        
        new_entry = CashBook(
            nomor_hp_owner=no_hp,
            tanggal=tanggal_dt,
            tipe=tipe,
            jumlah=jumlah,
            keterangan=keterangan
        )
        db.session.add(new_entry)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Catatan kas berhasil disimpan!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/buku-kas/<int:id>', methods=['DELETE'])
def delete_buku_kas(id):
    try:
        entry = CashBook.query.get(id)
        if not entry:
            return jsonify({"success": False, "message": "Data kas tidak ditemukan!"}), 404
            
        db.session.delete(entry)
        db.session.commit()
        return jsonify({"success": True, "message": "Catatan kas berhasil dihapus!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/uploads/karyawan_pics/<filename>')
def serve_karyawan_pic(filename):
    return send_from_directory(app.config['KARYAWAN_UPLOAD_FOLDER'], filename)

@app.route('/uploads/absensi_pics/<filename>')
def serve_absensi_pic(filename):
    return send_from_directory(app.config['ABSENSI_UPLOAD_FOLDER'], filename)


# ================= FILE SERVING ROUTES =================

@app.route('/uploads/profile_pics/<filename>')
def serve_profile_pic(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/uploads/product_pics/<filename>')
def serve_product_pic(filename):
    return send_from_directory(app.config['PRODUCT_UPLOAD_FOLDER'], filename)


if __name__ == '__main__':
    with app.app_context():
        db.create_all() 
        # Cek dan jalankan migrasi kolom transaksi, produk, dan pelanggan baru secara aman
        try:
            # Migrasi tabel transactions
            db.session.execute(db.text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS kilometer INTEGER DEFAULT 0;"))
            db.session.execute(db.text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS garansi VARCHAR(50) DEFAULT '';"))
            
            # Migrasi tabel products
            db.session.execute(db.text("ALTER TABLE products ADD COLUMN IF NOT EXISTS harga_beli INTEGER DEFAULT 0;"))
            db.session.execute(db.text("ALTER TABLE products ADD COLUMN IF NOT EXISTS catatan TEXT DEFAULT '';"))
            db.session.execute(db.text("ALTER TABLE products ADD COLUMN IF NOT EXISTS lokasi_rak VARCHAR(50) DEFAULT '';"))
            db.session.execute(db.text("ALTER TABLE products ADD COLUMN IF NOT EXISTS kode_produk VARCHAR(50) DEFAULT '';"))
            
            # Migrasi tabel customers
            db.session.execute(db.text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS plat_nomor VARCHAR(20) DEFAULT '';"))
            db.session.execute(db.text("ALTER TABLE customers ADD COLUMN IF NOT EXISTS merek_motor VARCHAR(50) DEFAULT '';"))
            
            db.session.commit()
            print("Migrasi skema database berhasil dijalankan.")
        except Exception as migration_error:
            db.session.rollback()
            print("Perhatian: Migrasi kolom dilewati:", migration_error)
            
    app.run(host='0.0.0.0', port=5000, debug=False)