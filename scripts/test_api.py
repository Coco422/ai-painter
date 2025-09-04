#!/usr/bin/env python3
"""
API测试脚本
用于测试AI Painter系统的基本功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
TEST_USERNAME = None

def test_health():
    """测试健康检查接口"""
    print("🔍 测试健康检查接口...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {str(e)}")
        return False

def test_register():
    """测试用户注册"""
    print("\n📝 测试用户注册...")

    # 使用生成的邀请码进行注册
    global TEST_USERNAME
    import time
    timestamp = str(int(time.time()))[-4:]  # 获取时间戳后4位
    TEST_USERNAME = f"testuser{timestamp}"
    register_data = {
        "username": TEST_USERNAME,
        "password": "testpass123",
        "invite_code": "KFJBZ756"  # 使用生成的邀请码
    }

    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=register_data,
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            print("✅ 用户注册成功")
            return True
        else:
            print(f"❌ 注册失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 注册请求失败: {str(e)}")
        return False

def test_login():
    """测试用户登录"""
    print("\n🔐 测试用户登录...")

    global TEST_USERNAME
    if not TEST_USERNAME:
        print("❌ 未找到注册的用户名")
        return None

    login_data = {
        "username": TEST_USERNAME,
        "password": "testpass123"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print("✅ 用户登录成功")
            return token
        else:
            print(f"❌ 登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 登录请求失败: {str(e)}")
        return None

def test_user_info(token):
    """测试获取用户信息"""
    print("\n👤 测试获取用户信息...")

    try:
        response = requests.get(
            f"{BASE_URL}/users/me/info",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ 获取用户信息成功")
            print(f"   用户名: {data['user']['username']}")
            print(f"   积分: {data['user']['points']}")
            print(f"   邀请码: {data['user']['invite_code']}")
            return True
        else:
            print(f"❌ 获取用户信息失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 获取用户信息请求失败: {str(e)}")
        return False

def test_generate_invite_code(token):
    """测试生成邀请码"""
    print("\n🎫 测试生成邀请码...")

    try:
        response = requests.post(
            f"{BASE_URL}/users/invite-codes",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ 生成邀请码成功")
            print(f"   邀请码: {data['code']}")
            return data['code']
        else:
            print(f"❌ 生成邀请码失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 生成邀请码请求失败: {str(e)}")
        return None

def test_admin_login():
    """测试管理员登录"""
    print("\n👑 测试管理员登录...")

    login_data = {
        "username": "admin",
        "password": "admin123"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print("✅ 管理员登录成功")
            return token
        else:
            print(f"❌ 管理员登录失败: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ 管理员登录请求失败: {str(e)}")
        return None

def test_admin_invite_codes(admin_token):
    """测试管理员获取邀请码列表"""
    print("\n📋 测试管理员获取邀请码列表...")

    try:
        response = requests.get(
            f"{BASE_URL}/users/admin/invite-codes",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            }
        )

        if response.status_code == 200:
            data = response.json()
            print("✅ 获取邀请码列表成功")
            print(f"   邀请码数量: {len(data)}")
            return True
        else:
            print(f"❌ 获取邀请码列表失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 获取邀请码列表请求失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试 AI Painter API...")
    print("=" * 50)

    # 测试健康检查
    if not test_health():
        print("❌ 服务器未启动或健康检查失败")
        return

    # 测试用户注册
    if not test_register():
        print("❌ 用户注册测试失败")
        return

    # 测试用户登录
    user_token = test_login()
    if not user_token:
        print("❌ 用户登录测试失败")
        return

    # 测试获取用户信息
    if not test_user_info(user_token):
        print("❌ 获取用户信息测试失败")
        return

    # 测试生成邀请码
    if not test_generate_invite_code(user_token):
        print("❌ 生成邀请码测试失败")
        return

    # 测试管理员登录
    admin_token = test_admin_login()
    if admin_token:
        # 测试管理员功能
        test_admin_invite_codes(admin_token)
    else:
        print("⚠️ 管理员登录失败，跳过管理员功能测试")

    print("\n" + "=" * 50)
    print("🎉 API测试完成！")
    print("\n📖 访问以下地址进行更多测试:")
    print(f"   API文档: {BASE_URL}/docs")
    print(f"   前端界面: {BASE_URL}/")
    print(f"   管理员面板: {BASE_URL}/admin")

if __name__ == "__main__":
    main()
