
from flask import Flask, jsonify, render_template_string, request
from threading import Lock
import os
import time
import hmac

app = Flask(__name__)
lock = Lock()

# Set DEVICE_TOKEN in Render's environment variables before
# using the bridge outside a school/demo environment.
DEVICE_TOKEN = os.environ.get(
    "DEVICE_TOKEN", "bikeguard-demo-token"
)

state = {
    "status": "SAFE",
    "tilt": "NORMAL",
    "impact": "NONE",
    "countdown_start": None,
    "countdown_value": 0,
    "alert": False,
    "last_event": "Waiting for Arduino connection",
    "last_event_time": time.time(),
    "device_last_seen": None,
    "last_serial": "",
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
  --yellow: #fbbf24;
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
  padding: 20px max(4%, calc((100% - 1180px)/2));
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
  color: var(--yellow);
}
main { max-width: 1180px; width: 92%; margin: 28px auto; }
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
  border: 8px solid var(--green);
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
.warn { color: var(--yellow); }
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
  header { align-items: flex-start; flex-wrap: wrap; }
  .grid { grid-template-columns: 1fr; }
  .hero, .wide { grid-column: span 1; }
}
</style>
</head>
<body>
<header>
  <div>
    <div class="brand">BIKE<span>GUARD</span></div>
    <div class="tagline">SMART RIDER SAFETY SYSTEM</div>
  </div>
  <div class="pill" id="connection">● CHECKING CONNECTION</div>
</header>

<main>
  <h1>Safety Dashboard</h1>
  <p>Monitor your BikeGuard prototype and its latest sensor events.</p>

  <div class="grid">
    <section class="panel hero">
      <div class="indicator" id="indicator"></div>
      <div class="label">CURRENT SYSTEM STATUS</div>
      <div class="big-status" id="status">WAITING FOR DEVICE</div>
      <div class="sub" id="message">Waiting for Arduino messages.</div>
      <div class="countdown" id="countdown"></div>
      <div class="actions">
        <button class="danger-btn" onclick="sendAction('/api/test')">
          TEST WEBSITE DEMO
        </button>
        <button class="primary" id="cancel" onclick="sendAction('/api/cancel')" hidden>
          CANCEL DEMO
        </button>
        <button class="secondary" id="reset" onclick="sendAction('/api/reset')">
          RESET WEBSITE
        </button>
      </div>
      <div class="small">
        Demo controls do not cancel the physical Arduino countdown.
        No SMS is sent by this website.
      </div>
    </section>

    <section class="panel">
      <div class="label">TILT SWITCH</div>
      <div class="value ok" id="tilt">NORMAL</div>
      <div class="small">Reported by the Arduino prototype</div>
    </section>

    <section class="panel">
      <div class="label">IMPACT STATUS</div>
      <div class="value ok" id="impact">NONE</div>
      <div class="small">The current tilt switch does not measure impact force.</div>
    </section>

    <section class="panel">
      <div class="label">GPS LOCATION</div>
      <div class="value warn">NOT CONNECTED</div>
      <div class="small">A GPS module is required for real coordinates.</div>
    </section>

    <section class="panel">
      <div class="label">GSM / SMS</div>
      <div class="value warn">NOT CONNECTED</div>
      <div class="small">A compatible GSM module is required to send SMS.</div>
    </section>

    <section class="panel">
      <div class="label">ARDUINO CONNECTION</div>
      <div class="value warn" id="device">NOT CONNECTED</div>
      <div class="small" id="deviceTime">Waiting for serial data</div>
    </section>

    <section class="panel wide">
      <div class="label">LATEST EVENT</div>
      <div id="event">Waiting for Arduino connection</div>
      <div class="small" id="eventTime"></div>
      <div class="small" id="serialLine"></div>
    </section>

    <section class="panel wide">
      <div class="label">EMERGENCY CONTACTS — BROWSER DEMO</div>
      <p>Contacts are kept only in this browser and are not sent to emergency services.</p>
      <form onsubmit="addContact(event)">
        <label for="contactName">Contact name</label>
        <input id="contactName" maxlength="60" placeholder="e.g. Mom" required>
        <label for="contactPhone">Phone number (optional)</label>
        <input id="contactPhone" maxlength="25" placeholder="e.g. 09XX XXX XXXX">
        <button class="secondary" type="submit">ADD CONTACT</button>
      </form>
      <div id="contacts" class="small">No contacts added.</div>
    </section>
  </div>
