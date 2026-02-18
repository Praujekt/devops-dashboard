from flask import Flask, jsonify
import psutil
import subprocess
import os

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)