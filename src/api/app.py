from flask import Flask, jsonify, send_from_directory
import psutil
import subprocess
import os
import requests

app = Flask(__name__)

@app.route('/')
def index():
    web_dir = os.path.join(os.path.dirname(__file__), '..', 'web')
    return send_from_directory(web_dir, 'index.html')

@app.route('/api')
def api_info():
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

@app.route('/k8s/pods')
def get_pod_details():
    try:
        result = subprocess.run(
            ['kubectl', 'get', 'pods', '-n', 'default', '-o', 'json'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            
            pods = []
            for item in data.get('items', []):
                pod_info = {
                    'name': item['metadata']['name'],
                    'status': item['status']['phase'],
                    'ready': sum(1 for c in item['status'].get('containerStatuses', []) if c.get('ready', False)),
                    'total_containers': len(item['spec']['containers']),
                    'restarts': sum(c.get('restartCount', 0) for c in item['status'].get('containerStatuses', [])),
                    'age': item['metadata']['creationTimestamp']
                }
                pods.append(pod_info)
            
            return jsonify({'pods': pods})
        return jsonify({'error': 'Failed to get pods'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_pod_count():
    try:
        result = subprocess.run(
            ['kubectl', 'get', 'pods', '-n', 'default', '--no-headers'],
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
    
@app.route('/environment')
def get_environment():
    return jsonify({
        'environment': os.environ.get('ENVIRONMENT', 'unknown'),
        'version': os.environ.get('APP_VERSION', 'v4')
    })
    
@app.route('/f1/next-race')
def next_f1_race():
    try:
        response = requests.get('https://api.openf1.org/v1/sessions?session_name=Race&year=2026', timeout=5)
        response.raise_for_status()
        data = response.json()
        
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        for session in data:
            session_date = datetime.fromisoformat(session['date_start'])
            if session_date > now:
                return jsonify({
                    'location': session['location'],
                    'country': session['country_name'],
                    'date': session['date_start'],
                    'circuit': session['circuit_short_name'],
                    'session_type': session['session_type']
                })
        
        return jsonify({'message': 'No upcoming race found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/f1/latest-race')
def latest_race():
    try:
        response = requests.get('https://api.openf1.org/v1/sessions?session_name=Race&year=2026', timeout=5)
        response.raise_for_status()
        data = response.json()
        
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        # Find most recent race in the past
        past_races = []
        for session in data:
            session_date = datetime.fromisoformat(session['date_start'])
            if session_date < now:
                past_races.append(session)
        
        if past_races:
            latest = past_races[-1]  # Last one in the list
            return jsonify({
                'location': latest['location'],
                'country': latest['country_name'],
                'date': latest['date_start'],
                'circuit': latest['circuit_short_name']
            })
        
        return jsonify({'message': 'No past races found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)