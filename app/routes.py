import io
import os
import calendar
import urllib.parse
from datetime import date, datetime, timedelta
from collections import defaultdict

# 2. Pustaka Pihak Ketiga (Flask, SQLAlchemy, Pandas, dll)
from flask import (Blueprint, render_template, redirect, url_for, 
                   flash, request, send_file)
from sqlalchemy import extract
import pandas as pd
import numpy as np

# 3. Impor dari Aplikasi Lokal Anda
from . import db
from .models import (Santri, SksMaster, RekapSks, RekapAbsensi, 
                     RekapBukuSadar)
from .forms import (RekapSksForm, SantriForm, UploadExcelForm, 
                    SksMasterForm, AbsensiForm, BukuSadarForm)


# 1. Buat Blueprint untuk admin
# Semua URL di file ini akan diawali dengan /admin
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
def admin_dashboard():
    # 1. Hitung jumlah santri aktif
    jumlah_santri = Santri.query.count()

    # 2. Hitung jumlah SKS yang terdaftar
    jumlah_sks = SksMaster.query.count()

    # 3. Hitung jumlah absensi yang diinput HARI INI
    absen_hari_ini = RekapAbsensi.query.filter_by(tanggal=date.today()).count()

    # 4. Hitung jumlah pelanggaran buku sadar HARI INI
    sadar_hari_ini = RekapBukuSadar.query.filter_by(tanggal=date.today()).count()

    # Kirim semua data statistik ke template
    return render_template(
        'admin_dashboard.html',
        title="Dashboard Admin",
        jumlah_santri=jumlah_santri,
        jumlah_sks=jumlah_sks,
        absen_hari_ini=absen_hari_ini,
        sadar_hari_ini=sadar_hari_ini
    )

# Tambahkan juga rute ini agar /admin langsung mengarah ke dashboard
@admin_bp.route('/')
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
def input_rekap_absensi():
    form = AbsensiForm()
    form.santri.choices = [(s.id, s.nama_lengkap) for s in Santri.query.order_by('nama_lengkap').all()]

    if form.validate_on_submit():
        absensi = RekapAbsensi(
            tanggal=form.tanggal.data,
            santri_id=form.santri.data,
            status=form.status.data,
            keterangan=form.keterangan.data
        )
        db.session.add(absensi)
        db.session.commit()
        flash('Data absensi berhasil disimpan!', 'success')
        return redirect(url_for('admin.input_rekap_absensi'))
    
    return render_template('input_absensi.html', title="Input Rekap Absensi", form=form)

@admin_bp.route('/rekap/buku-sadar', methods=['GET', 'POST'])
def input_buku_sadar():
    form = BukuSadarForm()
    form.santri.choices = [(s.id, s.nama_lengkap) for s in Santri.query.order_by('nama_lengkap').all()]

    if form.validate_on_submit():
        catatan = RekapBukuSadar(
            tanggal=form.tanggal.data,
            santri_id=form.santri.data,
            jumlah=form.jumlah.data,
            keterangan=form.keterangan.data,
            riyadhoh=form.riyadhoh.data,
            status_riyadhoh=form.status_riyadhoh.data # <-- TAMBAHKAN INI
        )
        db.session.add(catatan)
        db.session.commit()
        flash('Catatan Buku Sadar berhasil disimpan!', 'success')
        return redirect(url_for('admin.input_buku_sadar'))
    
    return render_template('input_buku_sadar.html', title="Input Rekap Buku Sadar", form=form)

@admin_bp.route('/riwayat/absensi')
def riwayat_absensi():
    # --- BAGIAN FILTER ---
    # Ambil nilai filter dari URL (request.args)
    q_santri_id = request.args.get('santri_id', type=int)
    q_start_date_str = request.args.get('start_date', '')
    q_end_date_str = request.args.get('end_date', '')
    q_status = request.args.get('status', '')

    # Query dasar untuk mengambil semua data absensi
    query = RekapAbsensi.query

    # Terapkan filter jika ada
    if q_santri_id:
        query = query.filter(RekapAbsensi.santri_id == q_santri_id)
    
    if q_start_date_str:
        start_date = datetime.strptime(q_start_date_str, '%Y-%m-%d').date()
        query = query.filter(RekapAbsensi.tanggal >= start_date)

    if q_end_date_str:
        end_date = datetime.strptime(q_end_date_str, '%Y-%m-%d').date()
        query = query.filter(RekapAbsensi.tanggal <= end_date)
    
    if q_status:
        query = query.filter(RekapAbsensi.status == q_status)

    # Eksekusi query dengan urutan tanggal terbaru di atas
    hasil_absensi = query.order_by(RekapAbsensi.tanggal.desc()).all()

    # Siapkan data untuk dropdown filter santri
    semua_santri = Santri.query.order_by(Santri.nama_lengkap).all()

    return render_template(
        'riwayat_absensi.html',
        title="Riwayat Absensi Santri",
        absensi_list=hasil_absensi,
        semua_santri=semua_santri,
        santri_id=q_santri_id,
        start_date_str=q_start_date_str,
        end_date_str=q_end_date_str,
        status=q_status,
    )
