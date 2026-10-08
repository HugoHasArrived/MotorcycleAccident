from flask import Flask, jsonify, render_template_string
import time

app = Flask(__name__)

system_state = {
    "status": "SAFE",
    "tilt": "NORMAL",
    "impact": "NONE",
    "gps": "NOT CONNECTED",
    "gsm": "NOT CONNECTED",
    "countdown": 0,
    "alert": False
}

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BikeGuard</title>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Arial, Helvetica, sans-serif;
    background:
        radial-gradient(circle at top, #263238 0%, #101417 45%, #050708 100%);
    color: white;
    min-height: 100vh;
}

header {
    padding: 25px;
    text-align: center;
    border-bottom: 1px solid #333;
    background: rgba(0,0,0,.35);
}

.logo {
    font-size: 32px;
    font-weight: 900;
    letter-spacing: 3px;
}

.subtitle {
    color: #aaa;
    margin-top: 6px;
}

.container {
    width: min(1100px, 94%);
    margin: 30px auto;
}

.status-card {
    background: rgba(20,25,28,.92);
    border: 1px solid #333;
    border-radius: 22px;
    padding: 35px;
    text-align: center;
    box-shadow: 0 15px 50px rgba(0,0,0,.4);
}

.status-light {
    width: 110px;
    height: 110px;
    border-radius: 50%;
    margin: 0 auto 20px;
    background: #16a34a;
    box-shadow: 0 0 45px rgba(22,163,74,.7);
}

.status-light.danger {
    background: #dc2626;
    box-shadow: 0 0 50px rgba(220,38,38,.9);
}

.status-title {
    font-size: 38px;
    font-weight: 900;
}

.status-message {
    color: #aaa;
    margin-top: 10px;
}

.grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 18px;
    margin-top: 20px;
}

.card {
    background: rgba(20,25,28,.9);
    border: 1px solid #333;
    border-radius: 18px;
    padding: 24px;
}

.card h3 {
    margin-top: 0;
    color: #ddd;
}

.value {
    font-size: 25px;
    font-weight: bold;
}

.normal {
    color: #4ade80;
}

.warning {
    color: #facc15;
}

.danger {
    color: #f87171;
}

.buttons {
    display: flex;
    gap: 15px;
    justify-content: center;
    margin-top: 25px;
    flex-wrap: wrap;
}

button {
    border: none;
    border-radius: 12px;
    padding: 15px 25px;
    font-size: 16px;
    font-weight: bold;
    cursor: pointer;
}

.test {
    background: #dc2626;
    color: white;
}

.cancel {
    background: #16a34a;
    color: white;
    display: none;
}

button:hover {
    transform: translateY(-2px);
    filter: brightness(1.1);
}

.countdown {
    font-size: 70px;
    font-weight: 900;
    color: #f87171;
    margin: 15px 0;
}

.location {
    margin-top: 20px;
    padding: 20px;
    border-radius: 15px;
    background: #111719;
}

footer {
    text-align: center;
    color: #777;
    padding: 30px;
}

@media(max-width:700px) {
    .grid {
        grid-template-columns: 1fr;
    }

    .status-title {
        font-size: 28px;
    }
}
</style>
</head>

<body>

<header>
    <div class="logo">BIKEGUARD</div>
    <div class="subtitle">
        Intelligent Bike Accident Detection & Emergency Alert System
    </div>
</header>

<div class="container">

    <div class="status-card">

        <div id="light" class="status-light"></div>

        <div id="statusTitle" class="status-title">
            SYSTEM SAFE
        </div>

        <div id="message" class="status-message">
            BikeGuard is monitoring the rider.
        </div>

        <div id="countdown" class="countdown"></div>

        <div class="buttons">

            <button class="test" onclick="testAccident()">
                TEST ACCIDENT ALERT
            </button>

            <button id="cancelButton"
                    class="cancel"
                    onclick="cancelAlert()">
                CANCEL ALERT
            </button>

        </div>

    </div>

    <div class="grid">

        <div class="card">
            <h3>Bike Sensor</h3>
            <div class="value normal">CONNECTED</div>
        </div>

        <div class="card">
            <h3>Tilt Detection</h3>
            <div id="tilt" class="value normal">NORMAL</div>
        </div>

        <div class="card">
            <h3>Impact Detection</h3>
            <div id="impact" class="value normal">NONE</div>
        </div>

        <div class="card">
            <h3>GPS</h3>
            <div class="value warning">NOT CONNECTED</div>
        </div>

        <div class="card">
            <h3>GSM</h3>
            <div class="value warning">NOT CONNECTED</div>
        </div>

        <div class="card">
            <h3>Emergency Contact</h3>
            <div class="value">READY</div>
        </div>

    </div>

    <div class="location">

        <h3>📍 Emergency Location</h3>

        <div id="locationText">
            GPS location will appear here when GPS hardware is connected.
        </div>

    </div>

</div>

<footer>
    BikeGuard • School Robotics & Engineering Project
</footer>

<script>

let timer = null;
let seconds = 10;

function testAccident() {

    if (timer !== null) {
        return;
    }

    seconds = 10;

    document.getElementById("light").classList.add("danger");

    document.getElementById("statusTitle").innerText =
        "POSSIBLE ACCIDENT";

    document.getElementById("message").innerText =
        "Accident detected. Confirm your safety.";

    document.getElementById("tilt").innerText =
        "ABNORMAL";

    document.getElementById("tilt").className =
        "value danger";

    document.getElementById("impact").innerText =
        "DETECTED";

    document.getElementById("impact").className =
        "value danger";

    document.getElementById("cancelButton").style.display =
        "inline-block";

    document.getElementById("countdown").innerText =
        seconds;

    timer = setInterval(function() {

        seconds--;

        document.getElementById("countdown").innerText =
            seconds;

        if (seconds <= 0) {

            clearInterval(timer);
            timer = null;

            sendEmergencyAlert();
        }

    }, 1000);
}


function cancelAlert() {

    if (timer !== null) {
        clearInterval(timer);
        timer = null;
    }

    document.getElementById("light").classList.remove("danger");

    document.getElementById("statusTitle").innerText =
        "ALERT CANCELLED";

    document.getElementById("message").innerText =
        "Rider confirmed they are safe.";

    document.getElementById("countdown").innerText = "";

    document.getElementById("cancelButton").style.display =
        "none";

    document.getElementById("tilt").innerText =
        "NORMAL";

    document.getElementById("tilt").className =
        "value normal";

    document.getElementById("impact").innerText =
        "NONE";

    document.getElementById("impact").className =
        "value normal";
}


function sendEmergencyAlert() {

    document.getElementById("statusTitle").innerText =
        "EMERGENCY ALERT";

    document.getElementById("message").innerText =
        "Emergency procedure activated.";

    document.getElementById("countdown").innerText =
        "🚨";

    document.getElementById("cancelButton").style.display =
        "none";

    document.getElementById("locationText").innerText =
        "Waiting for GPS hardware...";
}

</script>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)


@app.route("/api/status")
def status():
    return jsonify(system_state)


@app.route("/api/test")
def test():
    system_state["status"] = "ACCIDENT"
    system_state["tilt"] = "ABNORMAL"
    system_state["impact"] = "DETECTED"
    system_state["alert"] = True
    return jsonify(system_state)


@app.route("/api/reset")
def reset():
    system_state["status"] = "SAFE"
    system_state["tilt"] = "NORMAL"
    system_state["impact"] = "NONE"
    system_state["alert"] = False
    return jsonify(system_state)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
