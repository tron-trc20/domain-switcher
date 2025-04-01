from flask import Flask, redirect, request, jsonify
from domain_rotator import DomainRotator
import json

app = Flask(__name__)

# 从配置文件加载域名列表
with open('domains.json', 'r') as f:
    domains = json.load(f)

rotator = DomainRotator(domains)

@app.route('/')
def redirect_to_available_domain():
    # 获取下一个可用域名
    available_domain = rotator.get_next_available_domain()
    
    if not available_domain:
        return "所有域名当前都不可用，请稍后再试", 503
        
    # 获取原始请求的路径和参数
    path = request.path
    query_string = request.query_string.decode('utf-8')
    
    # 构建重定向URL
    redirect_url = f"https://{available_domain}{path}"
    if query_string:
        redirect_url += f"?{query_string}"
        
    return redirect(redirect_url)

@app.route('/mark_unavailable/<domain>')
def mark_domain_unavailable(domain):
    if domain in domains:
        rotator.mark_domain_unavailable(domain)
        return f"已标记域名 {domain} 为不可用"
    return "域名不存在", 404

@app.route('/clear_blocked/<domain>')
def clear_blocked_domain(domain):
    if domain in domains:
        rotator.clear_blocked_domain(domain)
        return f"已清除域名 {domain} 的封禁状态"
    return "域名不存在", 404

@app.route('/blocked_domains')
def get_blocked_domains():
    return jsonify({
        "blocked_domains": rotator.get_blocked_domains()
    })

@app.route('/domain_status')
def get_domain_status():
    return jsonify({
        "current_index": rotator.current_index,
        "domain_status": rotator.domain_status,
        "blocked_domains": rotator.get_blocked_domains()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 