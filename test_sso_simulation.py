#!/usr/bin/env python3
"""
模拟用户已登录状态，测试SSO免密跳转
"""
import requests
import json
from urllib.parse import urlparse, parse_qs

def simulate_logged_in_user():
    """模拟用户已登录状态"""
    base_url = "http://192.168.12.225"
    portal_url = f"{base_url}:9000"
    
    session = requests.Session()
    
    print("=== 模拟用户已登录状态测试 ===")
    
    # 1. 先完成门户登录流程
    print("\n1. 开始门户登录流程")
    
    # 访问登录页面
    resp = session.get(f"{portal_url}/login", allow_redirects=False)
    print(f"登录重定向状态码: {resp.status_code}")
    
    if resp.status_code == 307:
        auth_url = resp.headers.get('Location')
        print(f"重定向到Casdoor: {auth_url}")
        
        # 解析授权URL
        parsed = urlparse(auth_url)
        params = parse_qs(parsed.query)
        print(f"门户Client ID: {params.get('client_id', ['N/A'])[0]}")
        print(f"门户Redirect URI: {params.get('redirect_uri', ['N/A'])[0]}")
        
        # 模拟用户完成登录（这里需要手动完成）
        print("\n⚠️  请手动在浏览器中完成以下步骤：")
        print(f"1. 访问: {auth_url}")
        print("2. 在Casdoor中完成登录")
        print("3. 登录成功后，门户会保存用户会话")
        print("4. 然后测试SSO免密跳转")
        
        return
    
    # 2. 测试SSO免密跳转（假设用户已登录）
    print("\n2. 测试SSO免密跳转到app1")
    resp = session.get(f"{portal_url}/to/app1", allow_redirects=False)
    print(f"状态码: {resp.status_code}")
    print(f"重定向到: {resp.headers.get('Location', 'N/A')}")
    
    if resp.status_code == 307:
        redirect_url = resp.headers.get('Location')
        if redirect_url == "/login":
            print("❌ 用户未登录，需要先完成门户登录")
        else:
            print(f"✅ 重定向到: {redirect_url}")
            
            # 解析重定向URL
            if redirect_url.startswith("http"):
                parsed = urlparse(redirect_url)
                params = parse_qs(parsed.query)
                print(f"App1 Client ID: {params.get('client_id', ['N/A'])[0]}")
                print(f"App1 Redirect URI: {params.get('redirect_uri', ['N/A'])[0]}")
                
                # 检查静默登录参数
                if 'prompt' in params:
                    prompt = params['prompt'][0]
                    print(f"Prompt: {prompt} {'✅' if prompt == 'none' else '❌'}")
                else:
                    print("Prompt: 无 ❌")
                
                if 'id_token_hint' in params:
                    hint = params['id_token_hint'][0]
                    print(f"ID Token Hint: {hint[:20]}... ✅")
                else:
                    print("ID Token Hint: 无 ❌")
                
                # 检查scope
                if 'scope' in params:
                    print(f"Scope: {params['scope'][0]}")
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    simulate_logged_in_user()
