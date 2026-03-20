#!/usr/bin/env python3
"""
MongoDB 数据库设置脚本
创建数据库、集合和索引（包括复合索引）
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_mongo_config():
    """从环境变量获取 MongoDB 配置"""
    return {
        'uri': os.getenv('MONGO_URI', 'mongodb://localhost:27017/'),
        'database': os.getenv('MONGO_DB', 'narloom'),
        'asset_collection': os.getenv('MONGO_ASSET_DATA_COLLECTION', 'asset_data'),
        'work_collection': os.getenv('MONGO_WORK_DETAILS_COLLECTION', 'work_details')
    }

def setup_mongo_database(config):
    """设置 MongoDB 数据库、集合和索引"""
    client = None
    try:
        # 连接到 MongoDB
        client = MongoClient(config['uri'])

        # 测试连接
        client.admin.command('ping')
        print(f"成功连接到 MongoDB: {config['uri']}")

        # 获取数据库
        db = client[config['database']]
        print(f"使用数据库：{config['database']}")

        # 创建或获取集合
        asset_collection = db[config['asset_collection']]
        work_collection = db[config['work_collection']]

        print(f"集合准备完成:")
        print(f"  - {config['asset_collection']} (资产数据)")
        print(f"  - {config['work_collection']} (作品详情)")

        # 创建索引
        try:
            # asset_data 集合索引
            asset_collection.create_index('asset_id', unique=True, name='asset_id_unique')
            print(f"已创建索引：{config['asset_collection']}.asset_id (唯一)")

            # work_details 集合索引
            work_collection.create_index('work_id', unique=True, name='work_id_unique')
            print(f"已创建索引：{config['work_collection']}.work_id (唯一)")

            # work_details 复合索引
            work_collection.create_index([('work_id', 1), ('asset_ids', 1)], name='work_id_asset_ids_idx')
            print(f"已创建索引：{config['work_collection']}.work_id + asset_ids (复合)")

            work_collection.create_index([('work_id', 1), ('chapter_ids', 1)], name='work_id_chapter_ids_idx')
            print(f"已创建索引：{config['work_collection']}.work_id + chapter_ids (复合)")

        except PyMongoError as e:
            if 'already exists' in str(e):
                print(f"索引已存在")
            else:
                raise

        # 显示集合统计信息
        asset_count = asset_collection.count_documents({})
        work_count = work_collection.count_documents({})

        print(f"当前数据统计:")
        print(f"  - {config['asset_collection']}: {asset_count} 个文档")
        print(f"  - {config['work_collection']}: {work_count} 个文档")

        return True

    except ConnectionFailure as e:
        print(f"连接 MongoDB 失败：{e}")
        print("请确保 MongoDB 服务正在运行")
        return False
    except PyMongoError as e:
        print(f"MongoDB 操作错误：{e}")
        return False
    except Exception as e:
        print(f"未知错误：{e}")
        return False
    finally:
        if client:
            client.close()

def main():
    """主函数"""
    print("开始设置 MongoDB 数据库...")

    config = get_mongo_config()
    print(f"配置信息:")
    print(f"  连接 URI: {config['uri']}")
    print(f"  数据库：{config['database']}")
    print(f"  资产集合：{config['asset_collection']}")
    print(f"  作品集合：{config['work_collection']}")

    # 设置数据库
    if not setup_mongo_database(config):
        print("MongoDB 数据库设置失败")
        return

    print("MongoDB 数据库设置完成！")
    print("注意：MongoDB 数据库和集合会在首次插入数据时自动创建")
    print("索引已确保存在，保证数据完整性")
    print("创建的索引:")
    print(f"  - {config['asset_collection']}.asset_id (唯一索引)")
    print(f"  - {config['work_collection']}.work_id (唯一索引)")
    print(f"  - {config['work_collection']}.work_id + asset_ids (复合索引)")
    print(f"  - {config['work_collection']}.work_id + chapter_ids (复合索引)")

if __name__ == "__main__":
    main()