@admin_bp.route('/riwayat/absensi/export')
def export_riwayat_absensi():
    today_str = date.today().strftime('%Y-%m-%d')
    # 1. LOGIKA FILTER (SAMA PERSIS SEPERTI SEBELUMNYA)
    q_santri_id = request.args.get('santri_id', type=int)
    q_start_date_str = request.args.get('start_date', today_str) # <-- UBAH DI SINI
    q_end_date_str = request.args.get('end_date', today_str)   # <-- UBAH DI SINI
    q_status = request.args.get('status', '')

    query = RekapAbsensi.query

    if q_santri_id:
        query = query.filter(RekapAbsensi.santri_id == q_santri_id)
    if q_start_date_str:
        start_date = datetime.strptime(q_start_date_str, '%Y-%m-%d').date()
        query = query.filter(RekapAbsensi.tanggal >= start_date)
    if q_end_date_str:
        end_date = datetime.strptime(q_end_date_str, '%Y-%m-%d').date()
        query = query.filter(RekapAbsensi.tanggal <= end_date)
    if q_status:
        query = query.filter(RekapAbsensi.status == q_status)

    hasil_absensi = query.order_by(RekapAbsensi.tanggal.desc()).all()

    # 2. PERSIAPKAN DATA UNTUK EXCEL
    data_for_excel = []
    for absensi in hasil_absensi:
        data_for_excel.append({
            'Tanggal': absensi.tanggal.strftime('%Y-%m-%d'),
            'Nama Santri': absensi.santri.nama_lengkap,
            'Status': absensi.status.capitalize(),
            'Keterangan': absensi.keterangan
        })

    # 3. BUAT FILE EXCEL DI MEMORI
    df = pd.DataFrame(data_for_excel)
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Riwayat Absensi')

    output.seek(0)

    # 4. KIRIM FILE SEBAGAI UNDUHAN
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'riwayat_absensi_{date.today().strftime("%Y%m%d")}.xlsx'
    )

@admin_bp.route('/riwayat/buku-sadar')
def riwayat_buku_sadar():
    # --- BAGIAN FILTER ---
    # Default: bulan ini. Jika ada filter, gunakan filter tsb.
    today = date.today()
    q_month_str = request.args.get('month', today.strftime('%Y-%m'))
    
    selected_month = datetime.strptime(q_month_str, '%Y-%m').date()
    
    # Ambil semua data buku sadar untuk bulan yang dipilih
    # dan join dengan data santri untuk bisa memfilter kelas
    query = RekapBukuSadar.query.join(Santri).filter(
        extract('year', RekapBukuSadar.tanggal) == selected_month.year,
        extract('month', RekapBukuSadar.tanggal) == selected_month.month
    )

    # Terapkan filter tambahan jika ada
    q_santri_id = request.args.get('santri_id', type=int)
    q_kelas = request.args.get('kelas', '')

    if q_santri_id:
        query = query.filter(Santri.id == q_santri_id)
    if q_kelas:
        query = query.filter(Santri.kelas_saat_ini.ilike(f'%{q_kelas}%'))

    records = query.order_by(Santri.nama_lengkap, RekapBukuSadar.tanggal).all()
    
    # --- BAGIAN PENGOLAHAN DATA (PIVOT) ---
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

    # Menentukan jumlah hari dalam sebulan untuk header tabel
    _, num_days = calendar.monthrange(selected_month.year, selected_month.month)
    days_in_month = list(range(1, num_days + 1))
    
    # Siapkan data untuk dropdown filter
    semua_santri = Santri.query.order_by(Santri.nama_lengkap).all()
    
    return render_template(
        'riwayat_buku_sadar.html',
        title=f"Riwayat Buku Sadar - {selected_month.strftime('%B %Y')}",
        processed_data=processed_data,
        days_in_month=days_in_month,
        semua_santri=semua_santri,
        q_month_str=q_month_str,
        q_santri_id=q_santri_id,
        q_kelas=q_kelas
    )
@admin_bp.route('/riwayat/buku-sadar/export')
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

