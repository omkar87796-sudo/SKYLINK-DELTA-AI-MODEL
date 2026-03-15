"""
Skylink Delta AI Support - Backend Server
Run: python backend/main.py
"""
import os, sys, json, uuid, asyncio, sqlite3
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ── Database ───────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "skylink.db")

def db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY, user_ip TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL, role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT, phone TEXT, message TEXT,
        created_at TEXT DEFAULT (datetime('now')))""")
    c.execute("""CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT, message_id INTEGER, rating INTEGER,
        created_at TEXT DEFAULT (datetime('now')))""")
    conn.commit()
    conn.close()
    print("✅ Database ready:", DB_PATH)

# ── Knowledge Base ─────────────────────────────────────────────
KNOWLEDGE = [
    {
        "keys": ["programming mode","enter program","#759","pm mode","how to program","password 119"],
        "answer": "**Entering Programming Mode:**\n\n1. From any extension, dial **#759**\n2. Dial the 3-digit password → default is **119**\n3. Dial tone changes to *Program Mode tone*\n4. Dial **#** anytime to return to Program Mode\n\n> **Security tip:** Change default password immediately using code `300-XXX`"
    },
    {
        "keys": ["extension number","define extension","assign extension","200-ppp","port number","numbering","extn"],
        "answer": "**Define Extension Numbers:**\n\n**Step 1 - Erase all ports first (mandatory):**\n-> In Programming Mode dial `299-22-22-23`\n\n**Step 2 - Assign extension:**\n-> `200-PPP-NN*`\n- PPP = Port number (001-128)\n- NN = Extension number you want\n\n**Other commands:**\n- Erase a specific port: `201-PPP`\n- Define self port: `210-NN*`\n- Delete extension: `211-Extn.No`\n\n> Default numbering starts from **200**"
    },
    {
        "keys": ["door release","open door","lobby","release door","756","door lock","door open"],
        "answer": "**Door Release:**\n\n**During conversation with Door Extension:**\n-> Dial Flash + Door Release Code\n\n**Direct release from flat:**\n-> Lift handset -> dial **756** (default code)\n\n**Multi-door release:**\n-> Lift handset -> dial **756** + Door Number (1-8)\n\n**Change door release code:**\n-> In Programming Mode: `727-NNN*` (default: **756**)\n\n**Enable/disable for extension:**\n- Enable: From Master dial `#717-Extn.No`\n- Disable: From Master dial `#707-Extn.No`"
    },
    {
        "keys": ["do not disturb","dnd","#47","not disturb","busy signal"],
        "answer": "**Do Not Disturb (DND):**\n\n**Activate:**\n1. Lift handset -> hear dial tone\n2. Dial **#47** -> hang up\n3. Dial tone of instrument changes to confirm\n\n**Deactivate:**\n-> Same steps: Lift handset -> dial **#47** -> hang up\n\n**System-wide control (Programming Mode):**\n- Activate all: `222-3-1`\n- Deactivate all: `222-3-0`"
    },
    {
        "keys": ["panic","emergency","alert","#777","panic code","emergency dial"],
        "answer": "**Panic & Emergency:**\n\n**Panic Alert (#0):**\n1. Lift handset -> hear dial tone\n2. Dial **#0** -> hang up\n-> Alarm sent to security, your extension flashes on display for 30 seconds with siren\n\n**Check last 10 panic alerts:**\n-> From display extension -> dial **#45**\n\n**Simultaneous Emergency Dialing (#777):**\n1. Lift handset\n2. Dial **#777**\n-> Rings 4 pre-programmed extensions simultaneously\n\n**Set emergency extensions:**\n-> Dial `#723` -> enter 4 extension numbers one by one"
    },
    {
        "keys": ["wake up","alarm","wakeup","#766","morning alarm","set alarm"],
        "answer": "**Wake-up Alarm:**\n\n1. Lift handset -> hear dial tone\n2. Dial **#766** -> wait for beep\n3. Dial **HH** (24hr hour) -> wait for beep\n4. Dial **MM** (minutes) -> wait for beep -> hang up\n\n**Example - 4:30 PM (16:30):**\n-> Dial `#766 -> 16 -> 30`\n\n> Uses 24-hour Railway Time format.\n> 8 beeps = programming error, repeat the steps."
    },
    {
        "keys": ["watchdog","watchman","watch dog","#736","#731","night watch","security watch"],
        "answer": "**Watchman Watchdog:**\n\nMonitors if watchman responds to alarm rings at night.\n\n**Step 1 - Define Watchdog Manager (from Master):**\n-> `#736` + Extension No.\n\n**Step 2 - Define Watchman Extensions (from WWD Manager):**\n-> `#731` + up to 4 extension numbers\n\n**Step 3 - Set Alarm Times:**\n-> `#733-X-HH1-MM1` (X = 1 to 6 for six alarm slots)\n\n**Activate daily:** `#732`\n**Activate one day:** `#730`\n**Deactivate:** `#734`\n**Check results:** `#735-WatchmanExtension` from display"
    },
    {
        "keys": ["call forward","follow me","redirect","forward call","#41","call divert","divert"],
        "answer": "**Call Forwarding / Follow Me:**\n\n**Activate:**\n1. Lift handset -> dial **#41**\n2. Dial the extension to forward calls to\n-> Dial tone changes to confirm\n\n**Cancel:**\n-> Lift handset -> dial **#41** -> hang up\n\n**System-level control (Programming Mode):**\n- Activate all: `222-1-1`\n- Deactivate all: `222-1-0`\n\n> Forwarded calls shown on security display."
    },
    {
        "keys": ["conference","all party","three party","multi call","conference call"],
        "answer": "**Conference Calls:**\n\n**All-Party Conference (unlimited, Hotel Mode OFF):**\n1. During conversation -> press **Flash**\n2. Dial next extension -> talk\n3. Repeat to add more parties\n\n**Three-Party (Hotel Mode must be ON):**\n-> Extn1 -> Flash -> Extn2 -> Flash+3 for conference\n\n**Split/Toggle calls:** `Flash + 1`\n**Drop existing call:** `Flash + 2`"
    },
    {
        "keys": ["hotel mode","call transfer","transfer call","call camp","hotel feature","222-5"],
        "answer": "**Hotel Mode:**\n\n**Enable (Programming Mode):** `222-5-1`\n**Disable:** `222-5-0`\n\n**Call Transfer:**\n-> While in call -> dial `Flash + Extension No.` -> wait for answer -> hang up\n\n**Call Camp (transfer to busy extension):**\n-> While in call -> dial `Flash + Extn No.` -> hear busy tone -> hang up\n-> Call rings when extension becomes free"
    },
    {
        "keys": ["president broadcast","broadcast","announcement","record message","general announcement"],
        "answer": "**President Broadcast:**\n(requires President Broadcast Card)\n\nDefault password: **119**\n\n| Action | Code |\n|--------|------|\n| Record (max 15 sec) | `#3 -> 119 -> 1` |\n| Playback | `#3 -> 119 -> 2` |\n| Activate without ring | `#3 -> 119 -> 3` |\n| Activate with ring | `#3 -> 119 -> 6` |\n| Deactivate | `#3 -> 119 -> 4` |\n| Change password | `#3 -> 119 -> 5 -> new password` |"
    },
    {
        "keys": ["vendor alarm","vendor","pavwala","bhajiwala","doodhwala","plumber","electrician","vendor code"],
        "answer": "**Vendor Alarm System:**\n(requires Vendor Alarm Card)\n\n| Vendor | Activate | Deactivate |\n|--------|----------|------------|\n| Pavwala | #21 | #11 |\n| Bhajiwala | #22 | #12 |\n| Doodhwala | #23 | #13 |\n| Plumber | #24 | #14 |\n| Electrician | #25 | #15 |\n\n**How it works:**\n1. Flat owner dials activation code to register request\n2. Vendor dials same code from security extension on arrival\n3. A voice prompt is sent to all who registered"
    },
    {
        "keys": ["factory reset","factory set","reset","default settings","reset system","299"],
        "answer": "**Factory Reset:**\n\n(All done in Programming Mode)\n\n| Action | Code |\n|--------|------|\n| Erase all port contents | `299-22-22-23` |\n| Reset extension numbering | `299-22-22-20` |\n| Reset COS and display to default | `299-22-22-21` |\n\n> Always erase ports BEFORE reconfiguring extension numbers."
    },
    {
        "keys": ["hotline","hot line","#722","#721","auto dial","preset number"],
        "answer": "**Hot Line Feature:**\n\nAuto-dials a preset extension after lifting handset.\n\n**Set delay:** `#721-X` (X = seconds, max 6)\n\n**Set hotline extension:**\n1. Lift handset -> dial `#722` -> beep\n2. Dial desired extension -> hang up\n\n**Cancel hotline:**\n-> Dial `#722` -> beep -> hang up"
    },
    {
        "keys": ["call pickup","pick up","pickup","answer ringing","code 6"],
        "answer": "**Call Pickup:**\n\n**General pickup (any ringing call in your group):**\n1. Lift receiver -> dial tone\n2. Dial **6** -> connected\n\n**Specific extension pickup:**\n1. Dial the ringing extension -> hear busy tone\n2. Dial **6** -> connected\n\n> Default code is **6** and cannot be changed."
    },
    {
        "keys": ["barge in","barge-in","#44","join call","intrude"],
        "answer": "**Barge-In Feature:**\n\n(Must be enabled from Master extension)\n\n**To barge in:**\n1. Dial desired extension -> hear busy tone\n2. Dial **#44** -> you are now in the call\n\n**Enable barge-in (from Master):**\n-> Dial `#710` + extension numbers\n\n**Disable barge-in (from Master):**\n-> Dial `#700` + extension number"
    },
    {
        "keys": ["caller id","clip","talking caller","tcid","#742","called number identification"],
        "answer": "**Caller ID Setup:**\n\n**From your own extension:**\n- Before ring: `#742-0`\n- Between ring: `#742-1`\n\n**From Master extension:**\n- Before ring: `#701-Extn.No`\n- Between ring: `#711-Extn.No`\n\n**Check call history (Talking Caller ID):**\n- Last caller: dial `#50`\n- Previous callers: `#51`, `#52` ... `#59`"
    },
    {
        "keys": ["clock","date time","set time","set date","#760","#761","real time"],
        "answer": "**Real Time Clock (from Master only):**\n\n**Set time:**\n1. Dial `#760` -> beep\n2. Dial HH (24hr) -> beep\n3. Dial MM -> beep\n\n**Set date:**\n1. Dial `#761` -> beep\n2. Dial DD -> beep\n3. Dial MM -> beep\n4. Dial YY\n\n**View current date:** Dial `#762`"
    },
    {
        "keys": ["model","delta 32","delta 64","delta 128","capacity","specification","dimension"],
        "answer": "**Skylink Delta Models:**\n\n| Model | Max Ports | Dimensions |\n|-------|-----------|------------|\n| Delta 32 | 32 | 30x23x7 cm |\n| Delta 64 | 64 | 30x36x7 cm |\n| Delta 128 | 128 | 30x36x14 cm |\n\nAll models have identical features. Only the CPU card differs.\n- CPU Card 64 up to 64 ports\n- CPU Card 128 up to 128 ports\n\n**Optional Cards:** Vendor Alarm, Talking Caller ID (TCID), President Broadcast"
    },
    {
        "keys": ["super cross check","cross check","#42","visitor","security verify"],
        "answer": "**Super Cross Check:**\n\nVerifies if visitor entered the correct flat.\n\n**Activate:**\n1. Security dials flat -> takes permission -> sends visitor\n2. After hanging up -> dial **#42**\n3. System rings back after pre-programmed interval\n\n**Set interval (from Master):**\n-> `#743 -> 2 -> XX` (XX = minutes)"
    },
    {
        "keys": ["auto call back","#48","callback","busy back"],
        "answer": "**Auto Call Back:**\n\n1. Call desired extension -> hear busy tone\n2. Dial **#48** -> hang up\n\nWhen the extension frees up, your phone rings. Lift receiver -> automatically connected."
    },
    {
        "keys": ["password","change password","pm password","programming password"],
        "answer": "**Change Programming Mode Password:**\n\nIn Programming Mode:\n-> Dial `300-XXX` (XXX = your new 3-digit password)\n\n> Default password is **119**. Change immediately after installation!"
    },
    {
        "keys": ["warranty","guarantee","1 year","repair","replace","defect"],
        "answer": "**Skylink Warranty:**\n\n- **Duration:** 1 year from date of purchase\n- Covers defects in materials and workmanship\n\n**Not covered:** Improper maintenance, unauthorized modification, natural calamities\n\nContact: +91 22 40107138 | info@skylinkcommunication.com"
    }
]

SYSTEM_PROMPT = """You are a friendly technical support assistant for Skylink Delta Intercom Systems.
Help customers understand programming and operation of their intercom.
Use the provided knowledge to answer accurately. Give clear numbered steps.
If you do not know, say so and suggest calling +91 22 40107138."""

def get_local_answer(question):
    q = question.lower()
    best_score = 0
    best_answer = None
    for entry in KNOWLEDGE:
        score = sum(1 for k in entry["keys"] if k in q)
        if score > best_score:
            best_score = score
            best_answer = entry["answer"]
    if best_answer and best_score > 0:
        return best_answer
    return "I can help you with your **Skylink Delta Intercom**. Try asking about:\n\n📞 **Communication:** call forwarding, conference, hotline, call pickup\n🔒 **Security:** panic alert, watchdog, barge-in, super cross check\n🚪 **Door Release:** open lobby door, change door code\n⚙️ **Programming:** enter programming mode, define extensions, factory reset\n🏨 **Hotel Features:** call transfer, call camp, hotel mode\n📢 **Optional Features:** vendor alarm, president broadcast, wake-up alarm"

async def get_claude_answer(question, history):
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return get_local_answer(question)
    try:
        import urllib.request
        q = question.lower()
        context_chunks = [e["answer"] for e in KNOWLEDGE if any(k in q for k in e["keys"])]
        context = "\n\n".join(context_chunks[:3]) or "No specific manual section found."
        messages = history[-10:] + [{"role": "user", "content": "Relevant manual info:\n" + context + "\n\nCustomer question: " + question}]
        payload = json.dumps({"model": "claude-sonnet-4-20250514", "max_tokens": 1024, "system": SYSTEM_PROMPT, "messages": messages}).encode()
        req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=payload,
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())["content"][0]["text"]
    except Exception as e:
        print("Claude API error:", e)
        return get_local_answer(question)

# ── Admin Panel HTML ───────────────────────────────────────────
def build_admin_html(contacts, messages, feedback, session_count):
    def contact_rows():
        if not contacts:
            return "<tr><td colspan='6' style='text-align:center;color:#8a95a8;padding:20px'>No contacts yet</td></tr>"
        rows = ""
        for r in contacts:
            rows += "<tr><td>" + str(r[0]) + "</td><td><b>" + str(r[1]) + "</b></td><td><a href='mailto:" + str(r[2]) + "' style='color:#00cfb4'>" + str(r[2]) + "</a></td><td>" + str(r[3]) + "</td><td>" + str(r[4]) + "</td><td style='color:#8a95a8'>" + str(r[5]) + "</td></tr>"
        return rows

    def message_rows():
        if not messages:
            return "<tr><td colspan='5' style='text-align:center;color:#8a95a8;padding:20px'>No messages yet</td></tr>"
        rows = ""
        for r in messages:
            role_color = "#1a6bff" if r[2] == "user" else "#1c2b4a"
            short_content = str(r[3])[:100] + "..." if len(str(r[3])) > 100 else str(r[3])
            rows += "<tr><td>" + str(r[0]) + "</td><td style='font-size:11px;color:#8a95a8'>" + str(r[1])[:12] + "...</td><td><span style='background:" + role_color + ";padding:2px 8px;border-radius:4px;font-size:11px'>" + str(r[2]) + "</span></td><td>" + short_content + "</td><td style='color:#8a95a8;font-size:11px'>" + str(r[4]) + "</td></tr>"
        return rows

    def feedback_rows():
        if not feedback:
            return "<tr><td colspan='4' style='text-align:center;color:#8a95a8;padding:20px'>No feedback yet</td></tr>"
        rows = ""
        for r in feedback:
            stars = "★" * int(r[3]) if r[3] else ""
            rows += "<tr><td>" + str(r[0]) + "</td><td style='font-size:11px;color:#8a95a8'>" + str(r[1])[:12] + "...</td><td style='color:#f59e0b'>" + stars + "</td><td style='color:#8a95a8;font-size:11px'>" + str(r[4]) + "</td></tr>"
        return rows

    return """<!DOCTYPE html>
