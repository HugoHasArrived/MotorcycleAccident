
from flask import Flask, jsonify, render_template_string
from threading import Lock
import time

app = Flask(__name__)
lock = Lock()

state = {
    "status": "SAFE",
    "tilt": "NORMAL",
    "impact": "NONE",
    "countdown_start": None,
    "alert": False,
    "last_event": "System initialized",
    "gps": None,
    "contacts": []
}

PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BikeGuard | Safety Dashboard</title>
<style>
:root {
  color-scheme: dark;
  --bg: #090f19;
  --panel: #111c2b;
  --line: #26374c;
  --text: #eef5ff;
  --muted: #91a4bb;
  --green: #34d399;
  --red: #fb7185;
  --blue: #60a5fa;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: Inter, system-ui, Arial, sans-serif;
  background: radial-gradient(ellipse at top, #172c43, var(--bg) 58%);
  color: var(--text);
  min-height: 100vh;
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px max(5%, calc((100% - 1180px)/2));
  border-bottom: 1px solid var(--line);
  background: #09111de8;
}
.brand { font-size: 25px; font-weight: 900; letter-spacing: 2px; }
.brand span { color: var(--green); }
.tagline { color: var(--muted); font-size: 12px; margin-top: 5px; }
.pill {
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 8px 12px;
  font-size: 12px;
  color: var(--green);
  white-space: nowrap;
}
main { max-width: 1180px; width: 92%; margin: 28px auto; }
.welcome { margin-bottom: 22px; }
h1 { font-size: clamp(26px, 4vw, 38px); margin: 0 0 8px; }
p { color: var(--muted); line-height: 1.6; }
.grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.panel {
  background: linear-gradient(145deg, #142236, #0f1927);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 22px;
  min-width: 0;
}
.hero { grid-column: span 2; text-align: center; padding: 30px 20px; }
.label { color: var(--muted); font-size: 13px; margin-bottom: 13px; }
.big-status { font-size: clamp(26px, 4vw, 40px); font-weight: 900; }
.indicator {
  height: 82px; width: 82px; border-radius: 50%;
  margin: 0 auto 18px; background: #064e3b;
  border: 8px solid #34d399;
  box-shadow: 0 0 32px #34d39944;
}
.indicator.danger {
  background: #7f1d1d; border-color: var(--red);
  box-shadow: 0 0 35px #fb718555;
}
.sub { color: var(--muted); font-size: 14px; margin-top: 10px; }
.countdown { font-size: 56px; font-weight: 900; color: var(--red); margin: 8px; }
.actions { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin-top: 22px; }
button {
  border: 0; border-radius: 10px; padding: 13px 17px;
  font-weight: 800; cursor: pointer; font-size: 14px;
}
button:disabled { opacity: .5; cursor: not-allowed; }
.primary { background: var(--green); color: #05251b; }
.danger-btn { background: var(--red); color: #310813; }
.secondary { background: #26374c; color: var(--text); }
.value { font-size: 23px; font-weight: 800; overflow-wrap: anywhere; }
.ok { color: var(--green); }
.warn { color: #fbbf24; }
.bad { color: var(--red); }
.small { font-size: 12px; color: var(--muted); margin-top: 8px; }
.wide { grid-column: span 3; }
.row { display: flex; justify-content: space-between; gap: 12px; align-items: center; }
input {
  width: 100%; background: #091321; color: var(--text);
  border: 1px solid var(--line); border-radius: 9px;
  padding: 12px; margin: 6px 0 12px;
}
footer { text-align: center; color: var(--muted); padding: 28px 15px; font-size: 12px; }
@media(max-width:760px) {
  header { align-items: flex-start; }
  .grid { grid-template-columns: 1fr; }
  .hero, .wide { grid-column: span 1; }
  .pill { font-size: 10px; }
}
</style>
</head>
<body>
<header>
  <div>
    <div class="brand">BIKE<span>GUARD</span></div>
    <div class="tagline">SMART RIDER SAFETY SYSTEM</div>
  </div>
  <div class="pill" id="connection">● DEMO MODE</div>
</header>

<main>
  <div class="welcome">
    <h1>Safety Dashboard</h1>
    <p>Monitor your prototype, test the accident countdown, and manage emergency contacts.</p>
  </div>

  <div class="grid">
    <section class="panel hero">
      <div class="indicator" id="indicator"></div>
      <div class="label">CURRENT SYSTEM STATUS</div>
      <div class="big-status" id="status">SYSTEM SAFE</div>
      <div class="sub" id="message">No simulated accident detected.</div>
      <div class="countdown" id="countdown"></div>
      <div class="actions">
        <button class="danger-btn" id="test" onclick="testAccident()">TEST ACCIDENT</button>
        <button class="primary" id="cancel" onclick="cancelAccident()" hidden>CANCEL ALERT</button>
        <button class="secondary" id="reset" onclick="resetSystem()" hidden>RESET SYSTEM</button>
      </div>
      <div class="small">Website demonstration only — not a real emergency service.</div>
    </section>

    <section class="panel">
      <div class="label">TILT SENSOR</div>
      <div class="value ok" id="tilt">NORMAL</div>
      <div class="small">Live hardware connection not configured</div>
    </section>

    <section class="panel">
      <div class="label">IMPACT DETECTION</div>
      <div class="value ok" id="impact">NONE</div>
      <div class="small">Impact sensor not configured</div>
    </section>

    <section class="panel">
      <div class="label">GPS LOCATION</div>
      <div class="value warn">NOT CONNECTED</div>
      <div class="small">No GPS coordinates received</div>
    </section>

    <section class="panel">
      <div class="label">GSM / SMS</div>
      <div class="value warn">NOT CONNECTED</div>
      <div class="small">No SMS messages can be sent yet</div>
    </section>

    <section class="panel">
      <div class="label">ARDUINO CONNECTION</div>
      <div class="value warn">NOT CONNECTED</div>
      <div class="small">Render cannot directly access your USB-connected UNO.</div>
    </section>

    <section class="panel wide">
      <div class="row">
        <div>
          <div class="label">EMERGENCY CONTACTS</div>
          <div class="value" style="font-size:18px">Your safety circle</div>
        </div>
      </div>
      <p>Enter a contact name for this browser demo. Contact details are not saved to an account.</p>
      <form onsubmit="addContact(event)">
        <label for="contactName">Contact name</label>
        <input id="contactName" maxlength="60" placeholder="e.g. Mom" required>
        <label for="contactPhone">Phone number (optional demo field)</label>
        <input id="contactPhone" maxlength="25" placeholder="e.g. 09XX XXX XXXX">
        <button class="secondary" type="submit">ADD CONTACT</button>
      </form>
      <div id="contacts" class="small">No contacts added.</div>
    </section>

    <section class="panel wide">
      <div class="label">LATEST EVENT</div>
      <div id="event">System initialized</div>
      <div class="small" id="eventTime"></div>
    </section>
  </div>
</main>

<footer>BIKEGUARD • SCHOOL ROBOTICS & ENGINEERING PROTOTYPE</footer>

<script>
let timer = null;
let remaining = 10;
let contacts = [];

const $ = id => document.getElementById(id);

async function api(path) {
  const response = await fetch(path, {method: "POST"});
  if (!response.ok) throw new Error("Server request failed");
  return response.json();
}

function showEvent(text) {
  $("event").textContent = text;
  $("eventTime").textContent = new Date().toLocaleString();
}

function testAccident() {
  if (timer !== null) return;

  remaining = 10;
  $("indicator").classList.add("danger");
  $("status").textContent = "POSSIBLE ACCIDENT";
  $("message").textContent = "Demo countdown active. Press cancel if safe.";
  $("tilt").textContent = "ABNORMAL";
  $("tilt").className = "value bad";
  $("impact").textContent = "DEMO DETECTED";
  $("impact").className = "value bad";
  $("test").disabled = true;
  $("cancel").hidden = false;
  $("reset").hidden = true;
  $("countdown").textContent = remaining;
  showEvent("Simulated accident detected");

  timer = setInterval(() => {
    remaining--;
    $("countdown").textContent = remaining;

    if (remaining <= 0) {
      clearInterval(timer);
      timer = null;
      $("status").textContent = "ALERT TRIGGERED";
      $("message").textContent = "Demo alert activated. No SMS was sent.";
      $("countdown").textContent = "!";
      $("cancel").hidden = true;
      $("reset").hidden = false;
      showEvent("Demo emergency alert triggered");
    }
  }, 1000);
}

function cancelAccident() {
  if (timer === null) return;
  clearInterval(timer);
  timer = null;
  $("indicator").classList.remove("danger");
  $("status").textContent = "ALERT CANCELLED";
  $("message").textContent = "Demo cancelled by the user.";
  $("countdown").textContent = "";
  $("tilt").textContent = "NORMAL";
  $("tilt").className = "value ok";
  $("impact").textContent = "NONE";
  $("impact").className = "value ok";
  $("cancel").hidden = true;
  $("reset").hidden = false;
  showEvent("Demo alert cancelled");
}

function resetSystem() {
  if (timer !== null) clearInterval(timer);
  timer = null;
  $("indicator").classList.remove("danger");
  $("status").textContent = "SYSTEM SAFE";
  $("message").textContent = "No simulated accident detected.";
  $("countdown").textContent = "";
  $("tilt").textContent = "NORMAL";
  $("tilt").className = "value ok";
  $("impact").textContent = "NONE";
  $("impact").className = "value ok";
  $("test").disabled = false;
  $("cancel").hidden = true;
  $("reset").hidden = true;
  showEvent("System reset in demo");
}

function addContact(event) {
  event.preventDefault();
  const name = $("contactName").value.trim();
  const phone = $("contactPhone").value.trim();
  if (!name) return;

  contacts.push({name, phone});
  $("contacts").replaceChildren();

  contacts.forEach(contact => {
    const line = document.createElement("div");
    line.textContent = contact.phone
      ? contact.name + " — " + contact.phone
      : contact.name;
    $("contacts").appendChild(line);
  });

  $("contactName").value = "";
  $("contactPhone").value = "";
}

$("connection").textContent = "● WEBSITE ONLINE";
</script>
</body>
</html>
"""

@app.get("/")
def home():
    return render_template_string(PAGE)

@app.get("/api/status")
def get_status():
    with lock:
        data = dict(state)
        start = data["countdown_start"]
        if start is not None:
            data["countdown"] = max(0, 10 - int(time.time() - start))
        else:
            data["countdown"] = 0
        data["countdown_start"] = None
    return jsonify(data)

@app.post("/api/test")
def test():
    with lock:
        state.update(
            status="ACCIDENT",
            tilt="ABNORMAL",
            impact="DETECTED",
            countdown_start=time.time(),
            alert=False,
            last_event="Test accident started"
        )
        return jsonify({"ok": True, "message": "Demo countdown started"})

@app.post("/api/cancel")
def cancel():
    with lock:
        state.update(
            status="CANCELLED",
            tilt="NORMAL",
            impact="NONE",
            countdown_start=None,
            alert=False,
            last_event="Demo alert cancelled"
        )
        return jsonify({"ok": True})

@app.post("/api/reset")
def reset():
    with lock:
        state.update(
            status="SAFE",
            tilt="NORMAL",
            impact="NONE",
            countdown_start=None,
            alert=False,
            last_event="System reset"
        )
        return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
