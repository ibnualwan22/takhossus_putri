import io
import os
import calendar
import urllib.parse
import locale
try:
    locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8')
except locale.Error:
    try:
        # Fallback untuk lingkungan Windows
        locale.setlocale(locale.LC_TIME, 'Indonesian_indonesia.1252')
    except locale.Error:
        # Jika keduanya gagal, cetak peringatan dan lanjutkan tanpa crash
        print("Peringatan: Locale Bahasa Indonesia tidak ditemukan. Menggunakan locale default sistem.")
        pass
from datetime import date, datetime, timedelta
from collections import defaultdict

# 2. Pustaka Pihak Ketiga (Flask, SQLAlchemy, Pandas, dll)
from flask import (Blueprint, render_template, redirect, url_for, 
                   flash, request, send_file)
from sqlalchemy import extract, func
import pandas as pd
import numpy as np
from flask_login import login_required 

# 3. Impor dari Aplikasi Lokal Anda
from . import db
from .models import (Santri, SksMaster, RekapSks, RekapAbsensi, 
                     RekapBukuSadar)
from .forms import (RekapSksForm, SantriForm, UploadExcelForm, 
                    SksMasterForm, RekapAbsensiHarianForm, KoreksiBukuSadarForm )


# 1. Buat Blueprint untuk admin
# Semua URL di file ini akan diawali dengan /admin
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    # 1. Hitung jumlah santri aktif
    jumlah_santri = Santri.query.count()

    # 2. Hitung jumlah SKS yang terdaftar
    jumlah_sks = SksMaster.query.count()

    # PASTIKAN BARIS INI ADA
    today = date.today()

    # 3. Hitung jumlah absensi yang diinput HARI INI
    absen_hari_ini = RekapAbsensi.query.filter_by(tanggal=today).count()

    # 4. Hitung jumlah rekap buku sadar yang dibuat untuk MINGGU INI
    start_of_week = today - timedelta(days=(today.weekday() + 2) % 7)
    sadar_minggu_ini = RekapBukuSadar.query.filter_by(tanggal_awal_minggu=start_of_week).count()

    # Kirim semua data statistik ke template
    return render_template(
        'admin_dashboard.html',
        title="Dashboard Admin",
        jumlah_santri=jumlah_santri,
        jumlah_sks=jumlah_sks,
        absen_hari_ini=absen_hari_ini,
        sadar_minggu_ini=sadar_minggu_ini
    )

# Tambahkan juga rute ini agar /admin langsung mengarah ke dashboard
@admin_bp.route('/')
@login_required
def admin_index():
    return redirect(url_for('admin.admin_dashboard'))

# 2. Buat rute untuk halaman input rekap SKS
@admin_bp.route('/rekap/sks', methods=['GET', 'POST'])
def input_rekap_sks():
    form = RekapSksForm()
    
    # 3. Isi pilihan dropdown (choices) dari database
    # Ini akan mengambil semua data santri dan SKS untuk ditampilkan di form
    form.santri.choices = [(s.id, s.nama_lengkap) for s in Santri.query.order_by('nama_lengkap').all()]
    form.sks.choices = [(sks.id, sks.nama_sks) for sks in SksMaster.query.order_by('nama_sks').all()]

    # 4. Logika saat form di-submit (tombol 'Simpan' diklik)
    if form.validate_on_submit():
        # Buat objek baru dari model RekapSks
        rekap = RekapSks(
            tanggal=form.tanggal.data,
            santri_id=form.santri.data,
            sks_id=form.sks.data
        )
        # Simpan ke database
        db.session.add(rekap)
        db.session.commit()
        
        flash('Rekap SKS berhasil disimpan!', 'success')
        return redirect(url_for('admin.input_rekap_sks')) # Kembali ke halaman yang sama

    # 5. Tampilkan halaman HTML jika metodenya GET (pertama kali dibuka)
    return render_template('input_rekap_sks.html', title="Input Rekap SKS", form=form)

