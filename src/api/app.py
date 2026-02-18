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
        response = requests.get('https://ergast.com/api/f1/current/next.json', timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if data['MRData']['RaceTable']['Races']:
            race = data['MRData']['RaceTable']['Races'][0]
            return jsonify({
                'race_name': race['raceName'],
                'circuit': race['Circuit']['circuitName'],
                'location': f"{race['Circuit']['Location']['locality']}, {race['Circuit']['Location']['country']}",
                'date': race['date'],
                'time': race.get('time', 'TBA'),
                'round': race['round'],
                'season': race['season']
            })
        else:
            return jsonify({'message': 'No upcoming race found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/f1/standings/drivers')
def driver_standings():
    try:
        response = requests.get('https://ergast.com/api/f1/current/driverStandings.json', timeout=5)
        response.raise_for_status()
        data = response.json()
        
        standings = []
        for item in data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']:
            standings.append({
                'position': item['position'],
                'points': item['points'],
                'wins': item['wins'],
                'driver': f"{item['Driver']['givenName']} {item['Driver']['familyName']}",
                'team': item['Constructors'][0]['name']
            })
        
        return jsonify({'standings': standings})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)