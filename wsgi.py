from app import create_app

# Production WSGI entrypoint for Render / Gunicorn
app = create_app('production')
