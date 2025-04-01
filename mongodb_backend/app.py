from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import re

# 加载环境变量
load_dotenv()

app = Flask(__name__)
CORS(app)  # 启用跨域支持

# MongoDB 连接
MONGODB_URI = os.getenv('MONGODB_URI')
if not MONGODB_URI:
    raise ValueError("No MongoDB URI found. Please set MONGODB_URI environment variable.")

client = MongoClient(MONGODB_URI)
db = client.domain_manager
domains_collection = db.domains

def parse_domains_from_config(content):
    # 使用正则表达式提取域名列表
    active_pattern = r'activeDomains:\s*\[(.*?)\]'
    active_match = re.search(active_pattern, content, re.DOTALL)
    
    if active_match:
        # 提取域名并清理格式
        domains_str = active_match.group(1)
        domains = []
        for line in domains_str.split('\n'):
            # 提取引号中的域名
            domain_match = re.search(r'"([^"]+)"', line)
            if domain_match:
                domains.append(domain_match.group(1))
        return domains
    return []

# 初始化域名列表
@app.route('/api/init', methods=['POST'])
def init_domains():
    try:
        if domains_collection.count_documents({}) == 0:
            config_content = request.json.get('config')
            if not config_content:
                return jsonify({'error': '未提供配置内容'}), 400
                
            domains = parse_domains_from_config(config_content)
            for domain in domains:
                if domain:  # 确保域名不为空
                    domains_collection.insert_one({
                        'domain': domain,
                        'is_active': True,
                        'blocked_at': None
                    })
            return jsonify({'message': '域名初始化成功'})
        return jsonify({'message': '域名已经初始化'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/domains', methods=['GET'])
def get_domains():
    try:
        domains = list(domains_collection.find({}, {'_id': 0}))
        return jsonify(domains)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/domains/<domain>', methods=['PUT'])
def update_domain_status(domain):
    try:
        data = request.get_json()
        result = domains_collection.update_one(
            {'domain': domain},
            {'$set': {
                'is_active': data.get('is_active', True),
                'blocked_at': data.get('blocked_at')
            }}
        )
        if result.modified_count:
            return jsonify({'message': '域名状态已更新'})
        return jsonify({'error': '域名不存在'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/domains/status', methods=['GET'])
def get_domain_status():
    try:
        active_domains = list(domains_collection.find(
            {'is_active': True},
            {'domain': 1, '_id': 0}
        ))
        blocked_domains = list(domains_collection.find(
            {'is_active': False},
            {'domain': 1, 'blocked_at': 1, '_id': 0}
        ))
        return jsonify({
            'active_domains': active_domains,
            'blocked_domains': blocked_domains
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return jsonify({
        'status': 'running',
        'message': '域名管理 API 服务正在运行'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5001))) 