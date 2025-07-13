# app/models.py
from . import db

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
    tanggal = db.Column(db.Date, nullable=False)
    
    # Kolom baru untuk jumlah pelanggaran
    jumlah_pelanggaran = db.Column(db.Integer, nullable=False, default=1)
    
    # Keterangan ini akan sama untuk satu bulan
    keterangan_bulanan = db.Column(db.String(255), nullable=True)
    riyadhoh = db.Column(db.String(255), nullable=True)
    status_riyadhoh = db.Column(db.String(20), nullable=False, default='Belum Lunas')
    
    # Foreign Key ke tabel santri
    santri_id = db.Column(db.Integer, db.ForeignKey('santri.id'), nullable=False)
    
    # Relasi
    santri = db.relationship('Santri', backref=db.backref('rekap_buku_sadar', lazy=True))

    def __repr__(self):
        return f'<Buku Sadar: {self.santri.nama_lengkap} - {self.tanggal}>'