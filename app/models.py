# app/models.py
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin 

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(256))
    # Nanti kita bisa tambahkan kolom 'role' ('admin' atau 'wali')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

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

    def __repr__(self):
        return f'<Santri {self.nama_lengkap}>'

class SksMaster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama_sks = db.Column(db.String(150), unique=True, nullable=False)

class RekapSks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False)
    santri_id = db.Column(db.Integer, db.ForeignKey('santri.id'), nullable=False)
    sks_id = db.Column(db.Integer, db.ForeignKey('sks_master.id'), nullable=False)

    # Relasi untuk mempermudah query
    santri = db.relationship('Santri', backref=db.backref('rekap_sks', lazy=True))
    sks = db.relationship('SksMaster', backref=db.backref('rekap_sks', lazy=True))

class RekapAbsensi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tanggal = db.Column(db.Date, nullable=False)
    
    # Kolom baru untuk menyimpan jumlah sesi
    jumlah_hadir = db.Column(db.Integer, nullable=False, default=4)
    jumlah_sakit_izin = db.Column(db.Integer, nullable=False, default=0)
    jumlah_alpa = db.Column(db.Integer, nullable=False, default=0)
    
    # Keterangan ini akan sama untuk satu minggu
    keterangan_mingguan = db.Column(db.String(255), nullable=True)
    
    # Foreign Key ke tabel santri
    santri_id = db.Column(db.Integer, db.ForeignKey('santri.id'), nullable=False)
    
    # Relasi untuk mempermudah query
    santri = db.relationship('Santri', backref=db.backref('rekap_absensi', lazy=True))

    def __repr__(self):
        return f'<Absensi {self.santri.nama_lengkap} - {self.tanggal}>'
    
class RekapBukuSadar(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # Penanda unik untuk rekap mingguan per santri
    santri_id = db.Column(db.Integer, db.ForeignKey('santri.id'), nullable=False)
    tanggal_awal_minggu = db.Column(db.Date, nullable=False)

    # Kolom untuk data pelengkap mingguan
    keterangan = db.Column(db.String(255), nullable=True)
    riyadhoh = db.Column(db.String(255), nullable=True)
    status_lunas = db.Column(db.String(20), nullable=False, default='Belum Lunas')

    # Membuat constraint agar setiap santri hanya punya satu rekap per minggu
    __table_args__ = (db.UniqueConstraint('santri_id', 'tanggal_awal_minggu', name='_santri_minggu_uc'),)

    def __repr__(self):
        return f'<Buku Sadar Mingguan: {self.santri_id} - {self.tanggal_awal_minggu}>'