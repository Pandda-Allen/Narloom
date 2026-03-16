#!/usr/bin/env python3
"""
综合数据库部署脚本
在未部署数据库的电脑上运行此脚本，可以创建项目所需的所有数据库和表
包括MySQL数据库、表和MongoDB数据库、集合、索引
"""

import os
import sys
import pymysql
import pymysql.cursors
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
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

def get_mongo_config():
    """从环境变量获取MongoDB配置"""
    return {
        'uri': os.getenv('MONGO_URI', 'mongodb://localhost:27017/'),
        'database': os.getenv('MONGO_DB', 'narloom'),
        'asset_collection': os.getenv('MONGO_ASSET_DATA_COLLECTION', 'asset_data'),
        'work_collection': os.getenv('MONGO_WORK_DETAILS_COLLECTION', 'work_details')
    }

def create_mysql_database(config):
    """创建MySQL数据库（如果不存在）"""
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
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']} "
                          f"CHARACTER SET {config['charset']} COLLATE utf8mb4_unicode_ci")
            print(f"[OK] 数据库 {config['database']} 已确保存在")

        conn.commit()
        return True

    except Exception as e:
        print(f"[ERROR] 创建数据库失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

def create_mysql_tables(config):
    """创建所有MySQL表（如果不存在）"""
    conn = None
    try:
        # 连接到指定数据库
        conn = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset=config['charset'],
            cursorclass=pymysql.cursors.DictCursor
        )

        with conn.cursor() as cursor:
            # 1. 创建users表
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {config['table_users']} (
                    user_id VARCHAR(100) PRIMARY KEY,
                    email VARCHAR(255) UNIQUE,
                    password_hash VARCHAR(255),
                    name VARCHAR(255) DEFAULT '',
                    bio TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    INDEX idx_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print(f"[OK] 表 {config['table_users']} 已确保存在")

            # 2. 创建assets表
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {config['table_assets']} (
                    asset_id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    work_id CHAR(36),
                    asset_type VARCHAR(36) NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print(f"[OK] 表 {config['table_assets']} 已确保存在")

            # 3. 创建works表
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {config['table_works']} (
                    work_id CHAR(36) PRIMARY KEY,
                    author_id CHAR(36) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    genre VARCHAR(100) DEFAULT '',
                    status VARCHAR(50) DEFAULT 'draft',
                    word_count INT DEFAULT 0,
                    description TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print(f"[OK] 表 {config['table_works']} 已确保存在")

            # 4. 创建chapters表
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {config['table_chapters']} (
                    chapter_id CHAR(36) PRIMARY KEY,
                    work_id CHAR(36) NOT NULL,
                    author_id CHAR(36) NOT NULL,
                    chapter_num INT NOT NULL,
                    chapter_title VARCHAR(255) NOT NULL,
                    content LONGTEXT,
                    status VARCHAR(50) DEFAULT 'draft',
                    word_count INT DEFAULT 0,
                    notes TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    INDEX idx_work_id (work_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print(f"[OK] 表 {config['table_chapters']} 已确保存在")

        conn.commit()
        return True

    except Exception as e:
        print(f"[ERROR] 创建表失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

def setup_mongo_database(config):
    """设置MongoDB数据库、集合和索引"""
    client = None
    try:
        # 连接到MongoDB
        client = MongoClient(config['uri'])

        # 测试连接
        client.admin.command('ping')
        print(f"[OK] 成功连接到MongoDB: {config['uri']}")

        # 获取数据库
        db = client[config['database']]
        print(f"[OK] 使用数据库: {config['database']}")

        # 创建或获取集合
        asset_collection = db[config['asset_collection']]
        work_collection = db[config['work_collection']]

        print(f"[OK] 集合准备完成:")
        print(f"  - {config['asset_collection']} (资产数据)")
        print(f"  - {config['work_collection']} (作品详情)")

        # 创建索引
        try:
            # asset_data 集合索引
            asset_collection.create_index('asset_id', unique=True, name='asset_id_unique')
            print(f"[OK] 已创建索引: {config['asset_collection']}.asset_id (唯一)")

            # work_details 集合索引
            work_collection.create_index('work_id', unique=True, name='work_id_unique')
            print(f"[OK] 已创建索引: {config['work_collection']}.work_id (唯一)")

        except PyMongoError as e:
            if 'already exists' in str(e):
                print(f"[OK] 索引已存在")
            else:
                raise

        # 显示集合统计信息
        asset_count = asset_collection.count_documents({})
        work_count = work_collection.count_documents({})

        print(f"[STATS] 当前数据统计:")
        print(f"  - {config['asset_collection']}: {asset_count} 个文档")
        print(f"  - {config['work_collection']}: {work_count} 个文档")

        return True

    except ConnectionFailure as e:
        print(f"[ERROR] 连接MongoDB失败: {e}")
        print("请确保MongoDB服务正在运行")
        return False
    except PyMongoError as e:
        print(f"[ERROR] MongoDB操作错误: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 未知错误: {e}")
        return False
    finally:
        if client:
            client.close()

def main():
    """主函数"""
    print("=" * 60)
    print("开始部署项目所需的所有数据库...")
    print("=" * 60)

    # MySQL配置
    mysql_config = get_mysql_config()
    print("\n[CONFIG] MySQL配置信息:")
    print(f"  主机: {mysql_config['host']}:{mysql_config['port']}")
    print(f"  用户: {mysql_config['user']}")
    print(f"  数据库: {mysql_config['database']}")
    print(f"  字符集: {mysql_config['charset']}")
    print(f"  表: {mysql_config['table_users']}, {mysql_config['table_assets']}, "
          f"{mysql_config['table_works']}, {mysql_config['table_chapters']}")

    # MongoDB配置
    mongo_config = get_mongo_config()
    print("\n[CONFIG] MongoDB配置信息:")
    print(f"  连接URI: {mongo_config['uri']}")
    print(f"  数据库: {mongo_config['database']}")
    print(f"  资产集合: {mongo_config['asset_collection']}")
    print(f"  作品集合: {mongo_config['work_collection']}")

    print("\n" + "=" * 60)
    print("开始设置MySQL数据库...")
    print("-" * 60)

    # 创建MySQL数据库
    if not create_mysql_database(mysql_config):
        print("[ERROR] MySQL数据库创建失败，请检查MySQL服务是否运行")
        sys.exit(1)

    # 创建MySQL表
    if not create_mysql_tables(mysql_config):
        print("[ERROR] MySQL表创建失败")
        sys.exit(1)

    print("\n[OK] MySQL数据库和表设置完成！")

    print("\n" + "=" * 60)
    print("开始设置MongoDB数据库...")
    print("-" * 60)

    # 设置MongoDB
    if not setup_mongo_database(mongo_config):
        print("[ERROR] MongoDB数据库设置失败")
        sys.exit(1)

    print("\n[OK] MongoDB数据库设置完成！")

    print("\n" + "=" * 60)
    print("[SUCCESS] 所有数据库部署完成！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 确保 Flask 应用配置正确 (.env 文件)")
    print("2. 运行应用: python app.py 或 flask run")
    print("3. 应用启动时会自动初始化数据库连接")
    print("\n注意:")
    print("- MySQL 表结构已创建，可以直接使用")
    print("- MongoDB 集合和索引已确保存在")
    print("- 如果遇到问题，请检查数据库服务是否正常运行")

if __name__ == "__main__":
    main()