# BikeGuard Complete Starter

## Included
- `arduino/BikeGuard.ino`: Arduino UNO sketch for tilt switch, cancel countdown, buzzer and NEO-6M GPS.
- `bridge.py`: reads USB serial messages and forwards them to Vercel.
- `api/index.py`: authenticated device endpoint and dashboard status endpoint.
- `public/index.html`: responsive dashboard.
- `vercel.json`: Vercel routing.

## Wiring
- Tilt switch: one leg D2, other leg GND.
- Cancel pushbutton: one electrical side D7, opposite side GND.
- Buzzer positive (+) D8; negative (-) GND.
- NEO-6M TX -> Arduino D4.
- NEO-6M RX -> Arduino D5 (optional).
- GPS GND -> Arduino GND.
- GPS VCC -> only a voltage supported by your exact breakout board. Check its label/specification first.
- Arduino USB cable -> computer while using the Python bridge.

## Arduino
1. Install Arduino IDE.
2. In Library Manager, install `TinyGPSPlus` by Mikal Hart.
3. Open `arduino/BikeGuard.ino`, select Arduino Uno and the correct COM port, then upload.
4. Test GPS outdoors with a clear view of the sky; first fix can take several minutes.

## Vercel deployment
1. Upload the contents of this folder to a GitHub repository.
2. Import the repository into Vercel.
3. Set Environment Variables: `DEVICE_TOKEN` (new long random secret), `MONGODB_URI` (MongoDB Atlas connection string, recommended), and optionally `MONGODB_DB` (`bikeguard`).
4. Redeploy after setting variables.
5. Open your Vercel domain.

Do not reuse any token exposed in chat or screenshots. Do not put the token in Arduino code or public HTML.

## Windows bridge
1. Edit `bridge.py`: set `WEBSITE` to your actual Vercel URL and `DEVICE_TOKEN` to the exact same secret configured in Vercel.
2. Close Arduino Serial Monitor to release COM4.
3. In Command Prompt in this folder, run `python -m pip install pyserial requests`.
4. Run `python bridge.py` and leave the window open while testing.

## Limitations and safety
Without GSM or another internet-capable module, the Arduino cannot contact the website by itself. The computer must stay connected to the Arduino by USB and to the internet while `bridge.py` runs. MongoDB is recommended because Vercel serverless memory is temporary and not reliable for persistent data. This is a school prototype, not a certified crash detector or emergency-response service. Test on a table; keep hard electronics and batteries off the head and out of any helmet impact liner.
