#!/usr/bin/env python3
"""
MySQL数据库设置脚本
创建数据库和表结构
"""
import pymysql
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_mysql_config():
    """从环境变量获取MySQL配置"""
    return {
        'host': os.getenv('MYSQL_HOST', 'localhost'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'root'),
        'password': os.getenv('MYSQL_PASSWORD', ''),
        'database': os.getenv('MYSQL_DB', 'narloom'),
        'charset': os.getenv('MYSQL_CHARSET', 'utf8mb4'),
        'table_users': os.getenv('MYSQL_TABLE_USERS', 'users'),
        'table_assets': os.getenv('MYSQL_TABLE_ASSETS', 'assets'),
        'table_works': os.getenv('MYSQL_TABLE_WORKS', 'works'),
        'table_chapters': os.getenv('MYSQL_TABLE_CHAPTERS', 'chapters')
    }

def create_database(config):
    """创建数据库（如果不存在）"""
    conn = None
    try:
        # 连接到MySQL服务器（不指定数据库）
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            charset=config['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']} CHARACTER SET {config['charset']} COLLATE utf8mb4_unicode_ci")
            print(f"数据库 {config['database']} 已确保存在")

        conn.commit()
        return True

    except Exception as e:
        print(f"创建数据库失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """主函数"""
    print("开始设置MySQL数据库...")

    config = get_mysql_config()
    print(f"配置信息:")
    print(f"  主机: {config['host']}:{config['port']}")
    print(f"  用户: {config['user']}")
    print(f"  数据库: {config['database']}")
    print(f"  字符集: {config['charset']}")

    # 创建数据库
    if not create_database(config):
        print("数据库创建失败，请检查MySQL服务是否运行")
        return

    print("MySQL数据库设置完成！")
    print("注意：表结构将在应用启动时自动创建")
    print("将创建的表:")
    print(f"  - {config['table_users']} (用户表)")
    print(f"  - {config['table_assets']} (资产表)")
    print(f"  - {config['table_works']} (作品表)")
    print(f"  - {config['table_chapters']} (章节表)")

if __name__ == "__main__":
    main()