@admin_bp.route('/santri/tambah', methods=['GET', 'POST'])
@login_required 
def tambah_santri():
    form = SantriForm()
    upload_form = UploadExcelForm()

    # Logika untuk form input manual
    if form.submit.data and form.validate_on_submit():
        santri_baru = Santri(
            nama_lengkap=form.nama_lengkap.data,
            alamat=form.alamat.data,
            nama_orang_tua=form.nama_orang_tua.data,
            nama_pembimbing=form.nama_pembimbing.data,
            kelas_saat_ini=form.kelas_saat_ini.data,
            kelas_sekolah=form.kelas_sekolah.data,
            kamar=form.kamar.data,
            no_wa_wali=form.no_wa_wali.data,
        )
        db.session.add(santri_baru)
        db.session.commit()
        flash('Santri baru berhasil ditambahkan secara manual!', 'success')
        return redirect(url_for('admin.tambah_santri'))

    # Logika untuk form upload excel
    if upload_form.submit_upload.data and upload_form.validate_on_submit():
        file = upload_form.file.data
        try:
            # Baca file excel
            df = pd.read_excel(file).replace({np.nan: None})
            
            # Looping setiap baris di excel dan masukkan ke DB
            for index, row in df.iterrows():
                santri_excel = Santri(
                    nama_lengkap=row['nama_lengkap'],
                    alamat=row.get('alamat', None), # .get untuk kolom opsional
                    nama_orang_tua=row.get('nama_orang_tua', None),
                    nama_pembimbing=row.get('nama_pembimbing', None),
                    kelas_saat_ini=row.get('kelas_saat_ini', None),
                    kelas_sekolah=row.get('kelas_sekolah', None),
                    kamar=row.get('kamar', None),
                    no_wa_wali=row.get('no_wa_wali', None)
                )
                db.session.add(santri_excel)
            
            db.session.commit()
            flash(f'{len(df)} santri berhasil diimpor dari Excel!', 'success')
        except Exception as e:
            flash(f'Terjadi error saat mengimpor file: {e}', 'danger')
        
        return redirect(url_for('admin.tambah_santri'))

    return render_template(
        'input_santri.html', 
        title="Tambah Santri Baru", 
        form=form, 
        upload_form=upload_form  # Kirim form kedua ke template
    )
@admin_bp.route('/santri')
@login_required 
def daftar_santri():
    # 1. Ambil semua data santri dari database, urutkan berdasarkan nama
    semua_santri = Santri.query.order_by(Santri.nama_lengkap).all()
    
    # 2. Kirim data tersebut ke template HTML
    return render_template(
        'daftar_santri.html', 
        title="Daftar Santri Aktif", 
        santri_list=semua_santri
    )

@admin_bp.route('/santri/hapus/<int:id>', methods=['GET', 'POST'])
@login_required 
def hapus_santri(id):
    santri_untuk_dihapus = Santri.query.get_or_404(id)
    
    # Keamanan: Cek apakah santri punya data terkait sebelum menghapus
    if santri_untuk_dihapus.rekap_sks or santri_untuk_dihapus.rekap_absensi or santri_untuk_dihapus.rekap_buku_sadar:
        flash('Santri tidak bisa dihapus karena sudah memiliki data riwayat (SKS, Absensi, atau Buku Sadar).', 'danger')
        return redirect(url_for('admin.daftar_santri'))

    try:
        db.session.delete(santri_untuk_dihapus)
        db.session.commit()
        flash('Data santri berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Terjadi error saat menghapus data: {e}', 'danger')

    return redirect(url_for('admin.daftar_santri'))

