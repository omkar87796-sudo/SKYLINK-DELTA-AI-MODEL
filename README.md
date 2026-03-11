# 🏢 Skylink Delta AI Support Website

A complete full-stack AI-powered support website for Skylink Delta Intercom Systems.

## 📁 Project Structure

```
skylink/
├── start.py              ← Run this to launch everything
├── backend/
│   └── main.py           ← Python web server + AI engine + database
└── frontend/
    └── index.html        ← Complete website (all pages in one file)
```

## 🚀 How to Run

### Requirement: Python 3.8 or newer
Download from https://python.org if you don't have it.

### Step 1 — Run the website

**Windows:**
```
Double-click start.py
```
or
```
python start.py
```

**Mac / Linux:**
```
python3 start.py
```

### Step 2 — Open in browser
The browser opens automatically at: **http://localhost:8000**

That's it! The website is fully working.

---

## 🤖 AI Modes

### Mode 1: LOCAL (default — works with no API keys)
The AI uses a built-in knowledge base of all Skylink Delta manual content.
No internet, no API keys needed. Answers are based on your actual manual.

### Mode 2: CLAUDE API (optional — smarter answers)
Set your Anthropic API key to get Claude-powered answers:

**Windows (Command Prompt):**
```
set ANTHROPIC_API_KEY=sk-ant-your-key-here
set AI_MODE=claude
python start.py
```

**Mac/Linux:**
```
export ANTHROPIC_API_KEY=sk-ant-your-key-here
export AI_MODE=claude
python3 start.py
```

Get an API key at: https://console.anthropic.com

---

## 💾 Database

All chats and contact form submissions are automatically saved to:
```
backend/skylink.db
```
This is a SQLite database file. You can open it with:
- DB Browser for SQLite (free): https://sqlitebrowser.org
- Or any SQLite viewer

**Tables:**
- `sessions` — chat sessions
- `messages` — all chat messages
- `contacts` — contact form submissions
- `feedback` — thumbs up/down ratings

---

## 🌐 Features

- **AI Chat** — asks about any intercom feature, gets instant answer
- **Quick Reference** — all common codes from the manual
- **Contact Form** — saved to database automatically
- **Session Memory** — chat continues where you left off
- **Feedback** — thumbs up/down on each AI answer
- **Mobile Responsive** — works on phones and tablets

---

## 🔧 Deploy Online (optional)

To put this website online:

### Option A: Railway (easiest, ~$5/month)
1. Install Railway CLI: https://railway.app
2. Run: `railway login && railway init && railway up`

### Option B: Any VPS
```bash
# Copy files to server
scp -r skylink/ user@your-server.com:/home/user/

# On server:
python3 /home/user/skylink/start.py &
```

### Option C: Change port
```
python start.py 3000
```

---

## 📞 Support

Skylink Communication
+91 22 40107138
info@skylinkcommunication.com
skylinkcommunication.com
# SKYLINK-DELTA-AI-MODEL
