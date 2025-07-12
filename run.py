# run.py
import os
from app import create_app, db
from app.models import Santri, SksMaster, RekapSks # Import semua model

app = create_app(os.getenv('FLASK_ENV') or 'default')

@app.shell_context_processor
def make_shell_context():
    # Memudahkan akses saat menggunakan 'flask shell'
    return dict(db=db, Santri=Santri, SksMaster=SksMaster, RekapSks=RekapSks)

@app.route('/')
def index():
    return "<h1>Selamat Datang di Proyek Takhossus Putri!</h1><p>Fokus: Menu Rekap</p>"

# Rute untuk admin akan kita buat di file terpisah nanti (app/routes.py)