</main>

<footer>BIKEGUARD • SCHOOL ROBOTICS & ENGINEERING PROTOTYPE</footer>

<script>
const $ = id => document.getElementById(id);
let contacts = [];

async function sendAction(path) {
  try {
    const response = await fetch(path, {method: "POST"});
    if (!response.ok) throw new Error("Request failed");
    await refreshStatus();
  } catch (error) {
    $("message").textContent = "Could not contact the website server.";
  }
}

async function refreshStatus() {
  try {
    const response = await fetch("/api/status", {cache: "no-store"});
    if (!response.ok) throw new Error("Status request failed");
    const s = await response.json();

    const connected = s.device_connected;
    $("connection").textContent = connected
      ? "● ARDUINO CONNECTED" : "● ARDUINO DISCONNECTED";
    $("connection").style.color = connected ? "#34d399" : "#fbbf24";
    $("device").textContent = connected ? "CONNECTED" : "NOT CONNECTED";
    $("device").className = "value " + (connected ? "ok" : "warn");

    $("deviceTime").textContent = connected
      ? "Receiving recent serial messages"
      : "Keep the Python bridge running on the USB-connected computer";

    $("status").textContent = {
      SAFE: "SYSTEM SAFE",
      ACCIDENT: "POSSIBLE ACCIDENT",
      COUNTDOWN: "COUNTDOWN ACTIVE",
      CANCELLED: "ALERT CANCELLED",
      ALERT: "ALERT TRIGGERED"
    }[s.status] || s.status;

    const danger = ["ACCIDENT", "COUNTDOWN", "ALERT"].includes(s.status);
    $("indicator").classList.toggle("danger", danger);
    $("message").textContent = {
      SAFE: connected ? "Arduino reports normal status." : "Waiting for Arduino messages.",
      ACCIDENT: "Possible accident reported by the device.",
      COUNTDOWN: "Countdown active. Use the physical cancel button if safe.",
      CANCELLED: "Countdown cancelled.",
      ALERT: "Arduino reports that its countdown expired."
    }[s.status] || "Waiting for device status.";

    $("tilt").textContent = s.tilt;
    $("tilt").className = "value " + (s.tilt === "NORMAL" ? "ok" : "bad");
    $("impact").textContent = s.impact;
    $("impact").className = "value " + (s.impact === "NONE" ? "ok" : "bad");

    $("countdown").textContent =
      s.status === "COUNTDOWN" ? s.countdown : "";

    $("cancel").hidden = s.status !== "ACCIDENT" && s.status !== "COUNTDOWN";
    $("event").textContent = s.last_event || "No event yet";
    $("eventTime").textContent = s.last_event_time
      ? "Updated: " + new Date(s.last_event_time * 1000).toLocaleString()
      : "";
    $("serialLine").textContent = s.last_serial
      ? "Last Arduino message: " + s.last_serial : "";
  } catch (error) {
    $("connection").textContent = "● WEBSITE SERVER ERROR";
    $("connection").style.color = "#fb7185";
    $("message").textContent = "Unable to load status. Refresh the page later.";
  }
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
      ? contact.name + " — " + contact.phone : contact.name;
    $("contacts").appendChild(line);
  });

  $("contactName").value = "";
  $("contactPhone").value = "";
}

