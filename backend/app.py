from flask import Flask, jsonify, request, send_from_directory, render_template_string
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

# 主页（显示二维码）
@app.route('/')
def index():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>域名切换二维码</title>
        <script src="https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js"></script>
        <style>
            body {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
                background-color: #f5f5f5;
                font-family: Arial, sans-serif;
            }
            .container {
                text-align: center;
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            #qrcode {
                margin: 20px auto;
                position: relative;
                width: 256px;
                height: 256px;
            }
            #qrcode img.logo {
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                width: 50px;
                height: 50px;
                z-index: 2;
                background: white;
                padding: 5px;
                border-radius: 50%;
            }
            .admin-link {
                margin-top: 20px;
                color: #666;
                text-decoration: none;
            }
            .admin-link:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>域名切换二维码</h1>
            <div id="qrcode"></div>
            <a href="/admin" class="admin-link">管理后台</a>
        </div>
        <script>
            // 生成二维码
            window.onload = function() {
                const qrcode = new QRCode(document.getElementById("qrcode"), {
                    text: "https://domain-switcher.onrender.com/redirect",
                    width: 256,
                    height: 256,
                    colorDark : "#000000",
                    colorLight : "#ffffff",
                    correctLevel : QRCode.CorrectLevel.H
                });

                // 添加Logo
                setTimeout(() => {
                    const img = document.createElement('img');
                    img.src = 'https://domain-switcher.onrender.com/static/logo.png';
                    img.className = 'logo';
                    img.onload = function() {
                        document.getElementById("qrcode").appendChild(img);
                    }
                }, 100);
            };
        </script>
    </body>
    </html>
    ''')

# 重定向页面
@app.route('/redirect')
def redirect():
    config = load_config()
    if not config['activeDomains']:
        return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>错误</title>
            <style>
                body {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                    margin: 0;
                    background-color: #f5f5f5;
                    font-family: Arial, sans-serif;
                }
                .container {
                    text-align: center;
                    background: white;
                    padding: 2rem;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                .error {
                    color: #dc3545;
                    margin: 10px 0;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>错误</h1>
                <div class="error">没有可用的域名，请联系管理员</div>
            </div>
        </body>
        </html>
        ''')
    
    # 直接跳转到第一个可用域名
    return f'<script>window.location.href = "https://{config["activeDomains"][0]}";</script>'