@admin_bp.route('/santri/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_santri(id):
    santri = Santri.query.get_or_404(id)
    form = SantriForm(obj=santri) # 'obj=santri' akan mengisi form dengan data santri

    if form.validate_on_submit():
        # Update data santri dari form
        santri.nama_lengkap = form.nama_lengkap.data
        santri.alamat = form.alamat.data
        santri.nama_orang_tua = form.nama_orang_tua.data
        santri.nama_pembimbing = form.nama_pembimbing.data
        santri.kelas_saat_ini = form.kelas_saat_ini.data
        santri.kelas_sekolah = form.kelas_sekolah.data
        santri.kamar = form.kamar.data
        santri.no_wa_wali = form.no_wa_wali.data
        
        db.session.commit()
        flash('Data santri berhasil diperbarui!', 'success')
        return redirect(url_for('admin.daftar_santri'))

    # Saat pertama kali halaman dibuka (GET), tampilkan form yang sudah terisi
    return render_template('edit_santri.html', title="Edit Data Santri", form=form)

@admin_bp.route('/sks', methods=['GET', 'POST'])
@login_required
def kelola_sks():
    form = SksMasterForm()
    upload_form = UploadExcelForm()

    # Logika untuk form tambah manual
    if form.submit_manual.data and form.validate_on_submit():
        sks_baru = SksMaster(nama_sks=form.nama_sks.data)
        db.session.add(sks_baru)
        db.session.commit()
        flash('SKS baru berhasil ditambahkan!', 'success')
        return redirect(url_for('admin.kelola_sks'))

    # Logika untuk impor excel
    if upload_form.submit_upload.data and upload_form.validate_on_submit():
        file = upload_form.file.data
        try:
            df = pd.read_excel(file).replace({np.nan: None})
            # Pastikan excel punya kolom 'nama_sks'
            for index, row in df.iterrows():
                sks_excel = SksMaster(nama_sks=row['nama_sks'])
                db.session.add(sks_excel)
            
            db.session.commit()
            flash(f'{len(df)} SKS berhasil diimpor dari Excel!', 'success')
        except Exception as e:
            flash(f'Terjadi error saat mengimpor file: {e}', 'danger')
        
        return redirect(url_for('admin.kelola_sks'))

    # Ambil semua data SKS untuk ditampilkan di tabel
    semua_sks = SksMaster.query.order_by(SksMaster.nama_sks).all()

    return render_template(
        'kelola_sks.html',
        title="Kelola Master SKS",
        form=form,
        upload_form=upload_form,
        sks_list=semua_sks
    )

@admin_bp.route('/rekap/absensi', methods=['GET', 'POST'])
@login_required
def input_rekap_absensi():
    form = RekapAbsensiHarianForm()
    form.santri.choices = [(s.id, s.nama_lengkap) for s in Santri.query.order_by('nama_lengkap').all()]

    if form.validate_on_submit():
        santri_id = form.santri.data
        start_date = form.tanggal_awal_minggu.data
        keterangan_mingguan = form.keterangan.data

        # Hapus data lama untuk minggu tersebut
        end_date = start_date + timedelta(days=6)
        RekapAbsensi.query.filter(
            RekapAbsensi.santri_id == santri_id,
            RekapAbsensi.tanggal.between(start_date, end_date)
        ).delete(synchronize_session=False)

        # Simpan data baru untuk 6 hari aktif
        day_index = 0
        for i in range(7): # Loop 7 hari
            current_date = start_date + timedelta(days=i)
            if current_date.weekday() == 4: # Lewati hari Jumat
                continue
            
            # Ambil data dari form untuk hari ini
            day_form = form.days[day_index]
            
            # Hanya simpan jika ada sesi yang tidak hadir
            if day_form.sakit_izin.data > 0 or day_form.alpa.data > 0:
                absensi_harian = RekapAbsensi(
                    santri_id=santri_id,
                    tanggal=current_date,
                    jumlah_hadir=day_form.hadir.data,
                    jumlah_sakit_izin=day_form.sakit_izin.data,
                    jumlah_alpa=day_form.alpa.data,
                    keterangan_mingguan=keterangan_mingguan
                )
                db.session.add(absensi_harian)
            
            day_index += 1

        db.session.commit()
        flash('Rekap absensi mingguan berhasil disimpan!', 'success')
        return redirect(url_for('admin.input_rekap_absensi'))

    # Siapkan label untuk hari
    nama_hari = ["Sabtu", "Minggu", "Senin", "Selasa", "Rabu", "Kamis"]
    
    return render_template(
        'input_absensi_harian.html', 
        title="Input Rekap Absensi Harian", 
        form=form,
        nama_hari=nama_hari
    )

@admin_bp.route('/riwayat/absensi')
@login_required
def riwayat_absensi():
    # 1. LOGIKA FILTER (default 7 hari terakhir)
    today = date.today()
    start_default = today - timedelta(days=(today.weekday() + 2) % 7)
    end_default = start_default + timedelta(days=6)

    q_start_date_str = request.args.get('start_date', start_default.strftime('%Y-%m-%d'))
    q_end_date_str = request.args.get('end_date', end_default.strftime('%Y-%m-%d'))
    q_kelas = request.args.get('kelas', '')

    start_date = datetime.strptime(q_start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(q_end_date_str, '%Y-%m-%d').date()

    # 2. AMBIL DAFTAR SANTRI TERLEBIH DAHULU BERDASARKAN FILTER KELAS
    santri_query = Santri.query.order_by(Santri.nama_lengkap)
    if q_kelas:
        santri_query = santri_query.filter(Santri.kelas_saat_ini.ilike(f'%{q_kelas}%'))
    
    list_santri = santri_query.all()

    # 3. AMBIL SEMUA DATA ABSENSI PADA RENTANG TANGGAL TERPILIH
    records = RekapAbsensi.query.filter(
        RekapAbsensi.tanggal.between(start_date, end_date)
    ).all()
    
    # Kelompokkan record berdasarkan santri_id untuk pencarian cepat
    records_by_santri = defaultdict(list)
    for r in records:
        records_by_santri[r.santri_id].append(r)

    # 4. PROSES DATA UNTUK SETIAP SANTRI DI DAFTAR
    processed_data = {}
    for santri in list_santri:
        # Inisialisasi data untuk setiap santri
        santri_data = {
            'kelas': santri.kelas_saat_ini,
            'absensi': defaultdict(lambda: {'H': 4, 'I': 0, 'A': 0}) # Default hadir 4 sesi
        }
        
        # Atur default untuk hari Selasa menjadi 2 sesi
        for day_offset in range((end_date - start_date).days + 1):
            current_day = start_date + timedelta(days=day_offset)
            if current_day.weekday() == 1: # Selasa adalah weekday 1 di Python (jika Senin=0)
                 santri_data['absensi'][current_day] = {'H': 2, 'I': 0, 'A': 0}


        # Cek apakah santri ini punya catatan absensi
        if santri.id in records_by_santri:
            for record in records_by_santri[santri.id]:
                santri_data['absensi'][record.tanggal] = {
                    'H': record.jumlah_hadir,
                    'I': record.jumlah_sakit_izin,
                    'A': record.jumlah_alpa
                }
        
        processed_data[santri.nama_lengkap] = santri_data

    # 5. PERSIAPAN DATA UNTUK TEMPLATE
    date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    active_dates = [d for d in date_range if d.weekday() != 4] # Hapus Jumat

    return render_template(
        'riwayat_absensi.html',
        title="Laporan Detail Absensi",
        processed_data=processed_data,
        active_dates=active_dates,
        q_start_date_str=q_start_date_str,
        q_end_date_str=q_end_date_str,
        q_kelas=q_kelas
    )
@admin_bp.route('/riwayat/absensi/export')
@login_required
def export_riwayat_absensi():
    # 1. LOGIKA FILTER & PROSES DATA (COPY DARI RUTE riwayat_absensi)
    today = date.today()
    start_default = today - timedelta(days=(today.weekday() + 2) % 7)
    end_default = start_default + timedelta(days=6)

    q_start_date_str = request.args.get('start_date', start_default.strftime('%Y-%m-%d'))
    q_end_date_str = request.args.get('end_date', end_default.strftime('%Y-%m-%d'))
    q_kelas = request.args.get('kelas', '')

    start_date = datetime.strptime(q_start_date_str, '%Y-%m-%d').date()
    end_date = datetime.strptime(q_end_date_str, '%Y-%m-%d').date()

    query = RekapAbsensi.query.join(Santri).filter(RekapAbsensi.tanggal.between(start_date, end_date))
    if q_kelas:
        query = query.filter(Santri.kelas_saat_ini.ilike(f'%{q_kelas}%'))
    records = query.all()
    
    processed_data = defaultdict(lambda: {'kelas': '', 'absensi': defaultdict(lambda: {'H': 4, 'I': 0, 'A': 0})})
    for record in records:
        santri_name = record.santri.nama_lengkap
        processed_data[santri_name]['kelas'] = record.santri.kelas_saat_ini
        processed_data[santri_name]['absensi'][record.tanggal] = {'H': record.jumlah_hadir, 'I': record.jumlah_sakit_izin, 'A': record.jumlah_alpa}
    
    date_range = [start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1)]
    active_dates = [d for d in date_range if d.weekday() != 4]

    # 2. UBAH DATA PIVOT MENJADI FORMAT DATAFRAME
    data_for_excel = []
    for nama, data in processed_data.items():
        row_dict = {'NAMA': nama, 'KELAS': data['kelas']}
        for day in active_dates:
            row_dict[f"{day.strftime('%d/%m/%y')} - H"] = data['absensi'][day]['H']
            row_dict[f"{day.strftime('%d/%m/%y')} - I"] = data['absensi'][day]['I']
            row_dict[f"{day.strftime('%d/%m/%y')} - A"] = data['absensi'][day]['A']
        data_for_excel.append(row_dict)

    # 3. BUAT FILE EXCEL DI MEMORI
    df = pd.DataFrame(data_for_excel)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Laporan Absensi')
    output.seek(0)
    
    # 4. KIRIM FILE SEBAGAI UNDUHAN
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'laporan_absensi_{q_start_date_str}_sd_{q_end_date_str}.xlsx'
    )

