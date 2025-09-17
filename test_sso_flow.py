#!/usr/bin/env python3
"""
测试SSO流程的脚本
检查Casdoor的SSO会话状态和免密登录机制
"""
import urllib.request
import urllib.parse
import json
import re
from urllib.parse import urlparse, parse_qs

def test_casdoor_session():
    """测试Casdoor的SSO会话状态"""
    print("🔍 测试Casdoor SSO会话状态")
    print("=" * 50)
    
    # 1. 测试门户登录流程
    print("1. 测试门户登录流程...")
    portal_login_url = "http://192.168.12.225:9000/login"
    try:
        req = urllib.request.Request(portal_login_url)
        with urllib.request.urlopen(req) as response:
            redirect_url = response.getheader('Location')
            print(f"   HTTP状态码: {response.getcode()}")
            print(f"   门户登录重定向到: {redirect_url}")
            
            # 解析Casdoor授权URL
            if redirect_url and 'casdoor' in redirect_url:
                parsed = urlparse(redirect_url)
                params = parse_qs(parsed.query)
                print(f"   客户端ID: {params.get('client_id', ['N/A'])[0]}")
                print(f"   重定向URI: {params.get('redirect_uri', ['N/A'])[0]}")
                print(f"   作用域: {params.get('scope', ['N/A'])[0]}")
                print(f"   状态: {params.get('state', ['N/A'])[0]}")
            else:
                print("   ❌ 未重定向到Casdoor")
    except urllib.error.HTTPError as e:
        print(f"   HTTP错误: {e.code} - {e.reason}")
        redirect_url = e.headers.get('Location')
        if redirect_url:
            print(f"   重定向到: {redirect_url}")
    except Exception as e:
        print(f"   错误: {e}")
    
    print()

def test_app1_sso():
    """测试应用1的SSO流程"""
    print("2. 测试应用1 SSO流程...")
    app1_sso_url = "http://192.168.12.225:9000/to/app1"
    try:
        req = urllib.request.Request(app1_sso_url)
        with urllib.request.urlopen(req) as response:
            redirect_url = response.getheader('Location')
            print(f"   HTTP状态码: {response.getcode()}")
            print(f"   应用1 SSO重定向到: {redirect_url}")
            
            if redirect_url:
                parsed = urlparse(redirect_url)
                params = parse_qs(parsed.query)
                print(f"   客户端ID: {params.get('client_id', ['N/A'])[0]}")
                print(f"   重定向URI: {params.get('redirect_uri', ['N/A'])[0]}")
                print(f"   作用域: {params.get('scope', ['N/A'])[0]}")
                print(f"   状态: {params.get('state', ['N/A'])[0]}")
                print(f"   prompt参数: {params.get('prompt', ['N/A'])[0]}")
                print(f"   id_token_hint: {params.get('id_token_hint', ['N/A'])[0]}")
                
                # 检查是否包含静默登录参数
                if 'prompt=none' in redirect_url:
                    print("   ✅ 包含prompt=none参数")
                else:
                    print("   ❌ 缺少prompt=none参数")
                    
                if 'id_token_hint=' in redirect_url:
                    print("   ✅ 包含id_token_hint参数")
                else:
                    print("   ❌ 缺少id_token_hint参数")
            else:
                print("   ❌ 未重定向")
    except urllib.error.HTTPError as e:
        print(f"   HTTP错误: {e.code} - {e.reason}")
        redirect_url = e.headers.get('Location')
        if redirect_url:
            print(f"   重定向到: {redirect_url}")
    except Exception as e:
        print(f"   错误: {e}")
    
    print()

