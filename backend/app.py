from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
import os

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# 配置文件路径
CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "activeDomains": [],
        "blockedDomains": [],
        "backupDomains": []
    }

def save_config(config):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/admin')
def serve_admin():
    return send_from_directory(app.static_folder, 'admin.html')

@app.route('/redirect')
def serve_redirect():
    return send_from_directory(app.static_folder, 'redirect.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify(load_config())

@app.route('/api/config', methods=['POST'])
def update_config():
    config = request.json
    save_config(config)
    return jsonify({"status": "success"})

@app.route('/api/domains/active', methods=['GET'])
def get_active_domains():
    config = load_config()
    return jsonify(config['activeDomains'])

@app.route('/api/domains/blocked', methods=['GET'])
def get_blocked_domains():
    config = load_config()
    return jsonify(config['blockedDomains'])

@app.route('/api/domains/backup', methods=['GET'])
def get_backup_domains():
    config = load_config()
    return jsonify(config['backupDomains'])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 