# run.py (Kode Baru)
import os
from flask import redirect, url_for
from app import create_app, db
from app.models import Santri, SksMaster, RekapSks, RekapAbsensi, RekapBukuSadar, User

app = create_app(os.getenv('FLASK_ENV') or 'default')

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, Santri=Santri, SksMaster=SksMaster, RekapSks=RekapSks, RekapAbsensi=RekapAbsensi, RekapBukuSadar=RekapBukuSadar, User=User)

@app.route('/')
def index():
    # Langsung alihkan ke dashboard admin
    return redirect(url_for('admin.admin_dashboard'))