refreshStatus();
setInterval(refreshStatus, 1000);
</script>
</body>
</html>
"""


@app.get("/")
def home():
    return render_template_string(PAGE)


@app.get("/api/status")
def get_status():
    now = time.time()

    with lock:
        data = dict(state)
        last_seen = data["device_last_seen"]
        data["device_connected"] = (
            last_seen is not None and now - last_seen < 15
        )

        if data["status"] == "COUNTDOWN" and data["countdown_start"] is not None:
            elapsed = int(now - data["countdown_start"])
            data["countdown"] = max(0, data["countdown_value"] - elapsed)

            # Auto-complete website demo countdowns.
            if data["countdown"] == 0 and not data["device_connected"]:
                state.update(
                    status="ALERT",
                    alert=True,
                    countdown_start=None,
                    last_event="Website demo countdown expired",
                    last_event_time=now
                )
                data.update(
                    status="ALERT",
                    alert=True,
                    countdown=0,
                    countdown_start=None,
                    last_event="Website demo countdown expired",
                    last_event_time=now
                )
        else:
            data["countdown"] = data["countdown_value"]

        data["countdown_start"] = None

    return jsonify(data)


@app.post("/api/device")
def receive_device():
    supplied_token = request.headers.get("X-Device-Token", "")

    if not hmac.compare_digest(supplied_token, DEVICE_TOKEN):
        return jsonify({"ok": False, "error": "Unauthorized"}), 401

    body = request.get_json(silent=True) or {}
    message = str(body.get("message", "")).strip()

    if not message or len(message) > 100:
        return jsonify({"ok": False, "error": "Invalid message"}), 400

    now = time.time()

    with lock:
        state["device_last_seen"] = now
        state["last_serial"] = message

        if message == "BIKEGUARD_CONNECTED":
            state["last_event"] = "Arduino connected to Python bridge"

        elif message == "BG:SAFE":
            if state["status"] not in ("COUNTDOWN", "ALERT"):
                state.update(
                    status="SAFE",
                    tilt="NORMAL",
                    impact="NONE",
                    countdown_start=None,
                    countdown_value=0,
                    alert=False,
                    last_event="Arduino reports normal status"
                )

        elif message == "BG:ACCIDENT":
            state.update(
                status="ACCIDENT",
                tilt="ABNORMAL",
                impact="TILT DETECTED",
                countdown_start=None,
                countdown_value=0,
                alert=False,
                last_event="Arduino detected abnormal tilt"
            )

        elif message.startswith("BG:COUNTDOWN:"):
            try:
                seconds = int(message.split(":")[-1])
                seconds = max(0, min(60, seconds))
            except ValueError:
                return jsonify({"ok": False, "error": "Invalid countdown"}), 400

            state.update(
                status="COUNTDOWN",
                tilt="ABNORMAL",
                impact="TILT DETECTED",
                countdown_value=seconds,
                countdown_start=now,
                alert=False,
                last_event=f"Arduino countdown: {seconds} seconds"
            )

        elif message == "BG:CANCELLED":
            state.update(
                status="CANCELLED",
                tilt="NORMAL",
                impact="NONE",
                countdown_start=None,
                countdown_value=0,
                alert=False,
                last_event="Countdown cancelled using the Arduino button"
            )

        elif message == "BG:ALERT":
            state.update(
                status="ALERT",
                tilt="ABNORMAL",
                impact="TILT DETECTED",
                countdown_start=None,
                countdown_value=0,
                alert=True,
                last_event="Arduino countdown expired; alert triggered"
            )

        else:
            state["last_event"] = "Arduino message received"

        state["last_event_time"] = now

    return jsonify({"ok": True})


@app.post("/api/test")
def test():
    with lock:
        state.update(
            status="COUNTDOWN",
            tilt="ABNORMAL",
            impact="DEMO ONLY",
            countdown_start=time.time(),
            countdown_value=10,
            alert=False,
            last_event="Website demo countdown started",
            last_event_time=time.time()
        )
    return jsonify({"ok": True})


@app.post("/api/cancel")
def cancel():
    with lock:
        state.update(
            status="CANCELLED",
            tilt="NORMAL",
            impact="NONE",
            countdown_start=None,
            countdown_value=0,
            alert=False,
            last_event="Website demo cancelled",
            last_event_time=time.time()
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
            countdown_value=0,
            alert=False,
            last_event="Website status reset",
            last_event_time=time.time()
        )
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
