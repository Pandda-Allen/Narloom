#!/usr/bin/env python3
"""
综合数据库部署脚本
在未部署数据库的电脑上运行此脚本，可以创建项目所需的所有数据库和表
包括 MySQL 数据库、表和 MongoDB 数据库、集合、索引
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
    """从环境变量获取 MySQL 配置"""
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
        'table_chapters': os.getenv('MYSQL_TABLE_CHAPTERS', 'chapters'),
        'table_user_oauth_accounts': os.getenv('MYSQL_TABLE_USER_OAUTH_ACCOUNTS', 'user_oauth_accounts'),
        'table_token_blacklist': os.getenv('MYSQL_TABLE_TOKEN_BLACKLIST', 'token_blacklist'),
        'table_oauth_states': os.getenv('MYSQL_TABLE_OAUTH_STATES', 'oauth_states')
    }

def get_mongo_config():
    """从环境变量获取 MongoDB 配置"""
    return {
        'uri': os.getenv('MONGO_URI', 'mongodb://localhost:27017/'),
        'database': os.getenv('MONGO_DB', 'narloom'),
        'asset_collection': os.getenv('MONGO_ASSET_DATA_COLLECTION', 'asset_data'),
        'work_collection': os.getenv('MONGO_WORK_DETAILS_COLLECTION', 'work_details')
    }

def create_mysql_database(config):
    """创建 MySQL 数据库（如果不存在）"""
    conn = None
    try:
        # 连接到 MySQL 服务器（不指定数据库）
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
                          f"CHARACTER SET {config['charset']} COLLATE utf8mb4_0900_ai_ci")
            print(f"[OK] 数据库 {config['database']} 已确保存在")

        conn.commit()
        return True

    except Exception as e:
        print(f"[ERROR] 创建数据库失败：{e}")
        return False
    finally:
        if conn:
            conn.close()

def create_mysql_tables(config):
    """创建所有 MySQL 表（如果不存在）"""
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
            # 1. 创建 users 表
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {config['table_users']} (
                    user_id VARCHAR(100) PRIMARY KEY,
                    email VARCHAR(255) UNIQUE,
                    password_hash VARCHAR(255),
                    name VARCHAR(255) DEFAULT '',
                    bio TEXT,
                    phone VARCHAR(20),
                    avatar_url VARCHAR(500),
                    last_login_at DATETIME,
                    last_login_provider VARCHAR(20) DEFAULT 'email',
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    INDEX idx_email (email)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
            print(f"[OK] 表 {config['table_users']} 已确保存在")

            # 2. 创建 assets 表
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {config['table_assets']} (
                    asset_id CHAR(36) PRIMARY KEY,
                    user_id CHAR(36) NOT NULL,
                    work_id CHAR(36),
                    asset_type VARCHAR(36) NOT NULL,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    INDEX idx_user_id (user_id),
                    INDEX idx_work_id (work_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
            print(f"[OK] 表 {config['table_assets']} 已确保存在")

            # 3. 创建 works 表
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {config['table_works']} (
                    work_id CHAR(36) PRIMARY KEY,
                    author_id CHAR(36) NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    genre VARCHAR(100) DEFAULT '',
                    tags VARCHAR(500),
                    status VARCHAR(50) DEFAULT 'draft',
                    chapter_count INT DEFAULT 0,
                    word_count INT DEFAULT 0,
                    description TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    INDEX idx_author_id (author_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
            print(f"[OK] 表 {config['table_works']} 已确保存在")

            # 4. 创建 chapters 表
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {config['table_chapters']} (
                    chapter_id CHAR(36) PRIMARY KEY,
                    work_id CHAR(36) NOT NULL,
                    author_id CHAR(36) NOT NULL,
                    chapter_number INT NOT NULL,
                    chapter_title VARCHAR(255) NOT NULL,
                    content LONGTEXT,
                    status VARCHAR(50) DEFAULT 'draft',
                    word_count INT DEFAULT 0,
                    description TEXT,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL,
                    INDEX idx_work_id (work_id),
                    INDEX idx_chapter_number (work_id, chapter_number)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
            """)
            print(f"[OK] 表 {config['table_chapters']} 已确保存在")

            # 5. 创建 user_oauth_accounts 表（OAuth 账号绑定）
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {config['table_user_oauth_accounts']} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id VARCHAR(100) NOT NULL,
                    provider VARCHAR(20) NOT NULL COMMENT 'OAuth 提供商 (wechat/qq)',
                    open_id VARCHAR(100) NOT NULL COMMENT 'OAuth open_id',
                    union_id VARCHAR(100) COMMENT 'OAuth union_id',
                    access_token TEXT COMMENT 'OAuth access_token (可选)',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_user_provider (user_id, provider),
                    UNIQUE KEY unique_provider_openid (provider, open_id),
                    INDEX idx_user_id (user_id),
                    CONSTRAINT fk_user_oauth FOREIGN KEY (user_id) REFERENCES {config['table_users']}(user_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                COMMENT='用户 OAuth 账号绑定表'
            """)
            print(f"[OK] 表 {config['table_user_oauth_accounts']} 已确保存在")

            # 6. 创建 token_blacklist 表（JWT 令牌黑名单）
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {config['table_token_blacklist']} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    jti VARCHAR(100) NOT NULL UNIQUE COMMENT 'JWT ID',
                    user_id VARCHAR(100) COMMENT '用户 ID',
                    token_type VARCHAR(20) NOT NULL DEFAULT 'access' COMMENT '令牌类型',
                    blacklisted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL COMMENT '令牌原始过期时间',
                    reason VARCHAR(50) DEFAULT 'logout' COMMENT '加入黑名单原因',
                    INDEX idx_jti (jti),
                    INDEX idx_user_id (user_id),
                    INDEX idx_expires_at (expires_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                COMMENT='JWT 令牌黑名单表'
            """)
            print(f"[OK] 表 {config['table_token_blacklist']} 已确保存在")

            # 7. 创建 oauth_states 表（OAuth state 参数存储，CSRF 防护）
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {config['table_oauth_states']} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    state VARCHAR(100) NOT NULL UNIQUE COMMENT 'OAuth state 参数',
                    provider VARCHAR(20) NOT NULL COMMENT 'OAuth 提供商',
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    expires_at DATETIME NOT NULL COMMENT '过期时间',
                    INDEX idx_state (state),
                    INDEX idx_expires_at (expires_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci
                COMMENT='OAuth state 参数存储表'
            """)
            print(f"[OK] 表 {config['table_oauth_states']} 已确保存在")

        conn.commit()
        return True

    except Exception as e:
        print(f"[ERROR] 创建表失败：{e}")
        return False
    finally:
        if conn:
            conn.close()

def setup_mongo_database(config):
    """设置 MongoDB 数据库、集合和索引"""
    client = None
    try:
        # 连接到 MongoDB
        client = MongoClient(config['uri'])

        # 测试连接
        client.admin.command('ping')
        print(f"[OK] 成功连接到 MongoDB: {config['uri']}")

        # 获取数据库
        db = client[config['database']]
        print(f"[OK] 使用数据库：{config['database']}")

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
            print(f"[OK] 已创建索引：{config['asset_collection']}.asset_id (唯一)")

            # work_details 集合索引
            work_collection.create_index('work_id', unique=True, name='work_id_unique')
            print(f"[OK] 已创建索引：{config['work_collection']}.work_id (唯一)")

            # work_details 复合索引
            work_collection.create_index([('work_id', 1), ('asset_ids', 1)], name='work_id_asset_ids_idx')
            print(f"[OK] 已创建索引：{config['work_collection']}.work_id + asset_ids (复合)")

            work_collection.create_index([('work_id', 1), ('chapter_ids', 1)], name='work_id_chapter_ids_idx')
            print(f"[OK] 已创建索引：{config['work_collection']}.work_id + chapter_ids (复合)")

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
        print(f"[ERROR] 连接 MongoDB 失败：{e}")
        print("请确保 MongoDB 服务正在运行")
        return False
    except PyMongoError as e:
        print(f"[ERROR] MongoDB 操作错误：{e}")
        return False
    except Exception as e:
        print(f"[ERROR] 未知错误：{e}")
        return False
    finally:
        if client:
            client.close()

def main():
    """主函数"""
    print("=" * 60)
    print("开始部署项目所需的所有数据库...")
    print("=" * 60)

    # MySQL 配置
    mysql_config = get_mysql_config()
    print("\n[CONFIG] MySQL 配置信息:")
    print(f"  主机：{mysql_config['host']}:{mysql_config['port']}")
    print(f"  用户：{mysql_config['user']}")
    print(f"  数据库：{mysql_config['database']}")
    print(f"  字符集：{mysql_config['charset']}")
    print(f"  表：{mysql_config['table_users']}, {mysql_config['table_assets']}, "
          f"{mysql_config['table_works']}, {mysql_config['table_chapters']}, "
          f"{mysql_config['table_user_oauth_accounts']}, {mysql_config['table_token_blacklist']}, "
          f"{mysql_config['table_oauth_states']}")

    # MongoDB 配置
    mongo_config = get_mongo_config()
    print("\n[CONFIG] MongoDB 配置信息:")
    print(f"  连接 URI: {mongo_config['uri']}")
    print(f"  数据库：{mongo_config['database']}")
    print(f"  资产集合：{mongo_config['asset_collection']}")
    print(f"  作品集合：{mongo_config['work_collection']}")

    print("\n" + "=" * 60)
    print("开始设置 MySQL 数据库...")
    print("-" * 60)

    # 创建 MySQL 数据库
    if not create_mysql_database(mysql_config):
        print("[ERROR] MySQL 数据库创建失败，请检查 MySQL 服务是否运行")
        sys.exit(1)

    # 创建 MySQL 表
    if not create_mysql_tables(mysql_config):
        print("[ERROR] MySQL 表创建失败")
        sys.exit(1)

    print("\n[OK] MySQL 数据库和表设置完成！")

    print("\n" + "=" * 60)
    print("开始设置 MongoDB 数据库...")
    print("-" * 60)

    # 设置 MongoDB
    if not setup_mongo_database(mongo_config):
        print("[ERROR] MongoDB 数据库设置失败")
        sys.exit(1)

    print("\n[OK] MongoDB 数据库设置完成！")

    print("\n" + "=" * 60)
    print("[SUCCESS] 所有数据库部署完成！")
    print("=" * 60)
    print("\n下一步:")
    print("1. 确保 Flask 应用配置正确 (.env 文件)")
    print("2. 运行应用：python app.py 或 flask run")
    print("3. 应用启动时会自动初始化数据库连接")
    print("\n注意:")
    print("- MySQL 表结构已创建，可以直接使用")
    print("- MongoDB 集合和索引已确保存在")
    print("- 如果遇到问题，请检查数据库服务是否正常运行")

if __name__ == "__main__":
    main()