# 管理后台
@app.route('/admin')
def admin():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>域名管理后台</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }
            .container {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
            }
            .qr-link {
                color: #4CAF50;
                text-decoration: none;
            }
            .domain-lists {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .list-section {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
            }
            .domain-item {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px;
                background: white;
                margin: 5px 0;
                border-radius: 3px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            .domain-actions button {
                margin-left: 5px;
                padding: 5px 10px;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                background: #4CAF50;
                color: white;
            }
            .domain-actions button:hover {
                background: #45a049;
            }
            .add-domain {
                margin: 20px 0;
                padding: 15px;
                background: #e9ecef;
                border-radius: 5px;
            }
            .input-group {
                display: flex;
                gap: 10px;
                margin-bottom: 10px;
            }
            .input-group input, .input-group select {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            .input-group button {
                padding: 8px 15px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                cursor: pointer;
            }
            .save-bar {
                margin-top: 20px;
                text-align: right;
            }
            .save-bar button {
                padding: 10px 20px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>域名管理后台</h1>
                <a href="/" class="qr-link">查看二维码</a>
            </div>

            <div class="instructions">
                <h3>域名管理说明：</h3>
                <p>1. 当域名被微信封禁时，请将其移动到"已禁用域名"列表</p>
                <p>2. 可以通过单个添加或批量添加来添加新域名</p>
                <p>3. 可以通过"移动"按钮在不同状态之间移动域名</p>
                <p>4. 修改完成后，点击"保存更改"按钮保存更改</p>
            </div>

            <div class="add-domain">
                <h3>添加新域名</h3>
                <div class="input-group">
                    <input type="text" id="newDomain" placeholder="输入单个域名（例如：example.com）">
                    <select id="domainStatus">
                        <option value="active">可用域名</option>
                        <option value="backup">备用域名</option>
                    </select>
                    <button onclick="addNewDomain()">添加单个域名</button>
                </div>
                <div style="margin: 15px 0;">
                    <strong>或</strong>
                </div>
                <textarea id="batchDomains" placeholder="批量添加域名，每行一个域名，例如：
example1.com
example2.com
example3.com" style="width: 100%; height: 100px; margin-bottom: 10px;"></textarea>
                <div class="input-group">
                    <select id="batchDomainStatus">
                        <option value="active">可用域名</option>
                        <option value="backup">备用域名</option>
                    </select>
                    <button onclick="addBatchDomains()">批量添加域名</button>
                </div>
            </div>

            <div class="domain-lists">
                <div class="list-section">
                    <h3>可用域名</h3>
                    <div id="activeDomains" class="domain-list"></div>
                </div>
                <div class="list-section">
                    <h3>已禁用域名</h3>
                    <div id="blockedDomains" class="domain-list"></div>
                </div>
                <div class="list-section">
                    <h3>备用域名</h3>
                    <div id="backupDomains" class="domain-list"></div>
                </div>
            </div>

            <div class="save-bar">
                <button onclick="saveChanges()">保存更改</button>
            </div>
        </div>

        <script>
            const API_BASE_URL = window.location.origin;

            // 加载域名列表
            async function loadDomains() {
                try {
                    const response = await fetch(`${API_BASE_URL}/api/config`);
                    const config = await response.json();
                    displayDomains(config);
                } catch (error) {
                    console.error('加载域名失败:', error);
                    alert('加载域名失败，请检查网络连接');
                }
            }

            // 显示域名列表
            function displayDomains(config) {
                const activeList = document.getElementById('activeDomains');
                const blockedList = document.getElementById('blockedDomains');
                const backupList = document.getElementById('backupDomains');

                activeList.innerHTML = config.activeDomains.map(domain => createDomainElement(domain, 'active')).join('');
                blockedList.innerHTML = config.blockedDomains.map(domain => createDomainElement(domain, 'blocked')).join('');
                backupList.innerHTML = config.backupDomains.map(domain => createDomainElement(domain, 'backup')).join('');
            }

            // 创建域名元素
            function createDomainElement(domain, status) {
                return `
                    <div class="domain-item">
                        <span>${domain}</span>
                        <div class="domain-actions">
                            <button onclick="moveDomain('${domain}', '${status}')">移动</button>
                            <button onclick="deleteDomain('${domain}', '${status}')">删除</button>
                        </div>
                    </div>
                `;
            }

            // 添加新域名
            async function addNewDomain() {
                const input = document.getElementById('newDomain');
                const status = document.getElementById('domainStatus').value;
                const domain = input.value.trim();

                if (!domain) {
                    alert('请输入域名');
                    return;
                }

                if (!isValidDomain(domain)) {
                    alert('请输入有效的域名');
                    return;
                }

                try {
                    const response = await fetch(`${API_BASE_URL}/api/config`);
                    const config = await response.json();
                    
                    if (config.activeDomains.includes(domain) || 
                        config.blockedDomains.includes(domain) || 
                        config.backupDomains.includes(domain)) {
                        alert('该域名已存在');
                        return;
                    }

                    if (status === 'active') {
                        config.activeDomains.push(domain);
                    } else {
                        config.backupDomains.push(domain);
                    }

                    await fetch(`${API_BASE_URL}/api/config`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(config)
                    });

                    input.value = '';
                    displayDomains(config);
                } catch (error) {
                    console.error('添加域名失败:', error);
                    alert('添加域名失败，请检查网络连接');
                }
            }

            // 批量添加域名
            async function addBatchDomains() {
                const textarea = document.getElementById('batchDomains');
                const status = document.getElementById('batchDomainStatus').value;
                const domains = textarea.value.split('\n')
                    .map(d => d.trim())
                    .filter(d => d && isValidDomain(d));

                if (domains.length === 0) {
                    alert('请输入有效的域名');
                    return;
                }

                try {
                    const response = await fetch(`${API_BASE_URL}/api/config`);
                    const config = await response.json();
                    
                    const existingDomains = new Set([
                        ...config.activeDomains,
                        ...config.blockedDomains,
                        ...config.backupDomains
                    ]);

                    const newDomains = domains.filter(d => !existingDomains.has(d));

                    if (newDomains.length === 0) {
                        alert('所有输入的域名都已存在');
                        return;
                    }

                    if (status === 'active') {
                        config.activeDomains.push(...newDomains);
                    } else {
                        config.backupDomains.push(...newDomains);
                    }

                    await fetch(`${API_BASE_URL}/api/config`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(config)
                    });

                    textarea.value = '';
                    displayDomains(config);
                    alert(`成功添加 ${newDomains.length} 个新域名`);
                } catch (error) {
                    console.error('批量添加域名失败:', error);
                    alert('批量添加域名失败，请检查网络连接');
                }
            }

            // 移动域名
            async function moveDomain(domain, fromStatus) {
                try {
                    const response = await fetch(`${API_BASE_URL}/api/config`);
                    const config = await response.json();
                    
                    config[`${fromStatus}Domains`] = config[`${fromStatus}Domains`].filter(d => d !== domain);
                    
                    let toStatus;
                    if (fromStatus === 'active') {
                        toStatus = 'blocked';
                    } else if (fromStatus === 'blocked') {
                        toStatus = 'backup';
                    } else {
                        toStatus = 'active';
                    }
                    config[`${toStatus}Domains`].push(domain);

                    await fetch(`${API_BASE_URL}/api/config`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(config)
                    });

                    displayDomains(config);
                } catch (error) {
                    console.error('移动域名失败:', error);
                    alert('移动域名失败，请检查网络连接');
                }
            }

            // 删除域名
            async function deleteDomain(domain, status) {
                if (!confirm(`确定要删除域名 ${domain} 吗？`)) {
                    return;
                }

                try {
                    const response = await fetch(`${API_BASE_URL}/api/config`);
                    const config = await response.json();
                    
                    config[`${status}Domains`] = config[`${status}Domains`].filter(d => d !== domain);

                    await fetch(`${API_BASE_URL}/api/config`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(config)
                    });

                    displayDomains(config);
                } catch (error) {
                    console.error('删除域名失败:', error);
                    alert('删除域名失败，请检查网络连接');
                }
            }

            // 保存更改
            async function saveChanges() {
                try {
                    const response = await fetch(`${API_BASE_URL}/api/config`);
                    const config = await response.json();
                    
                    await fetch(`${API_BASE_URL}/api/config`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(config)
                    });

                    alert('保存成功！');
                } catch (error) {
                    console.error('保存失败:', error);
                    alert('保存失败，请检查网络连接');
                }
            }

            // 验证域名格式
            function isValidDomain(domain) {
                const pattern = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9](?:\.[a-zA-Z]{2,})+$/;
                return pattern.test(domain);
            }

            // 页面加载时获取域名列表
            window.onload = loadDomains;
        </script>
    </body>
    </html>
    ''')

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