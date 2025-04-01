import requests
import time
from typing import List, Optional
import threading
from datetime import datetime
import json
import urllib3

# 禁用SSL警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class DomainRotator:
    def __init__(self, domains: List[str], check_interval: int = 300):
        self.domains = domains
        self.current_index = 0
        self.domain_status = {domain: True for domain in domains}
        self.check_interval = check_interval
        self.lock = threading.Lock()
        self.last_check = {}
        self.blocked_domains = set()
        
    def check_domain(self, domain: str) -> bool:
        """检查域名是否可访问"""
        try:
            # 微信的User-Agent
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.20(0x18001442) NetType/WIFI Language/zh_CN',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
            }
            
            # 尝试HTTPS访问
            url = f"https://{domain}"
            print(f"\n正在检查域名 {domain} 的微信访问...")
            
            try:
                response = requests.get(url, headers=headers, timeout=5, verify=False)
                content = response.text.lower()
                
                # 检查页面特征（根据实际微信封禁页面）
                block_indicators = [
                    '已停止访问该网页',
                    '经网址安全检测',
                    '该网页包含恶意欺诈内容',
                    '为维护绿色上网环境',
                    '已停止访问',
                    '申请恢复访问'
                ]
                
                # 如果发现任何一个特征，说明被封禁
                for indicator in block_indicators:
                    if indicator in content:
                        print(f"域名 {domain} 已被微信封禁（检测到特征：{indicator}）")
                        return False
                
                print(f"域名 {domain} 微信访问正常")
                return True
                
            except requests.exceptions.RequestException as e:
                print(f"域名 {domain} 访问异常: {str(e)}")
                return True  # 如果是网络错误，不应该认为是被封禁
            
        except Exception as e:
            print(f"域名 {domain} 检查过程出错: {str(e)}")
            return True  # 如果是其他错误，不应该认为是被封禁
            
    def get_next_available_domain(self) -> Optional[str]:
        """获取下一个可用的域名"""
        with self.lock:
            start_index = self.current_index
            while True:
                domain = self.domains[self.current_index]
                
                # 如果域名已经被标记为封禁，直接跳过
                if domain in self.blocked_domains:
                    self.current_index = (self.current_index + 1) % len(self.domains)
                    if self.current_index == start_index:
                        return None
                    continue
                
                current_time = time.time()
                
                # 如果域名状态未知或上次检查时间超过间隔，重新检查
                if (domain not in self.last_check or 
                    current_time - self.last_check[domain] > self.check_interval):
                    print(f"\n开始检查域名: {domain}")
                    is_available = self.check_domain(domain)
                    self.domain_status[domain] = is_available
                    self.last_check[domain] = current_time
                    
                    if not is_available:
                        self.blocked_domains.add(domain)
                        print(f"域名 {domain} 已被标记为不可用")
                    else:
                        print(f"域名 {domain} 可用")
                
                if self.domain_status[domain]:
                    print(f"选择域名: {domain}")
                    return domain
                    
                self.current_index = (self.current_index + 1) % len(self.domains)
                if self.current_index == start_index:
                    return None
                    
    def mark_domain_unavailable(self, domain: str):
        """标记域名为不可用"""
        with self.lock:
            self.domain_status[domain] = False
            self.blocked_domains.add(domain)
            self.last_check[domain] = time.time()
            print(f"手动标记域名 {domain} 为不可用")
            
    def get_blocked_domains(self) -> List[str]:
        """获取所有被封禁的域名列表"""
        return list(self.blocked_domains)
        
    def clear_blocked_domain(self, domain: str):
        """清除域名的封禁状态"""
        with self.lock:
            if domain in self.blocked_domains:
                self.blocked_domains.remove(domain)
                self.domain_status[domain] = True
                self.last_check[domain] = 0  # 强制下次检查
                print(f"清除域名 {domain} 的封禁状态")

# 使用示例
if __name__ == "__main__":
    # 从配置文件加载域名列表
    with open('domains.json', 'r') as f:
        domains = json.load(f)
    
    rotator = DomainRotator(domains)
    
    # 测试获取可用域名
    print("开始测试域名可用性...")
    available_domain = rotator.get_next_available_domain()
    if available_domain:
        print(f"当前可用域名: {available_domain}")
    else:
        print("没有可用的域名") 