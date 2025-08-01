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
    kategori = SelectField('Kategori Santri', choices=[
        ('santri aktif', 'Santri Aktif'),
        ('tidak aktif', 'Tidak Aktif'),
        ('pengurus', 'Pengurus (Aktif)'),
        ('az-zahro', 'Az-Zahro'),
        ('mbak ndalem', 'Mbak Ndalem'),
        ('lulusan darul lughoh', 'Lulusan Darul Lughoh')
    ], validators=[DataRequired()])
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
    status_lunas = SelectField('Status Lunas', choices=[
        ('Belum Lunas', 'Belum Lunas'),
        ('Lunas', 'Lunas')
    ])
    submit = SubmitField('Simpan Rekap Seminggu')

    # Fungsi validasi kustom yang baru
    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False

        nama_hari = ["Sabtu", "Minggu", "Senin", "Selasa", "Rabu", "Kamis"]
        form_valid = True
        
        # Loop melalui setiap isian harian
        for i, day_form in enumerate(self.days.entries):
            total_sesi = day_form.hadir.data + day_form.sakit_izin.data + day_form.alpa.data
            
            # --- LOGIKA KONDISIONAL BARU ---
            # i=0 Sabtu, i=1 Minggu, i=2 Senin, i=3 Selasa, i=4 Rabu, i=5 Kamis
            if i == 1 or i == 5:  # Jika hari adalah Minggu atau Kamis
                expected_total = 3
            elif i == 3: # Jika hari adalah Selasa
                expected_total = 2
            else:       # Untuk hari-hari lainnya (Sabtu, Senin, Rabu)
                expected_total = 4
            # --------------------------------

            if total_sesi != expected_total:
                error_message = f'Total sesi hari {nama_hari[i]} harus {expected_total}, bukan {total_sesi}.'
                day_form.hadir.errors.append(error_message)
                form_valid = False
        
        return form_valid
# app/forms.py

class BukuSadarHarianForm(NoCsrfForm):
    alpa = IntegerField('Alpa', default=0)
    telat = IntegerField('Telat', default=0)

# Form utama untuk rekap mingguan
class RekapBukuSadarMingguanForm(FlaskForm):
    santri = SelectField('Nama Santri', coerce=int, validators=[DataRequired()])
    tanggal_awal_minggu = DateField('Pilih Hari Sabtu di Minggu Tersebut', validators=[DataRequired()])
    
    days = FieldList(FormField(BukuSadarHarianForm), min_entries=6, max_entries=6)
    
    keterangan = StringField('Keterangan Tambahan Mingguan')
    status_lunas = SelectField('Status Lunas', choices=[('Belum Lunas', 'Belum Lunas'), ('Lunas', 'Lunas')])
    submit = SubmitField('Simpan Rekap Buku Sadar')
    
class KoreksiBukuSadarForm(FlaskForm):
    # FieldList untuk 6 hari aktif (Sabtu-Kamis)
    days = FieldList(FormField(BukuSadarHarianForm), min_entries=6, max_entries=6)
    
    keterangan = StringField('Keterangan Umum Mingguan')
    status_lunas = SelectField(
        'Status Lunas',
        choices=[('Belum Lunas', 'Belum Lunas'), ('Lunas', 'Lunas')],
        validators=[DataRequired()]
    )
    submit = SubmitField('Simpan Perubahan')

class LalaranHarianForm(NoCsrfForm):
    # Pilihan: Hadir (dikosongi), Alpa (A), Telat (T), Izin (I)
    status = SelectField('Status', choices=[('', 'Hadir'), ('A', 'Alpa'), ('T', 'Telat'), ('I', 'Izin')])

# Form utama untuk rekap mingguan
class RekapLalaranMingguanForm(FlaskForm):
    santri = SelectField('Nama Santri', coerce=int, validators=[DataRequired()])
    tanggal_awal_minggu = DateField('Pilih Hari Sabtu di Minggu Tersebut', validators=[DataRequired()])
    days = FieldList(FormField(LalaranHarianForm), min_entries=6, max_entries=6)
    submit = SubmitField('Simpan Rekap Lalaran')
