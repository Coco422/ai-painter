#!/usr/bin/env python3
"""
重建数据库脚本
删除现有数据库文件并重新初始化
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def rebuild_database():
    """重建数据库"""
    # 删除现有数据库文件
    db_files = [
        "aipainter.db",
        "aipainter.db-journal",
        "aipainter.db-wal",
        "aipainter.db-shm"
    ]
    
    print("🗑️  删除现有数据库文件...")
    for db_file in db_files:
        if os.path.exists(db_file):
            os.remove(db_file)
            print(f"   已删除: {db_file}")
    
    print("\n🔄 重新初始化数据库...")
    
    # 重新初始化数据库
    from backend.init_db import init_database, create_admin_user, create_sample_data
    
    init_database()
    create_admin_user()
    create_sample_data()
    
    print("\n✅ 数据库重建完成！")
    print("\n📋 默认管理员账户:")
    print("   用户名: admin")
    print("   密码: admin123")
    print("   积分: 1000")

if __name__ == "__main__":
    print("🚀 开始重建数据库...")
    print("⚠️  这将删除所有现有数据！")
    
    confirm = input("确认继续? (y/N): ")
    if confirm.lower() in ['y', 'yes']:
        rebuild_database()
    else:
        print("❌ 操作已取消")