def test_casdoor_authorize():
    """测试Casdoor授权端点"""
    print("3. 测试Casdoor授权端点...")
    
    # 模拟静默登录请求
    auth_url = "http://192.168.12.225:8000/login/oauth/authorize"
    params = {
        'client_id': '0f122d9964f470c22a77',
        'response_type': 'code',
        'scope': 'openid profile email',
        'redirect_uri': 'http://192.168.12.225:9001/callback',
        'state': 'test_state',
        'prompt': 'none'
    }
    
    full_url = f"{auth_url}?{urllib.parse.urlencode(params)}"
    print(f"   测试URL: {full_url}")
    
    try:
        with urllib.request.urlopen(full_url) as response:
            content = response.read().decode('utf-8')
            
            # 检查响应内容
            if 'login' in content.lower():
                print("   ❌ 返回登录页面 - SSO会话无效")
            elif 'error' in content.lower():
                print("   ❌ 返回错误页面")
                # 尝试提取错误信息
                error_match = re.search(r'error["\']?\s*:\s*["\']?([^"\'}]+)', content)
                if error_match:
                    print(f"   错误信息: {error_match.group(1)}")
            else:
                print("   ✅ 可能成功 - 需要进一步检查")
                
    except urllib.error.HTTPError as e:
        if e.code == 302:  # 重定向
            redirect_url = e.headers.get('Location')
            print(f"   🔄 重定向到: {redirect_url}")
            if 'callback' in redirect_url and 'code=' in redirect_url:
                print("   ✅ 静默登录成功 - 返回授权码")
            else:
                print("   ❌ 重定向到非预期位置")
        else:
            print(f"   ❌ HTTP错误: {e.code}")
    except Exception as e:
        print(f"   错误: {e}")
    
    print()

def test_app_config():
    """测试应用配置"""
    print("4. 测试应用配置...")
    
    config_url = "http://192.168.12.225:8000/api/get-app-login"
    params = {
        'clientId': '0f122d9964f470c22a77',
        'responseType': 'code',
        'redirectUri': 'http://192.168.12.225:9001/callback',
        'scope': 'openid profile email',
        'state': 'test'
    }
    
    full_url = f"{config_url}?{urllib.parse.urlencode(params)}"
    
    try:
        with urllib.request.urlopen(full_url) as response:
            data = json.loads(response.read().decode('utf-8'))
            print(f"   配置状态: {data.get('status', 'unknown')}")
            print(f"   配置消息: {data.get('msg', 'no message')}")
            
            if data.get('data'):
                app_data = data['data']
                print(f"   应用名称: {app_data.get('name', 'N/A')}")
                print(f"   应用ID: {app_data.get('id', 'N/A')}")
                print(f"   客户端ID: {app_data.get('clientId', 'N/A')}")
                
                # 检查重定向URI配置
                redirect_uris = app_data.get('redirectUris', [])
                print(f"   配置的重定向URI: {redirect_uris}")
                
                if 'http://192.168.12.225:9001/callback' in redirect_uris:
                    print("   ✅ 重定向URI已正确配置")
                else:
                    print("   ❌ 重定向URI未配置")
            else:
                print("   ❌ 未返回应用配置数据")
                
    except Exception as e:
        print(f"   错误: {e}")
    
    print()

def main():
    """主函数"""
    print("🧪 SSO流程测试脚本")
    print("=" * 60)
    print()
    
    test_casdoor_session()
    test_app1_sso()
    test_casdoor_authorize()
    test_app_config()
    
    print("📋 测试总结和建议:")
    print("=" * 50)
    print("1. 如果缺少prompt=none参数，检查门户的/to/app1端点")
    print("2. 如果缺少id_token_hint参数，检查门户是否正确保存了id_token")
    print("3. 如果Casdoor返回登录页面，说明SSO会话无效")
    print("4. 如果重定向URI未配置，需要在Casdoor管理界面中添加")
    print()
    print("🔧 修复步骤:")
    print("1. 确保用户在门户正确登录")
    print("2. 检查门户是否正确保存了id_token")
    print("3. 在Casdoor管理界面中配置正确的重定向URI")
    print("4. 确保所有应用使用相同的client_id")

if __name__ == "__main__":
    main()
