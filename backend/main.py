"""
Skylink Delta AI Support - Backend Server
Run: python main.py
Then open: http://localhost:8000
"""
import os, sys, json, uuid, asyncio, sqlite3, re
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# ─── Database Setup ────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "skylink.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        user_ip TEXT,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT, phone TEXT, message TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT, message_id INTEGER, rating INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    conn.commit()
    conn.close()
    print("✅ Database ready:", DB_PATH)

def db():
    return sqlite3.connect(DB_PATH)

# ─── AI Knowledge Base ─────────────────────────────────────────
KNOWLEDGE = [
    {
        "keys": ["programming mode","enter program","#759","pm mode","how to program","password 119"],
        "answer": "**Entering Programming Mode:**\n\n1. From any extension, dial **#759**\n2. Dial the 3-digit password → default is **119**\n3. Dial tone changes to *Program Mode tone*\n4. Dial **#** anytime to return to Program Mode\n\n> **Security tip:** Change default password immediately using code `300-XXX`"
    },
    {
        "keys": ["extension number","define extension","assign extension","200-ppp","port number","numbering","extn"],
        "answer": "**Define Extension Numbers:**\n\n**Step 1 – Erase all ports first (mandatory):**\n→ In Programming Mode dial `299-22-22-23`\n\n**Step 2 – Assign extension:**\n→ `200-PPP-NN*`\n- PPP = Port number (001–128)\n- NN = Extension number you want\n\n**Other commands:**\n- Erase a specific port: `201-PPP`\n- Define self port: `210-NN*`\n- Delete extension: `211-Extn.No`\n\n> Default numbering starts from **200**"
    },
    {
        "keys": ["door release","open door","lobby","release door","756","door lock","door open"],
        "answer": "**Door Release:**\n\n**During conversation with Door Extension:**\n→ Dial `Flash` + Door Release Code\n\n**Direct release from flat:**\n→ Lift handset → dial **756** (default code)\n\n**Multi-door release:**\n→ Lift handset → dial **756** + Door Number (1–8)\n\n**Change door release code:**\n→ In Programming Mode: `727-NNN*` (default: **756**)\n\n**Enable/disable for extension:**\n- Enable: From Master dial `#717-Extn.No`\n- Disable: From Master dial `#707-Extn.No`"
    },
    {
        "keys": ["do not disturb","dnd","#47","not disturb","busy signal"],
        "answer": "**Do Not Disturb (DND):**\n\n**Activate:**\n1. Lift handset → hear dial tone\n2. Dial **#47** → hang up\n3. Dial tone of instrument changes to confirm\n\n**Deactivate:**\n→ Same steps: Lift handset → dial **#47** → hang up\n\n**System-wide control (Programming Mode):**\n- Activate all: `222-3-1`\n- Deactivate all: `222-3-0`"
    },
    {
        "keys": ["panic","emergency","alert","#0 ","dial #0","#777","panic code","emergency dial"],
        "answer": "**Panic & Emergency:**\n\n**Panic Alert (#0):**\n1. Lift handset → hear dial tone\n2. Dial **#0** → hang up\n→ Alarm sent to security, your extension flashes on display for 30 seconds with siren\n\n**Check last 10 panic alerts:**\n→ From display extension → dial **#45**\n\n**Simultaneous Emergency Dialing (#777):**\n1. Lift handset\n2. Dial **#777**\n→ Rings 4 pre-programmed extensions simultaneously\n\n**Set emergency extensions:**\n→ Dial `#723` → enter 4 extension numbers one by one"
    },
    {
        "keys": ["wake up","alarm","wakeup","#766","morning alarm","set alarm"],
        "answer": "**Wake-up Alarm:**\n\n1. Lift handset → hear dial tone\n2. Dial **#766** → wait for beep\n3. Dial **HH** (24hr hour) → wait for beep\n4. Dial **MM** (minutes) → wait for beep → hang up\n\n**Example – 4:30 PM (16:30):**\n→ Dial `#766 → 16 → 30`\n\n> Uses 24-hour Railway Time format.\n> 8 beeps = programming error, repeat the steps."
    },
    {
        "keys": ["watchdog","watchman","watch dog","#736","#731","night watch","security watch"],
        "answer": "**Watchman's Watchdog:**\n\nMonitors if watchman responds to alarm rings at night.\n\n**Step 1 – Define Watchdog Manager (from Master):**\n→ `#736` + Extension No.\n\n**Step 2 – Define Watchman Extensions (from WWD Manager):**\n→ `#731` + up to 4 extension numbers\n\n**Step 3 – Set Alarm Times:**\n→ `#733-X-HH1-MM1` (X = 1 to 6 for six alarm slots)\n\n**Activate daily:** `#732`\n**Activate one day:** `#730`\n**Deactivate:** `#734`\n**Check results:** `#735-WatchmanExtension` from display"
    },
    {
        "keys": ["call forward","follow me","redirect","forward call","#41","call divert","divert"],
        "answer": "**Call Forwarding / Follow Me:**\n\n**Activate:**\n1. Lift handset → dial **#41**\n2. Dial the extension to forward calls to\n→ Dial tone changes to confirm\n\n**Cancel:**\n→ Lift handset → dial **#41** → hang up\n\n**System-level control (Programming Mode):**\n- Activate all: `222-1-1`\n- Deactivate all: `222-1-0`\n\n> Forwarded calls shown on security display."
    },
    {
        "keys": ["conference","all party","three party","multi call","conference call"],
        "answer": "**Conference Calls:**\n\n**All-Party Conference (unlimited, Hotel Mode OFF):**\n1. During conversation → press **Flash**\n2. Dial next extension → talk\n3. Repeat to add more parties\n\n**Three-Party (Hotel Mode must be ON):**\n→ Extn1 → Flash → Extn2 → Flash+3 for conference\n\n**Split/Toggle calls:** `Flash + 1`\n**Drop existing call:** `Flash + 2`"
    },
    {
        "keys": ["hotel mode","call transfer","transfer call","call camp","hotel feature","222-5"],
        "answer": "**Hotel Mode:**\n\n**Enable (Programming Mode):** `222-5-1`\n**Disable:** `222-5-0`\n\n**Call Transfer:**\n→ While in call → dial `Flash + Extension No.` → wait for answer → hang up\n\n**Call Camp (transfer to busy extension):**\n→ While in call → dial `Flash + Extn No.` → hear busy tone → hang up\n→ Call rings when extension becomes free"
    },
    {
        "keys": ["president broadcast","broadcast","announcement","#3-","record message","general announcement"],
        "answer": "**President Broadcast:**\n*(requires President Broadcast Card)*\n\nDefault password: **119**\n\n| Action | Code |\n|--------|------|\n| Record (max 15 sec) | `#3 → 119 → 1` |\n| Playback | `#3 → 119 → 2` |\n| Activate without ring | `#3 → 119 → 3` |\n| Activate with ring | `#3 → 119 → 6` |\n| Deactivate | `#3 → 119 → 4` |\n| Change password | `#3 → 119 → 5 → new password` |"
    },
    {
        "keys": ["vendor alarm","vendor","pavwala","bhajiwala","doodhwala","plumber","electrician","vendor code"],
        "answer": "**Vendor Alarm System:**\n*(requires Vendor Alarm Card)*\n\n| Vendor | Activate | Deactivate |\n|--------|----------|------------|\n| Pavwala | #21 | #11 |\n| Bhajiwala | #22 | #12 |\n| Doodhwala | #23 | #13 |\n| Plumber | #24 | #14 |\n| Electrician | #25 | #15 |\n\n**How it works:**\n1. Flat owner dials activation code to register request\n2. Vendor dials same code from security extension on arrival\n3. A voice prompt is sent to all who registered"
    },
    {
        "keys": ["factory reset","factory set","reset","default settings","reset system","299"],
        "answer": "**Factory Reset:**\n\n*(All done in Programming Mode)*\n\n| Action | Code |\n|--------|------|\n| Erase all port contents | `299-22-22-23` |\n| Reset extension numbering (starts from 200) | `299-22-22-20` |\n| Reset COS & display to default | `299-22-22-21` |\n\n> ⚠️ Always erase ports BEFORE reconfiguring extension numbers."
    },
    {
        "keys": ["hotline","hot line","#722","#721","auto dial","preset number"],
        "answer": "**Hot Line Feature:**\n\nAuto-dials a preset extension after lifting handset.\n\n**Set delay:** `#721-X` (X = seconds, max 6)\n\n**Set hotline extension:**\n1. Lift handset → dial `#722` → beep\n2. Dial desired extension → hang up\n\n**Cancel hotline:**\n→ Dial `#722` → beep → hang up"
    },
    {
        "keys": ["call pickup","pick up","pickup","answer ringing","code 6","#6"],
        "answer": "**Call Pickup:**\n\n**General pickup (any ringing call in your group):**\n1. Lift receiver → dial tone\n2. Dial **6** → connected\n\n**Specific extension pickup:**\n1. Dial the ringing extension → hear busy tone\n2. Dial **6** → connected\n\n> Default code is **6** and cannot be changed."
    },
    {
        "keys": ["barge in","barge-in","#44","join call","intrude"],
        "answer": "**Barge-In Feature:**\n\n*(Must be enabled from Master extension)*\n\n**To barge in:**\n1. Dial desired extension → hear busy tone\n2. Dial **#44** → you're now in the call\n\n**Enable barge-in (from Master):**\n→ Dial `#710` + extension numbers\n\n**Disable barge-in (from Master):**\n→ Dial `#700` + extension number"
    },
    {
        "keys": ["caller id","clip","talking caller","tcid","#742","called number identification"],
        "answer": "**Caller ID Setup:**\n\n**From your own extension:**\n- Before ring: `#742-0`\n- Between ring: `#742-1`\n\n**From Master extension:**\n- Before ring: `#701-Extn.No`\n- Between ring: `#711-Extn.No`\n\n**Check call history (Talking Caller ID):**\n- Last caller: dial `#50`\n- Previous callers: `#51`, `#52` ... `#59`"
    },
    {
        "keys": ["clock","date time","set time","set date","#760","#761","real time"],
        "answer": "**Real Time Clock (from Master only):**\n\n**Set time:**\n1. Dial `#760` → beep\n2. Dial HH (24hr) → beep\n3. Dial MM → beep\n\n**Set date:**\n1. Dial `#761` → beep\n2. Dial DD → beep\n3. Dial MM → beep\n4. Dial YY\n\n**View current date:** Dial `#762`"
    },
    {
        "keys": ["model","delta 32","delta 64","delta 128","capacity","specification","dimension"],
        "answer": "**Skylink Delta Models:**\n\n| Model | Max Ports | Dimensions |\n|-------|-----------|------------|\n| Delta 32 | 32 | 30×23×7 cm |\n| Delta 64 | 64 | 30×36×7 cm |\n| Delta 128 | 128 | 30×36×14 cm |\n\nAll models have identical features. Only the CPU card differs.\n- CPU Card 64 → up to 64 ports\n- CPU Card 128 → up to 128 ports\n\n**Optional Cards:** Vendor Alarm, Talking Caller ID (TCID), President Broadcast"
    },
    {
        "keys": ["super cross check","cross check","#42","visitor","security verify"],
        "answer": "**Super Cross Check:**\n\nVerifies if visitor entered the correct flat.\n\n**Activate:**\n1. Security dials flat → takes permission → sends visitor\n2. After hanging up → dial **#42**\n3. System rings back after pre-programmed interval\n\n**Set interval (from Master):**\n→ `#743 → 2 → XX` (XX = minutes)\n→ Example for 2 min: `#743 → beep → 2 → beep → 02`"
    },
    {
        "keys": ["auto call back","#48","callback","busy back"],
        "answer": "**Auto Call Back:**\n\nRequest a callback when a busy extension becomes free.\n\n1. Call desired extension → hear busy tone\n2. Dial **#48** → hang up\n\nWhen the extension frees up, your phone rings. Lift receiver → automatically connected."
    },
    {
        "keys": ["password","change password","pm password","programming password","300-"],
        "answer": "**Change Programming Mode Password:**\n\nIn Programming Mode:\n→ Dial `300-XXX` (XXX = your new 3-digit password)\n\n> Default password is **119**.\n> Change immediately after installation!"
    },
    {
        "keys": ["display","display setting","assign display","202","display number"],
        "answer": "**Display Settings:**\n\nSystem handles up to **15 independent displays**.\n\n**Assign display to port:**\n→ `202-PPP-DD` (DD = display no. 01–15)\n→ DD = 00 removes the display assignment\n\n**Define display for Panic Indication:**\n→ `400-DD-PPP....`\n\n**Enable as General Panic Display:**\n- Enable: `401-DD....`\n- Disable: `402-DD....`"
    },
    {
        "keys": ["warranty","guarantee","1 year","repair","replace","defect"],
        "answer": "**Skylink Warranty:**\n\n- **Duration:** 1 year from date of purchase\n- Covers defects in materials and workmanship under normal use\n\n**Not covered:**\n- Improper maintenance\n- Unauthorized modification\n- Operation outside specifications\n- Natural calamities (flood, lightning, earthquake)\n\nFor warranty service, contact:\n📞 +91 22 40107138\n✉️ info@skylinkcommunication.com"
    }
]