@admin_bp.route('/riwayat/buku-sadar')
@login_required
def riwayat_buku_sadar():
    # 1. FILTER MINGGUAN
    today = date.today()
    start_default = today - timedelta(days=(today.weekday() + 2) % 7)
    q_start_date_str = request.args.get('start_date', start_default.strftime('%Y-%m-%d'))
    start_date = datetime.strptime(q_start_date_str, '%Y-%m-%d').date()
    end_date = start_date + timedelta(days=6)
    
    q_kelas = request.args.get('kelas', '')

    # 2. AMBIL DATA SANTRI
    santri_query = Santri.query.order_by(Santri.nama_lengkap)
    if q_kelas:
        santri_query = santri_query.filter(Santri.kelas_saat_ini.ilike(f'%{q_kelas}%'))
    list_santri = santri_query.all()

    # 3. AMBIL DATA ABSENSI & BUKU SADAR
    absensi_records = RekapAbsensi.query.filter(RekapAbsensi.tanggal.between(start_date, end_date)).all()
    sadar_records = RekapBukuSadar.query.filter_by(tanggal_awal_minggu=start_date).all()
    
    absensi_by_santri = defaultdict(lambda: defaultdict(int))
    for r in absensi_records:
        absensi_by_santri[r.santri_id][r.tanggal] = r.jumlah_alpa
        
    sadar_by_santri = {r.santri_id: r for r in sadar_records}

    # 4. PROSES DATA
    processed_data = {}
    for santri in list_santri:
        total_alpa = sum(absensi_by_santri[santri.id].values())
        sadar_info = sadar_by_santri.get(santri.id)
        
        santri_data = {
            'id': santri.id,
            'kelas': santri.kelas_saat_ini,
            'alpa_harian': absensi_by_santri[santri.id],
            'total_alpa': total_alpa,
            'keterangan': sadar_info.keterangan if sadar_info else '',
            'riyadhoh': sadar_info.riyadhoh if sadar_info else '',
            'status_lunas': sadar_info.status_lunas if sadar_info else 'Lunas'
        }
        processed_data[santri.nama_lengkap] = santri_data

    # 5. SIAPKAN DATA UNTUK TEMPLATE
    active_dates = [start_date + timedelta(days=i) for i in range(7) if (start_date + timedelta(days=i)).weekday() != 4]

    return render_template(
        'riwayat_buku_sadar.html',
        title=f"Riwayat Buku Sadar Mingguan",
        processed_data=processed_data,
        active_dates=active_dates,
        start_date_str=q_start_date_str,
        q_kelas=q_kelas
    )

