import time
import serial
import requests

# Set these before running.
PORT = 'COM4'
WEBSITE = 'https://YOUR-VERCEL-PROJECT.vercel.app'
DEVICE_TOKEN = 'PASTE_THE_SAME_DEVICE_TOKEN_FROM_VERCEL'
BAUD_RATE = 115200
API_URL = WEBSITE.rstrip('/') + '/api/device'


def main():
    print('BikeGuard bridge starting...')
    print(f'Connecting to {PORT} at {BAUD_RATE} baud')
    with serial.Serial(PORT, BAUD_RATE, timeout=1) as ser:
        time.sleep(2)
        print('Connected. Keep this window open while testing.')
        while True:
            try:
                raw = ser.readline()
                if not raw:
                    continue
                message = raw.decode('utf-8', errors='replace').strip()
                if not message:
                    continue
                print('Arduino:', message)
                try:
                    response = requests.post(
                        API_URL,
                        json={'message': message},
                        headers={'X-Device-Token': DEVICE_TOKEN},
                        timeout=10,
                    )
                    print('Vercel:', response.status_code, response.text[:250])
                except requests.RequestException as exc:
                    print('Network error:', exc)
                    time.sleep(2)
            except KeyboardInterrupt:
                print('\nBridge stopped.')
                break


if __name__ == '__main__':
    main()