SYSTEM_PROMPT = """You are a friendly technical support assistant for Skylink Delta Intercom Systems.
Help customers understand programming and operation of their intercom.
Use the provided knowledge to answer accurately. Give clear numbered steps.
If you don't know, say so and suggest calling +91 22 40107138."""

def get_local_answer(question: str) -> str:
    q = question.lower()
    
    # Score each knowledge entry
    best_score = 0
    best_answer = None
    
    for entry in KNOWLEDGE:
        score = sum(1 for k in entry["keys"] if k in q)
        if score > best_score:
            best_score = score
            best_answer = entry["answer"]
    
    if best_answer and best_score > 0:
        return best_answer
    
    return """I can help you with your **Skylink Delta Intercom**. Try asking about:

📞 **Communication:** call forwarding, conference, hotline, call pickup
🔒 **Security:** panic alert, watchdog, barge-in, super cross check  
🚪 **Door Release:** open lobby door, change door code
⚙️ **Programming:** enter programming mode, define extensions, factory reset
🏨 **Hotel Features:** call transfer, call camp, hotel mode
📢 **Optional Features:** vendor alarm, president broadcast, wake-up alarm
📋 **Quick codes:** do not disturb, caller ID, auto call back

**Examples:**
- *"How do I enter programming mode?"*
- *"How to release the lobby door?"*
- *"Set up panic alert"*"""

