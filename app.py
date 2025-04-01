from flask import Flask, jsonify, request, render_template_string, send_from_directory
import json
import os
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)

# 配置文件路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'static', 'config.js')

def load_config():
    try:
        app.logger.debug(f'尝试加载配置文件: {CONFIG_FILE}')
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                app.logger.debug(f'配置文件内容: {content}')
                # 提取CONFIG对象的内容
                config_str = content.split('CONFIG = ')[1].strip().rstrip(';')
                config = json.loads(config_str)
                app.logger.debug(f'解析后的配置: {config}')
                return config
        else:
            app.logger.warning(f'配置文件不存在: {CONFIG_FILE}')
    except Exception as e:
        app.logger.error(f'加载配置文件时出错: {str(e)}')
    return {"activeDomains": [], "blockedDomains": [], "backupDomains": []}

def save_config(config):
    try:
        app.logger.debug(f'尝试保存配置: {config}')
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            content = f'const CONFIG = {json.dumps(config, ensure_ascii=False, indent=4)};'
            f.write(content)
            app.logger.debug('配置保存成功')
    except Exception as e:
        app.logger.error(f'保存配置文件时出错: {str(e)}')
        raise

# 静态文件路由
@app.route('/static/<path:filename>')
def serve_static(filename):
    try:
        app.logger.debug(f'请求静态文件: {filename}')
        return send_from_directory(os.path.join(BASE_DIR, 'static'), filename)
    except Exception as e:
        app.logger.error(f'访问静态文件时出错: {str(e)}')
        return str(e), 500

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
    # 获取可用域名列表（排除已禁用的域名）
    available_domains = [d for d in config['activeDomains'] if d not in config['blockedDomains']]
    
    if not available_domains:
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
    return f'<script>window.location.href = "https://{available_domains[0]}";</script>'

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
            .input-group input {
                flex: 1;
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

                activeList.innerHTML = config.activeDomains
                    .filter(domain => !config.blockedDomains.includes(domain))
                    .map(domain => createDomainElement(domain, 'active'))
                    .join('');

                blockedList.innerHTML = config.blockedDomains
                    .map(domain => createDomainElement(domain, 'blocked'))
                    .join('');
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
                    
                    if (config.activeDomains.includes(domain)) {
                        alert('该域名已存在');
                        return;
                    }

                    config.activeDomains.push(domain);

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
                    
                    const existingDomains = new Set(config.activeDomains);
                    const newDomains = domains.filter(d => !existingDomains.has(d));

                    if (newDomains.length === 0) {
                        alert('所有输入的域名都已存在');
                        return;
                    }

                    config.activeDomains.push(...newDomains);

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
                    
                    if (fromStatus === 'active') {
                        config.blockedDomains.push(domain);
                    } else {
                        config.blockedDomains = config.blockedDomains.filter(d => d !== domain);
                    }

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
                    
                    config.activeDomains = config.activeDomains.filter(d => d !== domain);
                    config.blockedDomains = config.blockedDomains.filter(d => d !== domain);

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
    try:
        config = load_config()
        app.logger.debug(f'获取配置: {config}')
        return jsonify(config)
    except Exception as e:
        app.logger.error(f'获取配置时出错: {str(e)}')
        return jsonify({"error": str(e)}), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    try:
        config = request.json
        app.logger.debug(f'更新配置: {config}')
        save_config(config)
        return jsonify({"status": "success"})
    except Exception as e:
        app.logger.error(f'更新配置时出错: {str(e)}')
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 