@admin_bp.route('/riwayat/buku-sadar/export')
@login_required
def export_riwayat_buku_sadar():
    # 1. LOGIKA FILTER & PROSES DATA (COPY DARI RUTE SEBELUMNYA)
    today = date.today()
    q_month_str = request.args.get('month', today.strftime('%Y-%m'))
    selected_month = datetime.strptime(q_month_str, '%Y-%m').date()
    
    query = RekapBukuSadar.query.join(Santri).filter(
        extract('year', RekapBukuSadar.tanggal) == selected_month.year,
        extract('month', RekapBukuSadar.tanggal) == selected_month.month
    )

    q_santri_id = request.args.get('santri_id', type=int)
    q_kelas = request.args.get('kelas', '')

    if q_santri_id:
        query = query.filter(Santri.id == q_santri_id)
    if q_kelas:
        query = query.filter(Santri.kelas_saat_ini.ilike(f'%{q_kelas}%'))

    records = query.order_by(Santri.nama_lengkap, RekapBukuSadar.tanggal).all()
    
    processed_data = defaultdict(lambda: {
        'kelas': '', 
        'infractions': defaultdict(int), 
        'total': 0, 
        'keterangan_list': [], 
        'riyadhoh_list': [],
        'lunas_status': 'Lunas'
    })

    for record in records:
        santri_name = record.santri.nama_lengkap
        day = record.tanggal.day
        processed_data[santri_name]['kelas'] = record.santri.kelas_saat_ini
        processed_data[santri_name]['infractions'][day] += record.jumlah
        processed_data[santri_name]['total'] += record.jumlah
        processed_data[santri_name]['keterangan_list'].append(record.keterangan or 'ALFA')
        processed_data[santri_name]['riyadhoh_list'].append(record.riyadhoh or 'FISIK')
        if record.status_riyadhoh == 'Belum Lunas':
            processed_data[santri_name]['lunas_status'] = 'Belum Lunas'

    _, num_days = calendar.monthrange(selected_month.year, selected_month.month)
    days_in_month = list(range(1, num_days + 1))

    # 2. UBAH DATA PIVOT MENJADI FORMAT DATAFRAME
    data_for_excel = []
    for nama, data in processed_data.items():
        row_dict = {
            'NAMA': nama,
            'KELAS': data['kelas']
        }
        for day in days_in_month:
            row_dict[day] = data['infractions'].get(day, '')
        
        row_dict['TOTAL'] = data['total']
        row_dict['KETERANGAN'] = ', '.join(data['keterangan_list'])
        row_dict['RIYADHOH'] = ', '.join(data['riyadhoh_list'])
        row_dict['LUNAS'] = data['lunas_status']
        data_for_excel.append(row_dict)

    # 3. BUAT FILE EXCEL DI MEMORI
    df = pd.DataFrame(data_for_excel)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=selected_month.strftime('%B_%Y'))
    output.seek(0)

    # 4. KIRIM FILE SEBAGAI UNDUHAN
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'riwayat_buku_sadar_{q_month_str}.xlsx'
    )

