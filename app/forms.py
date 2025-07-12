# app/forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed 
from wtforms import DateField, SelectField, SubmitField, StringField, TextAreaField, IntegerField
from wtforms.validators import DataRequired
from .models import Santri, SksMaster

class RekapSksForm(FlaskForm):
    tanggal = DateField('Tanggal', validators=[DataRequired()])
    # Pilihan akan diisi secara dinamis di routes
    santri = SelectField('Nama Santri', coerce=int, validators=[DataRequired()])
    sks = SelectField('SKS yang Diselesaikan', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Simpan')

class SantriForm(FlaskForm):
    nama_lengkap = StringField('Nama Lengkap', validators=[DataRequired()])
    alamat = TextAreaField('Alamat')
    nama_orang_tua = StringField('Nama Orang Tua (Opsional)')
    nama_pembimbing = StringField('Nama Pembimbing')
    kelas_saat_ini = StringField('Kelas Saat Ini (Halaqah)')
    kelas_sekolah = StringField('Kelas Sekolah Formal')
    kamar = StringField('Kamar')
    no_wa_wali = StringField('No. WhatsApp Wali (Contoh: 62812...)')
    submit = SubmitField('Tambah Santri')

class UploadExcelForm(FlaskForm):
    file = FileField(
        'File Excel', 
        validators=[
            FileRequired(),
            FileAllowed(['xlsx', 'xls'], 'Hanya file Excel (.xlsx, .xls) yang diizinkan!')
        ]
    )
    submit_upload = SubmitField('Impor')

class SksMasterForm(FlaskForm):
    nama_sks = StringField('Nama SKS', validators=[DataRequired()])
    submit_manual = SubmitField('Tambah SKS')

class AbsensiForm(FlaskForm):
    tanggal = DateField('Tanggal', validators=[DataRequired()])
    santri = SelectField('Nama Santri', coerce=int, validators=[DataRequired()])
    status = SelectField(
        'Status Kehadiran', 
        choices=[
            ('hadir', 'Hadir'),
            ('sakit', 'Sakit'),
            ('pulang', 'Pulang'),
            ('izin', 'Izin Lainnya'),
            ('alpa', 'Alpa')
        ],
        validators=[DataRequired()]
    )
    keterangan = StringField('Keterangan (jika izin atau sakit)')
    submit = SubmitField('Simpan Absensi')

class BukuSadarForm(FlaskForm):
    tanggal = DateField('Tanggal', validators=[DataRequired()])
    santri = SelectField('Nama Santri', coerce=int, validators=[DataRequired()])
    jumlah = IntegerField('Jumlah Alpa/Tidak Setor', default=1, validators=[DataRequired()])
    keterangan = StringField('Keterangan')
    riyadhoh = StringField('Riyadhoh / Sanksi')
    status_riyadhoh = SelectField(
        'Status Riyadhoh',
        choices=[
            ('Belum Lunas', 'Belum Lunas'),
            ('Lunas', 'Lunas')
        ],
        validators=[DataRequired()]
    )
    submit = SubmitField('Simpan Catatan')