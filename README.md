# Assignment Tracker

A student assignment tracking web app built with Flask.

## Features
- User authentication (email/password + OAuth ready)
- Track assignments with due dates, priority, and status
- Organize by courses
- Dark/light theme (mobile-responsive)

## Local Development

```bash
pip install -r requirements.txt
python app.py
```

## Deploy to Railway

1. **Push to GitHub:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   # Create repo on GitHub and push
   ```

2. **Deploy on Railway:**
   - Go to https://railway.app
   - Sign up with GitHub
   - Click "New Project" → "Deploy from GitHub repo"
   - Select this repo
   - Railway will auto-detect Python and install dependencies

3. **Environment Variables (optional):**
   - `SECRET_KEY` - Generate with: `python -c "import secrets; print(secrets.token_hex(32))"`
   - `GOOGLE_CLIENT_ID` - For Google OAuth (optional)
   - `GOOGLE_CLIENT_SECRET` - For Google OAuth (optional)

That's it! Railway will build and deploy your app with a public URL.

## Tech Stack
- Flask (backend)
- SQLite (local) / PostgreSQL (production)
- Flask-Login (auth)
- HTML/CSS/JS (frontend)