@admin_bp.route('/riwayat/sks')
@login_required
def riwayat_sks_global():
    semua_santri = Santri.query.order_by(Santri.nama_lengkap).all()
    return render_template(
        'riwayat_sks_global.html',
        title="Ringkasan Riwayat SKS",
        santri_list=semua_santri
    )

@admin_bp.route('/riwayat/sks/<int:santri_id>')
@login_required
def riwayat_sks_per_santri(santri_id):
    # Ambil data santri yang spesifik
    santri = Santri.query.get_or_404(santri_id)
    
    # Ambil semua riwayat SKS untuk santri ini, urutkan berdasarkan tanggal
    sks_selesai = RekapSks.query.filter_by(santri_id=santri.id).order_by(RekapSks.tanggal.desc()).all()
    
    return render_template(
        'riwayat_sks_per_santri.html',
        title=f"Riwayat SKS - {santri.nama_lengkap}",
        santri=santri,
        sks_list=sks_selesai
    )

@admin_bp.route('/laporan/wali', methods=['GET'])
@login_required
def laporan_ke_wali():
    # Ambil santri_id dari pilihan dropdown di URL
    santri_id = request.args.get('santri_id', type=int)
    # Ambil catatan tes manual dari form
    tes_mapel_input = request.args.get('tes_mapel', '')

    semua_santri = Santri.query.order_by(Santri.nama_lengkap).all()
    
    laporan_data = None
    pesan_wa_encoded = None
    
    # Jika seorang santri telah dipilih dari dropdown
    if santri_id:
        santri = Santri.query.get_or_404(santri_id)
        
        # Tentukan rentang tanggal: 7 hari terakhir
        end_date = date.today()
        start_date = end_date - timedelta(days=6)

        # 1. Hitung jumlah hari aktif (bukan Jumat) dalam rentang waktu
        active_days = 0
        for i in range(7):
            if (start_date + timedelta(days=i)).weekday() != 4: # Jumat adalah weekday 4
                active_days += 1
        
        total_sesi_seminggu = active_days * 4

        # 2. Ambil total SAKIT/IZIN dan ALPA dari database
        rekap_absen = db.session.query(
            func.sum(RekapAbsensi.jumlah_sakit_izin).label('total_sakit_izin'),
            func.sum(RekapAbsensi.jumlah_alpa).label('total_alpa')
        ).filter(
            RekapAbsensi.santri_id == santri_id,
            RekapAbsensi.tanggal.between(start_date, end_date)
        ).one()
        
        total_sakit_izin = rekap_absen.total_sakit_izin or 0
        total_alpa = rekap_absen.total_alpa or 0

        # 3. Hitung jumlah HADIR secara manual
        total_hadir = total_sesi_seminggu - total_sakit_izin - total_alpa

        # 4. Ambil rekap SKS (ini tetap sama)
        sks_selesai = RekapSks.query.filter(
            RekapSks.santri_id == santri_id,
            RekapSks.tanggal.between(start_date, end_date)
        ).all()
        
        laporan_data = {
            'santri': santri,
            'hadir': total_hadir,
            'sakit_izin': total_sakit_izin,
            'alpa': total_alpa,
            'sks_list': [rekap.sks.nama_sks for rekap in sks_selesai]
        }
        
        # 5. Buat pesan WhatsApp (ini tetap sama)
        sks_text = '\n'.join([f"- {sks}" for sks in laporan_data['sks_list']]) or "Tidak ada"
        total_sesi_pesan = laporan_data['hadir'] + laporan_data['sakit_izin'] + laporan_data['alpa']
        pesan_template = (
            f"Akademik Takhossus Putri: Assalamualaikum Wr. Wb.\n\n"
            f"Kami dari pihak Akademik Madin Takhossus Amtsilati memberitahukan kepada bapak/ibu terkait perkembangan kegiatan belajar mengajar (KBM) ananda selama 1 minggu:\n\n"
            f"A.n : *{laporan_data['santri'].nama_lengkap}*\n"
            f"Fan : *{laporan_data['santri'].kelas_saat_ini}*\n\n"
            f"Telah menyelesaikan tes mata pelajaran:\n"
            f"{sks_text}\n\n"
            f"Dan berikut rekapan absensi dalam 1 minggu ({start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m/%Y')}), dari total {laporan_data['hadir'] + laporan_data['sakit_izin'] + laporan_data['alpa']} pertemuan:\n"
            f"hadir : {laporan_data['hadir']}\n"
            f"Sakit/Izin : {laporan_data['sakit_izin']}\n"
            f"Alpa : {laporan_data['alpa']}\n\n"
            f"Sekian pemberitahuan dari kami, kurang lebihnya mohon maaf dan terima kasih.\n\n"
            f"Wassalamualaikum Wr. Wb."
        )
        pesan_wa_encoded = urllib.parse.quote(pesan_template)

    return render_template(
        'laporan_wali.html',
        title="Buat Laporan untuk Wali Santri",
        semua_santri=semua_santri,
        selected_santri_id=santri_id,
        laporan_data=laporan_data,
        pesan_wa_encoded=pesan_wa_encoded,
        tes_mapel_input=tes_mapel_input
    )

