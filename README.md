# Urban Issue Reporter - Modular Flask Application

## 🏗️ Project Structure

```
urban-flask-app/
├── app.py                 # Main application entry point
├── app_original.py        # Backup of original monolithic code
├── config.py              # Configuration settings
├── models.py              # Database models and operations
├── utils.py               # Utility functions
├── requirements.txt       # Project dependencies
├── routes/                # Route modules
│   ├── __init__.py       # Route initialization
│   ├── main.py           # Main routes (home, issues, comments)
│   ├── auth.py           # Authentication routes
│   └── admin.py          # Admin routes
├── static/               # CSS, JS, images
├── templates/            # HTML templates
└── uploads/              # User uploaded files
```

## ✅ Successfully Refactored Features

### 🔧 Modular Architecture
- **Separation of Concerns**: Each module has a single responsibility
- **Configuration Management**: Environment-based configuration in `config.py`
- **Database Abstraction**: Clean model classes in `models.py`
- **Utility Functions**: Reusable functions in `utils.py`
- **Route Organization**: Routes grouped by functionality

### 📊 All Original Features Preserved
- ✅ User registration and authentication
- ✅ Issue reporting with image upload
- ✅ Issue filtering and searching  
- ✅ Comment system with admin responses
- ✅ Admin dashboard and status management
- ✅ Email notifications
- ✅ Statistics display (users count, issues count)
- ✅ Category system (Road, Transport, Sanitation, Infrastructure, Water, Electricity, Environment, Other)

## 🚀 Running the Application

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**:
   ```bash
   python app.py
   ```

3. **Access the Application**:
   - Open: http://localhost:5000
   - Admin Login: admin@example.com / admin123

## 🌐 Deploying to Render

This project includes a `render.yaml` blueprint and a `wsgi.py` entrypoint for production.

### 1. Python Version Pin
Render defaulted to Python 3.13 which caused a build failure compiling `scikit-learn==1.3.0` (Cython errors like `'int_t' is not a type identifier`). We have added `runtime.txt`:

```
python-3.11.9
```

`scikit-learn 1.3.0` officially supports Python up to 3.11. Keeping 3.11.x avoids the heavy source build issues seen on 3.13.

### 2. One-Time Setup
1. Push your code (including `runtime.txt`) to GitHub.
2. In Render, create a New Web Service → Use repo.
3. Render auto-detects `render.yaml` and provisions the service.

### 3. Build & Start Commands
Defined in `render.yaml`:
- Build: `pip install -r requirements.txt`
- Start: `gunicorn wsgi:app`

### 4. Persistent Data
The SQLite DB and uploads are stored on a mounted disk at `/data`:
- `DATABASE_PATH=/data/urban_issues.db`
- `UPLOAD_FOLDER=/data/uploads`

### 5. Health Check
After deploy visit:
- `/healthz` → returns JSON `{ "status": "ok", ... }` once DB is reachable and app started.

### 6. Troubleshooting Build Failures
| Symptom | Cause | Fix |
|--------|-------|-----|
| Cython compile errors in scikit-learn (`'int_t' is not a type identifier`) | Python 3.13 selected | Ensure `runtime.txt` present with `python-3.11.9` and redeploy |
| Slow startup | ML models warming | Background thread warms models; just wait or hit `/healthz` repeatedly |
| Missing SECRET_KEY warning | Env var regenerated | Ignore unless rotating sessions matters |

### 7. Redeploy Steps (After Changes)
1. Commit & push changes.
2. Render auto deploys (if `autoDeploy: true`).
3. Watch logs; confirm `Startup complete` line from `wsgi.py`.
4. Hit `/healthz`.

### 8. Optional Production Optimizations
- Split dev vs prod requirements (move heavy ML libs to separate file if not always needed).
- Pre-build wheel layer: host wheels or upgrade scikit-learn to a version supporting newer Python (≥1.4 for later versions; verify release notes first).
- Consider migrating to PostgreSQL for concurrency (SQLite has write locks under load).

## 🔐 Environment Variables Summary
| Variable | Purpose | Example |
|----------|---------|---------|
| SECRET_KEY | Session signing | auto-generated |
| MAIL_USERNAME / MAIL_PASSWORD | SMTP credentials | your-email / app password |
| DATABASE_PATH | SQLite file path | /data/urban_issues.db |
| UPLOAD_FOLDER | Uploaded images | /data/uploads |

## 🩺 Health Endpoint
`/healthz` performs a lightweight DB connection and returns uptime; ideal for external monitors.

## ♻️ Future Improvements (Roadmap)
- Decorator for profile completeness check.
- Structured JSON logging (e.g., loguru or stdlib JSON formatter).
- Metrics endpoint (Prometheus format) for request counts and model inference latency.
- Switch to async task queue (e.g., RQ or Celery) for heavy ML retraining.

## 🧪 Testing Status

✅ **Application successfully tested and verified**
- All routes functional
- Database operations working
- Email system operational
- Admin panel accessible
- Template rendering correct
- No runtime errors

## 📋 Notes

- The VS Code editor may show lint warnings for Jinja2 template syntax in HTML files (e.g., `{{ variable }}`, `{% if %}`, etc.). These are false positives and do not affect the application functionality.
- The application uses SQLite database stored in `urban_issues.db`
- Email notifications are configured for Gmail SMTP
- File uploads are stored in the `uploads/` directory

## 🎯 Benefits of Modular Structure

- **Maintainability**: Easy to locate and modify specific functionality
- **Scalability**: Simple to add new features without affecting existing code
- **Testing**: Individual modules can be unit tested
- **Deployment**: Production-ready structure with environment configuration