# app/forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed 
from wtforms import DateField, SelectField, SubmitField, StringField, TextAreaField, IntegerField, PasswordField
from wtforms.validators import DataRequired, ValidationError
from .models import Santri, SksMaster
from wtforms import Form as NoCsrfForm, FieldList, FormField

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

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
    
class AbsensiHarianForm(NoCsrfForm):
    hadir = IntegerField('Hadir', default=4)
    sakit_izin = IntegerField('Sakit/Izin', default=0)
    alpa = IntegerField('Alpa', default=0)

# Form utama yang menggunakan form harian di atas
class RekapAbsensiHarianForm(FlaskForm):
    santri = SelectField('Nama Santri', coerce=int, validators=[DataRequired()])
    tanggal_awal_minggu = DateField('Pilih Hari Sabtu di Minggu Tersebut', validators=[DataRequired()])
    
    days = FieldList(FormField(AbsensiHarianForm), min_entries=6, max_entries=6)
    
    keterangan = StringField('Keterangan Tambahan Mingguan')
    submit = SubmitField('Simpan Rekap Seminggu')

    # Fungsi validasi kustom yang baru
    def validate(self, **kwargs):
        # Jalankan validasi bawaan terlebih dahulu
        if not super().validate(**kwargs):
            return False

        nama_hari = ["Sabtu", "Minggu", "Senin", "Selasa", "Rabu", "Kamis"]
        form_valid = True
        
        # Loop melalui setiap isian harian
        for i, day_form in enumerate(self.days.entries):
            total_sesi = day_form.hadir.data + day_form.sakit_izin.data + day_form.alpa.data
            
            # Jika total sesi untuk satu hari tidak sama dengan 4
            if total_sesi != 4:
                # Tambahkan pesan error spesifik ke field 'hadir' pada hari tersebut
                error_message = f'Total sesi hari {nama_hari[i]} harus 4, bukan {total_sesi}.'
                day_form.hadir.errors.append(error_message)
                form_valid = False
        
        return form_valid
    
class KoreksiBukuSadarForm(FlaskForm):
    # FieldList untuk 6 hari aktif
    days = FieldList(FormField(AbsensiHarianForm), min_entries=6, max_entries=6)
    
    keterangan = StringField('Keterangan Umum Mingguan')
    riyadhoh = StringField('Riyadhoh / Sanksi')
    status_lunas = SelectField(
        'Status Lunas',
        choices=[('Belum Lunas', 'Belum Lunas'), ('Lunas', 'Lunas')],
        validators=[DataRequired()]
    )
    submit = SubmitField('Simpan Koreksi')