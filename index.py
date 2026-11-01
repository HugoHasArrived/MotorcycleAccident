
import os
from datetime import datetime, timezone

from flask import Flask, request, jsonify
from pymongo import MongoClient, DESCENDING

app = Flask(__name__)

MONGODB_URI = os.environ.get('MONGODB_URI', '')
MONGODB_DB = os.environ.get('MONGODB_DB', 'bikeguard')

_memory_latest = None


def get_collection():
    if not MONGODB_URI:
        return None

    client = MongoClient(
        MONGODB_URI,
        serverSelectionTimeoutMS=4000
    )
    return client[MONGODB_DB]['events']


@app.get('/api/status')
def status():
    global _memory_latest

    try:
        col = get_collection()

        latest = (
            col.find_one(
                {},
                {'_id': 0},
                sort=[('received_at', DESCENDING)]
            )
            if col is not None
            else _memory_latest
        )

        return jsonify({
            'ok': True,
            'storage': 'mongodb' if col is not None else 'temporary-memory',
            'latest': latest
        })

    except Exception as exc:
        return jsonify({
            'ok': False,
            'error': 'Database unavailable',
            'detail': str(exc)
        }), 503


@app.post('/api/device')
def device():
    global _memory_latest

    body = request.get_json(silent=True) or {}
    message = body.get('message')

    if not isinstance(message, str) or not message.strip():
        return jsonify({
            'ok': False,
            'error': 'Expected a non-empty message'
        }), 400

    message = message.strip()[:2000]

    event = {
        'message': message,
        'received_at': datetime.now(timezone.utc).isoformat()
    }

    parts = message.split(',')

    if len(parts) >= 5 and parts[0] == 'BG':
        event['state'] = parts[1]

        try:
            event['latitude'] = float(parts[2]) if parts[2] else None
            event['longitude'] = float(parts[3]) if parts[3] else None
        except ValueError:
            event['latitude'] = None
            event['longitude'] = None

        event['gps_valid'] = parts[4] == '1'

    try:
        col = get_collection()

        if col is not None:
            col.insert_one(event)
        else:
            _memory_latest = event

    except Exception as exc:
        return jsonify({
            'ok': False,
            'error': 'Could not save event',
            'detail': str(exc)
        }), 503

    return jsonify({
        'ok': True,
        'saved': True,
        'received': message
    })
