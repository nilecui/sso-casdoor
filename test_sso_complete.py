#!/usr/bin/env python3
"""
测试完整的SSO流程：门户登录 -> 免密跳转到app1
"""
import requests
import json
from urllib.parse import urlparse, parse_qs

def test_complete_sso_flow():
    base_url = "http://192.168.12.225"
    portal_url = f"{base_url}:9000"
    casdoor_url = f"{base_url}:8000"
    
    session = requests.Session()
    
    print("=== 测试完整SSO流程 ===")
    
    # 1. 访问门户首页
    print("\n1. 访问门户首页")
    resp = session.get(f"{portal_url}/")
    print(f"状态码: {resp.status_code}")
    print(f"内容包含: {'未登录' in resp.text}")
    
    # 2. 点击登录按钮
    print("\n2. 点击登录按钮")
    resp = session.get(f"{portal_url}/login", allow_redirects=False)
    print(f"状态码: {resp.status_code}")
    print(f"重定向到: {resp.headers.get('Location', 'N/A')}")
    
    if resp.status_code == 307:
        auth_url = resp.headers.get('Location')
        print(f"授权URL: {auth_url}")
        
        # 解析授权URL参数
        parsed = urlparse(auth_url)
        params = parse_qs(parsed.query)
        print(f"Client ID: {params.get('client_id', ['N/A'])[0]}")
        print(f"Redirect URI: {params.get('redirect_uri', ['N/A'])[0]}")
        print(f"Scope: {params.get('scope', ['N/A'])[0]}")
        print(f"State: {params.get('state', ['N/A'])[0]}")
        
        # 检查是否有prompt参数
        if 'prompt' in params:
            print(f"Prompt: {params['prompt'][0]}")
        else:
            print("Prompt: 无 (正常登录)")
    
    # 3. 模拟用户已登录状态（通过直接访问Casdoor登录）
    print("\n3. 模拟用户登录状态")
    print("注意：这里需要手动在浏览器中完成Casdoor登录")
    print("登录后，门户会保存用户会话")
    
    # 4. 测试免密跳转到app1
    print("\n4. 测试免密跳转到app1")
    resp = session.get(f"{portal_url}/to/app1", allow_redirects=False)
    print(f"状态码: {resp.status_code}")
    print(f"重定向到: {resp.headers.get('Location', 'N/A')}")
    
    if resp.status_code == 307:
        redirect_url = resp.headers.get('Location')
        if redirect_url == "/login":
            print("❌ 用户未登录，重定向到登录页面")
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
                    print(f"Prompt: {params['prompt'][0]} {'✅' if params['prompt'][0] == 'none' else '❌'}")
                else:
                    print("Prompt: 无 ❌")
                
                if 'id_token_hint' in params:
                    print(f"ID Token Hint: {params['id_token_hint'][0][:20]}... ✅")
                else:
                    print("ID Token Hint: 无 ❌")
    
    print("\n=== 测试完成 ===")
    print("\n要实现SSO免密登录，需要：")
    print("1. 用户先在门户完成登录")
    print("2. 门户保存用户会话和id_token")
    print("3. 点击'进入应用1'时，使用prompt=none和id_token_hint进行静默授权")
    print("4. Casdoor验证会话后直接重定向到app1，无需再次登录")

if __name__ == "__main__":
    test_complete_sso_flow()
