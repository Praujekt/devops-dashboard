from flask import Flask, jsonify
import psutil
import subprocess
import os
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'healthy',
        'message': 'DevOps Dashboard API'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200

@app.route('/metrics')
def get_metrics():
    return jsonify({
        'cpu_percent': psutil.cpu_percent(interval=1),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'kubernetes_pods': get_pod_count()
    })

def get_pod_count():
    try:
        result = subprocess.run(
            ['kubectl', 'get', 'pods', '-A', '--no-headers'],
            capture_output=True, 
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            return len([line for line in lines if line])
        return 0
    except Exception as e:
        print(f"Error getting pod count: {e}")
        return 0
    
@app.route('/f1/next-race')
def next_f1_race():
    try:
        # OpenF1 doesn't have a "next race" endpoint, so we'll use a static 2026 calendar
        # Or we can scrape F1.com, but for now let's return current season info
        response = requests.get('https://api.openf1.org/v1/sessions?session_name=Race&year=2026', timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Find next race (first one in the future)
        from datetime import datetime
        now = datetime.utcnow()
        
        for session in data:
            session_date = datetime.fromisoformat(session['date_start'].replace('Z', '+00:00'))
            if session_date > now:
                return jsonify({
                    'race_name': session['meeting_name'],
                    'location': session['location'],
                    'country': session['country_name'],
                    'date': session['date_start'],
                    'circuit': session['circuit_short_name']
                })
        
        return jsonify({'message': 'No upcoming race found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/f1/latest-session')
def latest_session():
    try:
        response = requests.get('https://api.openf1.org/v1/sessions?session_name=Race&year=2026', timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data:
            latest = data[-1]  # Get most recent
            return jsonify({
                'race_name': latest['meeting_name'],
                'location': latest['location'],
                'country': latest['country_name'],
                'date': latest['date_start'],
                'circuit': latest['circuit_short_name']
            })
        
        return jsonify({'message': 'No session data found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)