<html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Skylink Admin</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:system-ui,sans-serif;background:#0b0f1a;color:#e0e6f0;padding:24px;}
h1{font-size:22px;margin-bottom:4px;color:white;}
.sub{color:#8a95a8;font-size:13px;margin-bottom:24px;}
.stats{display:flex;gap:14px;margin-bottom:24px;flex-wrap:wrap;}
.stat{background:#1c2b4a;border:1px solid #2a3d5a;border-radius:12px;padding:16px 24px;text-align:center;min-width:120px;}
.sn{font-size:28px;font-weight:700;color:#1a6bff;}
.sl{font-size:11px;color:#8a95a8;margin-top:4px;text-transform:uppercase;letter-spacing:1px;}
.section{background:#111827;border:1px solid #1c2b4a;border-radius:12px;padding:20px;margin-bottom:20px;overflow-x:auto;}
h2{font-size:15px;margin-bottom:14px;color:white;border-bottom:1px solid #1c2b4a;padding-bottom:10px;}
table{width:100%;border-collapse:collapse;font-size:12px;}
th{text-align:left;padding:8px 10px;color:#8a95a8;font-weight:500;border-bottom:1px solid #1c2b4a;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;}
td{padding:9px 10px;border-bottom:1px solid #1c2b4a;vertical-align:top;word-break:break-word;}
tr:last-child td{border-bottom:none;}
tr:hover td{background:rgba(28,43,74,0.4);}
</style></head><body>
<h1>Skylink Admin Panel</h1>
<div class='sub'>Live data from your deployed website &nbsp;|&nbsp; <a href='/admin?key=""" + os.environ.get("ADMIN_KEY","skylink2025") + """' style='color:#00cfb4'>Refresh</a></div>
<div class='stats'>
<div class='stat'><div class='sn'>""" + str(len(contacts)) + """</div><div class='sl'>Contact Leads</div></div>
<div class='stat'><div class='sn'>""" + str(session_count) + """</div><div class='sl'>Sessions</div></div>
<div class='stat'><div class='sn'>""" + str(len(messages)) + """</div><div class='sl'>Chat Messages</div></div>
<div class='stat'><div class='sn'>""" + str(len(feedback)) + """</div><div class='sl'>Feedback</div></div>
</div>
<div class='section'>
<h2>📩 Contact Form Submissions</h2>
<table><tr><th>ID</th><th>Name</th><th>Email</th><th>Phone</th><th>Message</th><th>Date</th></tr>""" + contact_rows() + """</table>
</div>
<div class='section'>
<h2>💬 Recent Chat Messages (last 50)</h2>
<table><tr><th>ID</th><th>Session</th><th>Role</th><th>Message</th><th>Date</th></tr>""" + message_rows() + """</table>
</div>
<div class='section'>
<h2>⭐ Feedback Ratings</h2>
<table><tr><th>ID</th><th>Session</th><th>Rating</th><th>Date</th></tr>""" + feedback_rows() + """</table>
</div>
</body></html>"""

# ── HTTP Handler ───────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def send_html_str(self, html, status=200):
        body = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, filepath):
        try:
            with open(filepath, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError:
            self.send_html_str("<h1>404 Not Found</h1>", 404)

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length)) if length else {}

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers()

    def do_GET(self):
        parsed  = urlparse(self.path)
        path    = parsed.path
        qs      = parse_qs(parsed.query)

        # ── Home page ─────────────────────────────────────────
        if path == "/" or path == "/index.html":
            html_file = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
            self.send_file(html_file)

        # ── Admin panel ───────────────────────────────────────
        elif path == "/admin":
            admin_key = os.environ.get("ADMIN_KEY", "skylink2025")
            provided  = qs.get("key", [""])[0]
            if provided != admin_key:
                self.send_html_str("""<!DOCTYPE html><html><head><meta charset='UTF-8'>
                <title>Admin Login</title>
                <style>body{font-family:system-ui;background:#0b0f1a;color:white;display:flex;
                align-items:center;justify-content:center;height:100vh;margin:0;}
                .box{background:#1c2b4a;padding:40px;border-radius:16px;text-align:center;}
                h2{margin-bottom:20px;}
                input{padding:10px 16px;border-radius:8px;border:1px solid #2a3d5a;
                background:#0b0f1a;color:white;font-size:14px;width:260px;margin-right:8px;}
                button{padding:10px 20px;background:#1a6bff;color:white;border:none;
                border-radius:8px;cursor:pointer;font-size:14px;}
                </style></head><body><div class='box'>
                <h2>🔒 Skylink Admin</h2>
                <form method='GET' action='/admin'>
                <input name='key' type='password' placeholder='Enter admin key'>
                <button type='submit'>Login</button>
                </form></div></body></html>""")
                return
            conn = db()
            contacts  = conn.execute("SELECT id,name,email,phone,message,created_at FROM contacts ORDER BY created_at DESC").fetchall()
            messages  = conn.execute("SELECT id,session_id,role,content,created_at FROM messages ORDER BY created_at DESC LIMIT 50").fetchall()
            feedback  = conn.execute("SELECT id,session_id,message_id,rating,created_at FROM feedback ORDER BY created_at DESC").fetchall()
            sess_count= conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            conn.close()
            self.send_html_str(build_admin_html(contacts, messages, feedback, sess_count))

        # ── Chat history ──────────────────────────────────────
        elif path.startswith("/api/history/"):
            session_id = path.split("/")[-1]
            conn = db()
            rows = conn.execute(
                "SELECT role,content,created_at FROM messages WHERE session_id=? ORDER BY created_at",
                (session_id,)
            ).fetchall()
            conn.close()
            self.send_json([{"role": r[0], "content": r[1], "time": r[2]} for r in rows])

        # ── Health check ──────────────────────────────────────
        elif path == "/api/health":
            self.send_json({"status": "ok", "mode": os.environ.get("AI_MODE", "local")})

        # ── Static files ──────────────────────────────────────
        else:
            static = os.path.join(os.path.dirname(__file__), "..", "frontend", path.lstrip("/"))
            if os.path.isfile(static):
                with open(static, "rb") as f:
                    body = f.read()
                ct = "text/css" if path.endswith(".css") else "application/javascript" if path.endswith(".js") else "text/plain"
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        body = self.read_body()

        # ── Chat ──────────────────────────────────────────────
        if path == "/api/chat":
            message    = body.get("message", "").strip()
            session_id = body.get("session_id") or str(uuid.uuid4())

            if not message:
                self.send_json({"error": "Empty message"}, 400)
                return

            conn = db()
            exists = conn.execute("SELECT id FROM sessions WHERE id=?", (session_id,)).fetchone()
            if not exists:
                conn.execute("INSERT INTO sessions VALUES (?,?,?)",
                             (session_id, self.client_address[0], datetime.now().isoformat()))

            rows = conn.execute(
                "SELECT role,content FROM messages WHERE session_id=? ORDER BY created_at DESC LIMIT 10",
                (session_id,)
            ).fetchall()
            history = [{"role": r[0], "content": r[1]} for r in reversed(rows)]

            ai_mode = os.environ.get("AI_MODE", "local")
            if ai_mode == "claude":
                loop = asyncio.new_event_loop()
                answer = loop.run_until_complete(get_claude_answer(message, history))
                loop.close()
            else:
                answer = get_local_answer(message)

            conn.execute("INSERT INTO messages (session_id,role,content) VALUES (?,?,?)",
                         (session_id, "user", message))
            conn.execute("INSERT INTO messages (session_id,role,content) VALUES (?,?,?)",
                         (session_id, "assistant", answer))
            conn.commit()
            msg_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            conn.close()

            self.send_json({
                "session_id": session_id,
                "message_id": msg_id,
                "response":   answer,
                "timestamp":  datetime.now().isoformat()
            })

        # ── Feedback ──────────────────────────────────────────
        elif path == "/api/feedback":
            conn = db()
            conn.execute("INSERT INTO feedback (session_id,message_id,rating) VALUES (?,?,?)",
                         (body.get("session_id"), body.get("message_id"), body.get("rating")))
            conn.commit()
            conn.close()
            self.send_json({"status": "ok"})

        # ── Contact ───────────────────────────────────────────
        elif path == "/api/contact":
            name    = body.get("name",    "").strip()
            email   = body.get("email",   "").strip()
            phone   = body.get("phone",   "").strip()
            message = body.get("message", "").strip()

            if not name or not email:
                self.send_json({"error": "Name and email required"}, 400)
                return

            conn = db()
            conn.execute("INSERT INTO contacts (name,email,phone,message) VALUES (?,?,?,?)",
                         (name, email, phone, message))
            conn.commit()
            conn.close()
            print("New contact:", name, "<" + email + ">")
            self.send_json({"status": "ok", "message": "Thank you! We will contact you within 24 hours."})

        else:
            self.send_json({"error": "Not found"}, 404)


# ── Start Server ───────────────────────────────────────────────
def run(port=8000):
    init_db()
    server = HTTPServer(("0.0.0.0", port), Handler)
    print("=" * 50)
    print("  Skylink Delta AI Support Server")
    print("  Open: http://localhost:" + str(port))
    print("  AI Mode:", os.environ.get("AI_MODE", "local"))
    print("  Admin:  http://localhost:" + str(port) + "/admin?key=" + os.environ.get("ADMIN_KEY", "skylink2025"))
    print("=" * 50)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped.")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8000))
    run(port)