@admin_bp.route('/riwayat/buku-sadar/list')
def list_riwayat_buku_sadar():
    # --- BAGIAN FILTER ---
    q_santri_id = request.args.get('santri_id', type=int)
    q_start_date_str = request.args.get('start_date', '')
    q_end_date_str = request.args.get('end_date', '')
    q_status = request.args.get('status', '') # Filter untuk Lunas/Belum Lunas

    query = RekapBukuSadar.query

    if q_santri_id:
        query = query.filter(RekapBukuSadar.santri_id == q_santri_id)
    if q_start_date_str:
        start_date = datetime.strptime(q_start_date_str, '%Y-%m-%d').date()
        query = query.filter(RekapBukuSadar.tanggal >= start_date)
    if q_end_date_str:
        end_date = datetime.strptime(q_end_date_str, '%Y-%m-%d').date()
        query = query.filter(RekapBukuSadar.tanggal <= end_date)
    if q_status:
        query = query.filter(RekapBukuSadar.status_riyadhoh == q_status)

    hasil_catatan = query.order_by(RekapBukuSadar.tanggal.desc()).all()
    semua_santri = Santri.query.order_by(Santri.nama_lengkap).all()

    return render_template(
        'list_buku_sadar.html',
        title="Daftar Catatan Buku Sadar",
        catatan_list=hasil_catatan,
        semua_santri=semua_santri,
        santri_id=q_santri_id,
        start_date_str=q_start_date_str,
        end_date_str=q_end_date_str,
        status=q_status
    )

@admin_bp.route('/riwayat/buku-sadar/hapus/<int:id>', methods=['POST', 'GET'])
def hapus_buku_sadar(id):
    catatan = RekapBukuSadar.query.get_or_404(id)
    try:
        db.session.delete(catatan)
        db.session.commit()
        flash('Catatan berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error saat menghapus: {e}', 'danger')
    return redirect(url_for('admin.list_riwayat_buku_sadar'))

# RUTE UNTUK EDIT CATATAN BUKU SADAR
@admin_bp.route('/riwayat/buku-sadar/edit/<int:id>', methods=['GET', 'POST'])
def edit_buku_sadar(id):
    catatan = RekapBukuSadar.query.get_or_404(id)
    form = BukuSadarForm(obj=catatan)
    form.santri.choices = [(s.id, s.nama_lengkap) for s in Santri.query.order_by('nama_lengkap').all()]

    if form.validate_on_submit():
        catatan.tanggal = form.tanggal.data
        catatan.santri_id = form.santri.data
        catatan.jumlah = form.jumlah.data
        catatan.keterangan = form.keterangan.data
        catatan.riyadhoh = form.riyadhoh.data
        catatan.status_riyadhoh = form.status_riyadhoh.data
        db.session.commit()
        flash('Catatan berhasil diperbarui!', 'success')
        return redirect(url_for('admin.list_riwayat_buku_sadar'))

    # Saat method GET, isi dropdown santri dengan nilai yang sudah ada
    form.santri.data = catatan.santri_id
    return render_template('edit_buku_sadar.html', title="Edit Catatan Buku Sadar", form=form)

@admin_bp.route('/riwayat/sks')
def riwayat_sks_global():
    semua_santri = Santri.query.order_by(Santri.nama_lengkap).all()
    return render_template(
        'riwayat_sks_global.html',
        title="Ringkasan Riwayat SKS",
        santri_list=semua_santri
    )

@admin_bp.route('/riwayat/sks/<int:santri_id>')
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

        # 1. Ambil & hitung rekap absensi
        absensi = RekapAbsensi.query.filter(
            RekapAbsensi.santri_id == santri_id,
            RekapAbsensi.tanggal.between(start_date, end_date)
        ).all()
        
        rekap_absen = defaultdict(int)
        for absen in absensi:
            rekap_absen[absen.status] += 1

        # 2. Ambil rekap SKS
        sks_selesai = RekapSks.query.filter(
            RekapSks.santri_id == santri_id,
            RekapSks.tanggal.between(start_date, end_date)
        ).all()
        
        laporan_data = {
            'santri': santri,
            'hadir': rekap_absen.get('hadir', 0),
            'sakit': rekap_absen.get('sakit', 0),
            'izin': rekap_absen.get('izin', 0),
            'alpa': rekap_absen.get('alpa', 0),
            'sks_list': [rekap.sks.nama_sks for rekap in sks_selesai]
        }
        
        # 3. Buat pesan WhatsApp
        sks_text = '\n'.join([f"- {sks}" for sks in laporan_data['sks_list']]) or "Tidak ada"
        
        pesan_template = (
            f"Akademik Takhossus Putri: Assalamualaikum Wr. Wb.\n\n"
            f"Kami dari pihak Akademik Madin Takhossus Amtsilati memberitahukan kepada bapak/ibu terkait perkembangan kegiatan belajar mengajar (KBM) ananda selama 1 minggu:\n\n"
            f"A.n : *{laporan_data['santri'].nama_lengkap}*\n"
            f"Fan : *{laporan_data['santri'].kelas_saat_ini}*\n\n"
            f"Telah menyelesaikan tes mata pelajaran:\n"
            f"{sks_text}\n\n"
            f"Dan berikut rekapan absensi dalam 1 minggu ({start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m/%Y')}):\n"
            f"Hadir : {laporan_data['hadir']}\n"
            f"Alfa : {laporan_data['alpa']}\n"
            f"Sakit : {laporan_data['sakit']}\n"
            f"Izin : {laporan_data['izin']}\n\n"
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