@admin_bp.route('/koreksi/buku-sadar/<int:santri_id>/<start_date_str>', methods=['GET', 'POST'])
@login_required
def koreksi_buku_sadar(santri_id, start_date_str):
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = start_date + timedelta(days=6)
    santri = Santri.query.get_or_404(santri_id)
    form = KoreksiBukuSadarForm()

    if form.validate_on_submit():
        # 1. Update data di RekapAbsensi
        day_index = 0
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            if current_date.weekday() == 4: continue

            day_form = form.days[day_index]
            # Logika validasi total sesi per hari (4 atau 2)
            expected_total = 2 if current_date.weekday() == 1 else 4
            if (day_form.hadir.data + day_form.sakit_izin.data + day_form.alpa.data) != expected_total:
                flash(f"Total sesi untuk hari {current_date.strftime('%A')} harus {expected_total}!", "danger")
                return redirect(url_for('admin.koreksi_buku_sadar', santri_id=santri_id, start_date_str=start_date_str))

            # Update atau buat record absensi
            record_absensi = RekapAbsensi.query.filter_by(santri_id=santri_id, tanggal=current_date).first()
            if record_absensi:
                record_absensi.jumlah_hadir = day_form.hadir.data
                record_absensi.jumlah_sakit_izin = day_form.sakit_izin.data
                record_absensi.jumlah_alpa = day_form.alpa.data
            elif day_form.sakit_izin.data > 0 or day_form.alpa.data > 0:
                new_record = RekapAbsensi(
                    santri_id=santri_id, tanggal=current_date,
                    jumlah_hadir=day_form.hadir.data,
                    jumlah_sakit_izin=day_form.sakit_izin.data,
                    jumlah_alpa=day_form.alpa.data
                )
                db.session.add(new_record)
            day_index += 1

        # 2. Update atau buat data di RekapBukuSadar (ringkasan mingguan)
        record_sadar = RekapBukuSadar.query.filter_by(santri_id=santri_id, tanggal_awal_minggu=start_date).first()
        if record_sadar:
            record_sadar.keterangan = form.keterangan.data
            record_sadar.riyadhoh = form.riyadhoh.data
            record_sadar.status_lunas = form.status_lunas.data
        else:
            new_sadar = RekapBukuSadar(
                santri_id=santri_id, tanggal_awal_minggu=start_date,
                keterangan=form.keterangan.data,
                riyadhoh=form.riyadhoh.data,
                status_lunas=form.status_lunas.data
            )
            db.session.add(new_sadar)

        db.session.commit()
        flash('Data koreksi berhasil disimpan!', 'success')
        return redirect(url_for('admin.riwayat_buku_sadar'))

    # --- Method GET: Isi form dengan data yang ada ---
    # 1. Isi data mingguan (keterangan, riyadhoh, status)
    rekap_sadar = RekapBukuSadar.query.filter_by(santri_id=santri_id, tanggal_awal_minggu=start_date).first()
    if rekap_sadar:
        form.keterangan.data = rekap_sadar.keterangan
        form.riyadhoh.data = rekap_sadar.riyadhoh
        form.status_lunas.data = rekap_sadar.status_lunas

    # 2. Isi data absensi harian
    absensi_records = RekapAbsensi.query.filter(
        RekapAbsensi.santri_id == santri_id,
        RekapAbsensi.tanggal.between(start_date, end_date)
    ).all()
    absensi_dict = {rec.tanggal: rec for rec in absensi_records}

    day_index = 0
    for i in range(7):
        current_date = start_date + timedelta(days=i)
        if current_date.weekday() == 4: continue
        
        expected_total = 2 if current_date.weekday() == 1 else 4
        record = absensi_dict.get(current_date)
        if record:
            form.days[day_index].hadir.data = record.jumlah_hadir
            form.days[day_index].sakit_izin.data = record.jumlah_sakit_izin
            form.days[day_index].alpa.data = record.jumlah_alpa
        else: # Jika tidak ada record, berarti hadir penuh
            form.days[day_index].hadir.data = expected_total
            form.days[day_index].sakit_izin.data = 0
            form.days[day_index].alpa.data = 0
        day_index += 1

    nama_hari = ["Sabtu", "Minggu", "Senin", "Selasa", "Rabu", "Kamis"]
    return render_template(
        'koreksi_buku_sadar.html',
        title=f"Koreksi Absensi & Buku Sadar: {santri.nama_lengkap}",
        form=form,
        nama_hari=nama_hari,
        santri=santri,
        start_date_str=start_date_str
    )