async def get_claude_answer(question: str, history: list) -> str:
    """Call real Claude API if ANTHROPIC_API_KEY is set"""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key or api_key == "your-key-here":
        return get_local_answer(question)
    
    try:
        import urllib.request
        
        # Build context from knowledge base
        q = question.lower()
        context_chunks = []
        for entry in KNOWLEDGE:
            if any(k in q for k in entry["keys"]):
                context_chunks.append(entry["answer"])
        context = "\n\n".join(context_chunks[:3]) if context_chunks else "No specific manual section found."
        
        messages = history[-10:] + [{
            "role": "user",
            "content": f"Relevant manual info:\n{context}\n\nCustomer question: {question}"
        }]
        
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1024,
            "system": SYSTEM_PROMPT,
            "messages": messages
        }).encode()
        
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["content"][0]["text"]
    except Exception as e:
        print(f"Claude API error: {e} - using local KB")
        return get_local_answer(question)

# ─── HTTP Request Handler ──────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        pass  # quiet logs
    
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
    
    def send_html(self, path):
        try:
            with open(path, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
    
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
        path = urlparse(self.path).path
        
        if path == "/" or path == "/index.html":
            html = os.path.join(os.path.dirname(__file__), "..", "frontend", "index.html")
            self.send_html(html)
        
        elif path.startswith("/api/history/"):
            session_id = path.split("/")[-1]
            conn = db()
            msgs = conn.execute(
                "SELECT role, content, created_at FROM messages WHERE session_id=? ORDER BY created_at",
                (session_id,)
            ).fetchall()
            conn.close()
            self.send_json([{"role": r[0], "content": r[1], "time": r[2]} for r in msgs])
        
        elif path == "/api/health":
            self.send_json({"status": "ok", "mode": os.environ.get("AI_MODE","local")})
        
        else:
            # Try to serve static file
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
        
        # ── POST /api/chat ──────────────────────────────────
        if path == "/api/chat":
            message    = body.get("message", "").strip()
            session_id = body.get("session_id") or str(uuid.uuid4())
            
            if not message:
                self.send_json({"error": "Empty message"}, 400)
                return
            
            conn = db()
            
            # Create session if new
            exists = conn.execute("SELECT id FROM sessions WHERE id=?", (session_id,)).fetchone()
            if not exists:
                conn.execute("INSERT INTO sessions VALUES (?,?,?)",
                             (session_id, self.client_address[0], datetime.now().isoformat()))
            
            # Load history
            rows = conn.execute(
                "SELECT role, content FROM messages WHERE session_id=? ORDER BY created_at DESC LIMIT 10",
                (session_id,)
            ).fetchall()
            history = [{"role": r[0], "content": r[1]} for r in reversed(rows)]
            
            # Get AI answer (sync wrapper)
            ai_mode = os.environ.get("AI_MODE", "local")
            if ai_mode == "claude":
                loop = asyncio.new_event_loop()
                answer = loop.run_until_complete(get_claude_answer(message, history))
                loop.close()
            else:
                answer = get_local_answer(message)
            
            # Save messages
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
                "response": answer,
                "timestamp": datetime.now().isoformat()
            })
        
        # ── POST /api/feedback ──────────────────────────────
        elif path == "/api/feedback":
            conn = db()
            conn.execute("INSERT INTO feedback (session_id,message_id,rating) VALUES (?,?,?)",
                         (body.get("session_id"), body.get("message_id"), body.get("rating")))
            conn.commit()
            conn.close()
            self.send_json({"status": "ok"})
        
        # ── POST /api/contact ───────────────────────────────
        elif path == "/api/contact":
            name    = body.get("name", "").strip()
            email   = body.get("email", "").strip()
            phone   = body.get("phone", "").strip()
            message = body.get("message", "").strip()
            
            if not name or not email:
                self.send_json({"error": "Name and email required"}, 400)
                return
            
            conn = db()
            conn.execute("INSERT INTO contacts (name,email,phone,message) VALUES (?,?,?,?)",
                         (name, email, phone, message))
            conn.commit()
            conn.close()
            print(f"📩 New contact: {name} <{email}> - {message[:50]}")
            self.send_json({"status": "ok", "message": "Thank you! We'll contact you within 24 hours."})
        
        else:
            self.send_json({"error": "Not found"}, 404)


# ─── Start Server ──────────────────────────────────────────────
def run(port=8000):
    init_db()
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"\n{'='*52}")
    print(f"  🚀 Skylink Delta AI Support Server")
    print(f"  🌐 Open: http://localhost:{port}")
    print(f"  🤖 AI Mode: {os.environ.get('AI_MODE','local')}")
    print(f"  📦 DB: {DB_PATH}")
    print(f"{'='*52}\n")
    print("  Press Ctrl+C to stop\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")


if __name__ == "__main__":
    # Render sets the PORT environment variable automatically
    port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8000))
    run(port)
