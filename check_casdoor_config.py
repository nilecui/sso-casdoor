#!/usr/bin/env python3
"""
检查Casdoor配置的脚本
"""
import requests
import json

def check_app_config(client_id, redirect_uri):
    """检查应用配置"""
    url = "http://192.168.12.225:8000/api/get-app-login"
    params = {
        "clientId": client_id,
        "responseType": "code",
        "redirectUri": redirect_uri,
        "scope": "openid profile email",
        "state": "test"
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        print(f"客户端ID: {client_id}")
        print(f"重定向URI: {redirect_uri}")
        print(f"状态: {data.get('status', 'unknown')}")
        print(f"消息: {data.get('msg', 'no message')}")
        if data.get('data'):
            print(f"应用数据: {json.dumps(data['data'], indent=2)}")
        print("-" * 50)
        return data.get('status') == 'ok'
    except Exception as e:
        print(f"错误: {e}")
        return False

def main():
    """主函数"""
    print("检查Casdoor应用配置...")
    print("=" * 50)
    
    # 测试不同的客户端ID和重定向URI组合
    test_cases = [
        ("0f122d9964f470c22a77", "http://192.168.12.225:9000/callback"),
        ("0f122d9964f470c22a77", "http://localhost:9000/callback"),
        ("0f122d9964f470c22a77", "http://192.168.12.225:9001/callback"),
        ("0f122d9964f470c22a77", "http://localhost:9001/callback"),
        ("057afae89f6bab92b9", "http://192.168.12.225:9000/callback"),
        ("5d32e8498072413770bf", "http://192.168.12.225:9002/callback"),
    ]
    
    for client_id, redirect_uri in test_cases:
        check_app_config(client_id, redirect_uri)
    
    print("\n建议:")
    print("1. 如果所有测试都失败，说明需要在Casdoor管理界面中添加重定向URI")
    print("2. 访问 http://192.168.12.225:8000 登录管理界面")
    print("3. 进入 Applications 页面，找到对应的应用")
    print("4. 在 OAuth 配置中添加以下重定向URI:")
    print("   - http://192.168.12.225:9000/callback")
    print("   - http://192.168.12.225:9001/callback") 
    print("   - http://192.168.12.225:9002/callback")

if __name__ == "__main__":
    main()
