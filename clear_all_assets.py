"""
清空数据库中所有 asset 记录以及 OSS 上的图片
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    Config.init_app(app)
    return app

def clear_all_assets():
    """清空所有 asset 数据和 OSS 图片"""
    from services import mysql_service, MongoService, mysql_base_service
    from services.storage import oss_service

    print("开始清空所有资产数据...")

    # 1. 从 MySQL 获取所有 asset 记录
    # 使用原生 SQL 获取所有 asset
    conn = mysql_base_service._ensure_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT asset_id, user_id, asset_type, work_id FROM assets")
        all_assets = cursor.fetchall()

    print(f"共找到 {len(all_assets)} 条 asset 记录")

    # 2. 遍历删除
    deleted_count = 0
    oss_deleted_count = 0
    mongo_deleted_count = 0

    for asset in all_assets:
        asset_id = asset['asset_id']
        asset_type = asset['asset_type']

        # 删除 OSS 上的图片（仅 comic 类型）
        if asset_type == 'comic':
            # 从 MongoDB 获取 oss_object_key
            asset_data = MongoService().fetch_asset_data(asset_id)
            if asset_data and asset_data.get('oss_object_key'):
                oss_object_key = asset_data['oss_object_key']
                try:
                    delete_result = oss_service.delete_picture(oss_object_key)
                    if delete_result.get('success'):
                        oss_deleted_count += 1
                        print(f"  已删除 OSS 图片：{oss_object_key}")
                    else:
                        print(f"  OSS 删除失败：{oss_object_key} - {delete_result.get('error')}")
                except Exception as e:
                    print(f"  OSS 删除异常：{oss_object_key} - {str(e)}")

            # 删除 MongoDB 中的 asset_data
            try:
                MongoService().delete_asset_data(asset_id)
                mongo_deleted_count += 1
            except Exception as e:
                print(f"  MongoDB 删除异常：{asset_id} - {str(e)}")

        # 删除 MySQL 中的 asset 记录
        try:
            mysql_service.delete_asset(asset_id)
            deleted_count += 1
            print(f"  已删除 asset: {asset_id}")
        except Exception as e:
            print(f"  MySQL 删除异常：{asset_id} - {str(e)}")

    print(f"\n清空完成!")
    print(f"  - MySQL 删除 asset 记录：{deleted_count} 条")
    print(f"  - OSS 删除图片：{oss_deleted_count} 张")
    print(f"  - MongoDB 删除 asset_data: {mongo_deleted_count} 条")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        print("Starting to clear all assets...")
        clear_all_assets()
