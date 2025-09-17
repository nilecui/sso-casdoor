#!/usr/bin/env python3
"""
完整的SSO测试和解决方案
"""
import requests
import json
from urllib.parse import urlparse, parse_qs

def test_sso_flow():
    """测试SSO流程"""
    base_url = "http://192.168.12.225"
    portal_url = f"{base_url}:9000"
    app1_url = f"{base_url}:9001"
    
    session = requests.Session()
    
    print("=== SSO免密登录测试 ===")
    print("\n要实现SSO免密登录，需要按以下步骤操作：")
    print("\n步骤1: 在门户完成登录")
    print(f"1. 访问门户: {portal_url}")
    print("2. 点击右上角'登录'按钮")
    print("3. 在Casdoor中完成登录")
    print("4. 登录成功后会自动回到门户首页")
    
    print("\n步骤2: 测试免密跳转")
    print("1. 在门户首页点击'进入应用1'")
    print("2. 应该直接跳转到app1，无需再次登录")
    
    print("\n当前状态检查:")
    
    # 检查门户状态
    resp = session.get(f"{portal_url}/")
    if "未登录" in resp.text:
        print("❌ 门户: 用户未登录")
        print("   需要先完成门户登录才能测试SSO")
    else:
        print("✅ 门户: 用户已登录")
    
    # 检查app1状态
    try:
        resp = session.get(f"{app1_url}/")
        if resp.status_code == 200:
            print("✅ App1: 服务正常运行")
        else:
            print(f"❌ App1: 服务异常 (状态码: {resp.status_code})")
    except:
        print("❌ App1: 服务无法访问")
    
    print("\n=== 技术实现说明 ===")
    print("SSO免密登录的技术原理：")
    print("1. 用户在门户登录后，门户保存用户会话和id_token")
    print("2. 点击'进入应用1'时，门户构造静默授权请求：")
    print("   - 使用prompt=none参数")
    print("   - 传递id_token_hint参数")
    print("   - 使用app1的client_id")
    print("3. Casdoor验证用户会话，如果有效则直接重定向到app1")
    print("4. 如果会话无效，则回退到正常登录流程")
    
    print("\n=== 当前配置 ===")
    print("门户Client ID: 057afae89f6bab92b9")
    print("App1 Client ID: 0f122d9964f470c22a77")
    print("App2 Client ID: 0f122d9964f470c22a77")
    print("Casdoor地址: http://192.168.12.225:8000")
    
    print("\n=== 测试建议 ===")
    print("1. 在浏览器中访问门户并完成登录")
    print("2. 登录成功后，点击'进入应用1'")
    print("3. 观察是否直接跳转到app1而不需要再次登录")
    print("4. 如果仍然跳转到登录页面，检查Casdoor应用配置")

if __name__ == "__main__":
    test_sso_flow()
