#!/usr/bin/env python3
"""
MySQL 数据库设置脚本
创建数据库和表结构
"""
import pymysql
import os
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
        'table_token_blacklist': os.getenv('MYSQL_TABLE_TOKEN_BLACKLIST', 'token_blacklist')
    }

def create_database(config):
    """创建数据库（如果不存在）"""
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
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']} CHARACTER SET {config['charset']} COLLATE utf8mb4_0900_ai_ci")
            print(f"数据库 {config['database']} 已确保存在")

        conn.commit()
        return True

    except Exception as e:
        print(f"创建数据库失败：{e}")
        return False
    finally:
        if conn:
            conn.close()

def create_tables(config):
    """创建所有表（如果不存在）"""
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
                    tags VARCHAR(1000) COMMENT 'JSON 格式存储的标签数组',
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

            # 5. 创建 token_blacklist 表（JWT 令牌黑名单）
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

        conn.commit()
        return True

    except Exception as e:
        print(f"[ERROR] 创建表失败：{e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """主函数"""
    print("开始设置 MySQL 数据库...")

    config = get_mysql_config()
    print(f"配置信息:")
    print(f"  主机：{config['host']}:{config['port']}")
    print(f"  用户：{config['user']}")
    print(f"  数据库：{config['database']}")
    print(f"  字符集：{config['charset']}")

    # 创建数据库
    if not create_database(config):
        print("数据库创建失败，请检查 MySQL 服务是否运行")
        return

    # 创建表
    if not create_tables(config):
        print("表创建失败")
        return

    print("\nMySQL 数据库设置完成！")
    print("将创建的表:")
    print(f"  - {config['table_users']} (用户基础信息表)")
    print(f"  - {config['table_assets']} (资产表)")
    print(f"  - {config['table_works']} (作品表)")
    print(f"  - {config['table_chapters']} (章节表)")
    print(f"  - {config['table_token_blacklist']} (JWT 令牌黑名单表)")

if __name__ == "__main__":
    main()
