# app/models.py
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin 

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False, default='admin') # Kolom role sudah ada, bagus!

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class RekapLalaran(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(1), nullable=False) # 'A', 'T', 'I'
    
    santri_id = db.Column(db.Integer, db.ForeignKey('santri.id', ondelete='CASCADE'), nullable=False)
    
    # Definisikan relasi dua arah
    santri = db.relationship('Santri', back_populates='rekap_lalaran')

    def __repr__(self):
        return f'<Lalaran {self.santri.nama_lengkap} - {self.status}>'

class Santri(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_lengkap = db.Column(db.String(100), nullable=False)
    alamat = db.Column(db.String(255))
    nama_orang_tua = db.Column(db.String(100))
    nama_pembimbing = db.Column(db.String(100))
    kelas_saat_ini = db.Column(db.String(50))
    kelas_sekolah = db.Column(db.String(50))
    kamar = db.Column(db.String(50))
    no_wa_wali = db.Column(db.String(20), nullable=True)
    kategori = db.Column(db.String(50), nullable=False, default='santri aktif')

    # Relasi dua arah ke tabel anak
    rekap_sks = db.relationship('RekapSks', back_populates='santri', cascade="all, delete-orphan")
    rekap_absensi = db.relationship('RekapAbsensi', back_populates='santri', cascade="all, delete-orphan")
    rekap_buku_sadar = db.relationship('RekapBukuSadar', back_populates='santri', cascade="all, delete-orphan")
    rekap_lalaran = db.relationship('RekapLalaran', back_populates='santri', cascade="all, delete-orphan")


    def __repr__(self):
        return f'<Santri {self.nama_lengkap}>'

class SksMaster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_sks = db.Column(db.String(150), unique=True, nullable=False)
    # Tambahkan relasi balik ke RekapSks
    rekap_sks = db.relationship('RekapSks', backref='sks_master')

class RekapSks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False)
    
    # --- PERBAIKAN DI SINI ---
    # Cukup satu definisi santri_id, gabungkan ondelete='CASCADE'
    santri_id = db.Column(db.Integer, db.ForeignKey('santri.id', ondelete='CASCADE'), nullable=False)
    sks_id = db.Column(db.Integer, db.ForeignKey('sks_master.id'), nullable=False)

    # Definisikan relasi dua arah
    santri = db.relationship('Santri', back_populates='rekap_sks')

class RekapAbsensi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False)
    
    # Kolom jumlah sesi
    jumlah_hadir = db.Column(db.Integer, nullable=False, default=4)
    jumlah_sakit_izin = db.Column(db.Integer, nullable=False, default=0)
    jumlah_alpa = db.Column(db.Integer, nullable=False, default=0)
    
    # Kolom baru untuk info mingguan
    keterangan_mingguan = db.Column(db.String(255), nullable=True)
    riyadhoh = db.Column(db.String(255), nullable=True)
    status_lunas = db.Column(db.String(20), nullable=False, default='Belum Lunas')
    
    # Foreign Key dan relasi (tidak berubah)
    santri_id = db.Column(db.Integer, db.ForeignKey('santri.id', ondelete='CASCADE'), nullable=False)
    santri = db.relationship('Santri', back_populates='rekap_absensi')

    def __repr__(self):
        return f'<Absensi {self.santri.nama_lengkap} - {self.tanggal}>'
    
class RekapBukuSadar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False)

    # Kolom baru untuk alpa dan telat
    jumlah_alpa = db.Column(db.Integer, default=0)
    jumlah_telat = db.Column(db.Integer, default=0)

    # Keterangan dan riyadhoh akan sama untuk satu minggu
    keterangan_mingguan = db.Column(db.String(255), nullable=True)
    riyadhoh = db.Column(db.String(255), nullable=True)
    status_lunas = db.Column(db.String(20), nullable=False, default='Belum Lunas')

    santri_id = db.Column(db.Integer, db.ForeignKey('santri.id', ondelete='CASCADE'), nullable=False)
    santri = db.relationship('Santri', back_populates='rekap_buku_sadar')

    def __repr__(self):
        return f'<Buku Sadar Harian: {self.santri.nama_lengkap} - {self.tanggal}>'