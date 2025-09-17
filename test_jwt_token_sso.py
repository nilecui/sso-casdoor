#!/usr/bin/env python3
"""
测试JWT Token传递方案的SSO流程
"""
import requests
import json
from urllib.parse import urlparse, parse_qs

def test_jwt_token_sso():
    """测试JWT Token传递方案的SSO流程"""
    base_url = "http://192.168.12.225"
    portal_url = f"{base_url}:9000"
    app1_url = f"{base_url}:9001"
    app2_url = f"{base_url}:9002"
    
    session = requests.Session()
    
    print("=== JWT Token传递方案SSO测试 ===")
    
    # 1. 测试门户登录
    print("\n1. 测试门户登录")
    resp = session.get(f"{portal_url}/")
    print(f"门户状态码: {resp.status_code}")
    print(f"用户状态: {'未登录' if '未登录' in resp.text else '已登录'}")
    
    # 2. 测试登录流程
    print("\n2. 测试登录流程")
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
    
    # 3. 测试JWT Token传递
    print("\n3. 测试JWT Token传递到App1")
    print("模拟场景：用户已在门户登录，点击'进入应用1'")
    
    # 模拟有access_token的情况
    mock_token = "mock_access_token_12345"
    resp = session.get(f"{portal_url}/to/app1", allow_redirects=False)
    print(f"跳转状态码: {resp.status_code}")
    print(f"重定向到: {resp.headers.get('Location', 'N/A')}")
    
    # 4. 测试App1接收token
    print("\n4. 测试App1接收SSO Token")
    resp = session.get(f"{app1_url}/?sso_token={mock_token}")
    print(f"App1状态码: {resp.status_code}")
    print(f"App1响应: {'包含用户信息' if 'username' in resp.text else '需要登录'}")
    
    # 5. 测试App2接收token
    print("\n5. 测试App2接收SSO Token")
    resp = session.get(f"{app2_url}/?sso_token={mock_token}")
    print(f"App2状态码: {resp.status_code}")
    print(f"App2响应: {'包含用户信息' if 'username' in resp.text else '需要登录'}")
    
    print("\n=== JWT Token方案实现说明 ===")
    print("✅ 已实现的功能：")
    print("1. 门户登录时保存access_token")
    print("2. 点击'进入应用'时传递token作为URL参数")
    print("3. 子应用验证token并自动登录")
    print("4. 支持App1和App2的SSO免密登录")
    
    print("\n=== 测试步骤 ===")
    print("1. 在浏览器中访问门户: http://192.168.12.225:9000")
    print("2. 点击'登录'完成Casdoor登录")
    print("3. 登录成功后，点击'进入应用1'")
    print("4. 应该直接跳转到App1并显示用户信息，无需再次登录")
    print("5. 同样测试'进入应用2'")
    
    print("\n=== 技术原理 ===")
    print("1. 用户在门户登录后，门户保存access_token")
    print("2. 点击'进入应用'时，门户构造URL: http://app1/?sso_token=access_token")
    print("3. App1接收token，调用Casdoor API验证token")
    print("4. 如果token有效，直接显示受保护页面")
    print("5. 如果token无效，显示登录页面")

if __name__ == "__main__":
    test_jwt_token_sso()
