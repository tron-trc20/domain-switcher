from flask import Flask, render_template_string, send_from_directory
import os

app = Flask(__name__)

# 静态文件路由
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'), filename)

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
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>域名跳转</title>
            <script src="/static/config.js"></script>
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
                <h1>正在跳转...</h1>
                <div id="message"></div>
            </div>
            <script>
                window.onload = function() {
                    const availableDomains = CONFIG.activeDomains.filter(
                        domain => !CONFIG.blockedDomains.includes(domain)
                    );
                    
                    if (availableDomains.length > 0) {
                        window.location.href = "https://" + availableDomains[0];
                    } else {
                        document.getElementById("message").innerHTML = `
                            <div class="error">没有可用的域名，请联系管理员</div>
                        `;
                    }
                };
            </script>
        </body>
        </html>
    ''')

# 管理后台
@app.route('/admin')
def admin():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>域名管理后台</title>
        <script src="/static/config.js"></script>
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
                <p>1. 此页面仅用于查看当前域名状态</p>
                <p>2. 如需修改域名配置，请直接修改 GitHub 仓库中的 config.js 文件</p>
                <p>3. 修改完成后，在 Render 上重新部署即可生效</p>
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
        </div>

        <script>
            // 显示域名列表
            function displayDomains(config) {
                const activeList = document.getElementById('activeDomains');
                const blockedList = document.getElementById('blockedDomains');

                activeList.innerHTML = config.activeDomains
                    .filter(domain => !config.blockedDomains.includes(domain))
                    .map(domain => `
                        <div class="domain-item">
                            <span>${domain}</span>
                        </div>
                    `)
                    .join('');

                blockedList.innerHTML = config.blockedDomains
                    .map(domain => `
                        <div class="domain-item">
                            <span>${domain}</span>
                        </div>
                    `)
                    .join('');
            }

            // 页面加载时显示域名列表
            window.onload = function() {
                displayDomains(CONFIG);
            };
        </script>
    </body>
    </html>
    ''')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 