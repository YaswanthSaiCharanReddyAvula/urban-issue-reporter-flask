import os
import threading
import time
from app import create_app
from models import init_db, get_db_connection

# Production WSGI entrypoint for Render / Gunicorn
start_time = time.time()
app = create_app('production')

# Ensure required directories (Render disk typically mounted at /data)
upload_dir = os.environ.get('UPLOAD_FOLDER', 'uploads')
models_dir = os.environ.get('MODELS_FOLDER', 'models')
os.makedirs(upload_dir, exist_ok=True)
os.makedirs(models_dir, exist_ok=True)

# Initialize database (idempotent)
try:
	init_db()
	print("✅ Database ready (wsgi)")
except Exception as e:
	print(f"❌ Database init error (wsgi): {e}")

# Background ML warm-up (non-blocking)
def _warm_models():
	try:
		from ml_models import initialize_ml_models
		print("🤖 (wsgi bg) Initializing ML models...")
		initialize_ml_models()
		print("✅ (wsgi bg) ML models ready")
	except Exception as e:
		print(f"⚠️  (wsgi bg) ML warm-up failed: {e}")

threading.Thread(target=_warm_models, daemon=True).start()

@app.route('/healthz')
def healthz():
	"""Lightweight health check for Render / monitoring"""
	try:
		conn = get_db_connection()
		conn.execute('SELECT 1')
		conn.close()
		return {"status": "ok", "uptime_sec": round(time.time() - start_time, 2)}, 200
	except Exception as e:
		return {"status": "error", "error": str(e)}, 500

print(f"🚀 WSGI app initialized in {time.time() - start_time:.2f}s")
