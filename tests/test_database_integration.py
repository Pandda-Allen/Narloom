"""
数据库集成测试：验证 MySQL 和 MongoDB 服务的交互。
注意：这些测试会操作真实数据库，请确保在测试环境中运行。
"""
import sys
import os
import uuid
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from services.mysql_service import mysql_service
from services.mongo_service import mongo_service

def setup_module():
    """模块级别的初始化：创建 Flask 应用并初始化服务"""
    global app
    app = create_app()
    # 初始化服务
    with app.app_context():
        mysql_service.init_app(app)
        mongo_service.init_app(app)

def test_mysql_asset_crud():
    """测试 MySQL 资产 CRUD 操作"""
    with app.app_context():
        # 确保服务已初始化
        assert mysql_service._initialized

        # 插入资产
        user_id = str(uuid.uuid4())
        asset_type = 'test_asset'
        asset = mysql_service.insert_asset(user_id=user_id, asset_type=asset_type)
        assert 'asset_id' in asset
        asset_id = asset['asset_id']
        print(f'Created asset: {asset_id}')

        # 查询资产
        fetched = mysql_service.fetch_asset_by_id(asset_id)
        assert fetched is not None
        assert fetched['asset_id'] == asset_id
        assert fetched['user_id'] == user_id
        assert fetched['asset_type'] == asset_type

        # 更新资产
        update_data = {'asset_type': 'updated_asset'}
        updated = mysql_service.update_asset(asset_id, update_data)
        assert updated is not None
        assert updated['asset_type'] == 'updated_asset'

        # 删除资产
        deleted = mysql_service.delete_asset(asset_id)
        assert deleted is True

        # 验证删除
        fetched_after = mysql_service.fetch_asset_by_id(asset_id)
        assert fetched_after is None

        print('MySQL asset CRUD test passed')

def test_mongo_asset_data_crud():
    """测试 MongoDB asset_data CRUD 操作"""
    with app.app_context():
        assert mongo_service._initialized

        asset_id = str(uuid.uuid4())
        asset_data = {'title': 'Test Asset', 'content': 'This is a test'}

        # 插入 asset_data
        mongo_service.insert_asset_data(asset_id, asset_data)

        # 查询 asset_data
        fetched = mongo_service.fetch_asset_data(asset_id)
        assert fetched is not None
        assert fetched['title'] == 'Test Asset'
        assert fetched['content'] == 'This is a test'

        # 更新 asset_data
        new_data = {'title': 'Updated Asset', 'content': 'Updated content'}
        updated = mongo_service.update_asset_data(asset_id, new_data)
        assert updated is True

        # 验证更新
        fetched_updated = mongo_service.fetch_asset_data(asset_id)
        assert fetched_updated['title'] == 'Updated Asset'

        # 删除 asset_data
        deleted = mongo_service.delete_asset_data(asset_id)
        assert deleted is True

        # 验证删除
        fetched_after = mongo_service.fetch_asset_data(asset_id)
        assert fetched_after is None

        print('MongoDB asset_data CRUD test passed')

def test_mysql_work_crud_with_tags():
    """测试 MySQL 作品 CRUD 操作（包括 tags 字段）"""
    with app.app_context():
        author_id = str(uuid.uuid4())
        title = 'Test Work'
        tags = ['玄幻', '冒险', '热血']

        # 插入作品（带 tags）
        work = mysql_service.insert_work(author_id=author_id, title=title, tags=tags)
        assert 'work_id' in work
        work_id = work['work_id']

        # 查询作品（验证 tags 被正确解析为列表）
        fetched = mysql_service.fetch_work_by_id(work_id)
        assert fetched is not None
        assert fetched['title'] == title
        assert fetched['author_id'] == author_id
        # 验证 tags 字段被正确解析为 Python 列表
        assert isinstance(fetched['tags'], list)
        assert fetched['tags'] == tags

        # 更新作品（包括 tags 字段）
        new_tags = ['完结', '精品']
        update_data = {'title': 'Updated Work', 'status': 'published', 'tags': new_tags}
        updated = mysql_service.update_work(work_id, update_data)
        assert updated is not None
        assert updated['title'] == 'Updated Work'
        assert updated['status'] == 'published'
        # 验证 tags 被正确更新
        assert isinstance(updated['tags'], list)
        assert updated['tags'] == new_tags

        # 删除作品
        deleted = mysql_service.delete_work(work_id)
        assert deleted is True

        # 验证删除
        fetched_after = mysql_service.fetch_work_by_id(work_id)
        assert fetched_after is None

        print('MySQL work CRUD with tags test passed')

def test_mysql_work_tags_storage():
    """测试 tags 字段的存储和读取"""
    with app.app_context():
        author_id = str(uuid.uuid4())
        title = 'Tags Test Work'

        # 测试 1: 传入列表类型的 tags
        tags_list = ['标签 1', '标签 2', '标签 3']
        work1 = mysql_service.insert_work(author_id=author_id, title=title, tags=tags_list)
        work_id1 = work1['work_id']

        # 验证读取时 tags 是列表
        fetched1 = mysql_service.fetch_work_by_id(work_id1)
        assert isinstance(fetched1['tags'], list)
        assert fetched1['tags'] == tags_list

        # 测试 2: 传入空列表
        work2 = mysql_service.insert_work(author_id=author_id, title=title + ' 2', tags=[])
        work_id2 = work2['work_id']
        fetched2 = mysql_service.fetch_work_by_id(work_id2)
        assert fetched2['tags'] == [] or fetched2['tags'] == '[]'

        # 测试 3: 传入 None
        work3 = mysql_service.insert_work(author_id=author_id, title=title + ' 3', tags=None)
        work_id3 = work3['work_id']
        fetched3 = mysql_service.fetch_work_by_id(work_id3)
        assert fetched3['tags'] is None or fetched3['tags'] == ''

        # 测试 4: 更新 tags 字段
        mysql_service.update_work(work_id1, {'tags': ['新标签 1', '新标签 2']})
        updated = mysql_service.fetch_work_by_id(work_id1)
        assert isinstance(updated['tags'], list)
        assert updated['tags'] == ['新标签 1', '新标签 2']

        # 清理
        mysql_service.delete_work(work_id1)
        mysql_service.delete_work(work_id2)
        mysql_service.delete_work(work_id3)

        print('MySQL work tags storage test passed')

def test_mysql_chapter_crud():
    """测试 MySQL 章节 CRUD 操作"""
    with app.app_context():
        # 首先创建作品
        author_id = str(uuid.uuid4())
        work = mysql_service.insert_work(author_id=author_id, title='Parent Work')
        work_id = work['work_id']

        # 插入章节
        chapter = mysql_service.insert_chapter(
            work_id=work_id,
            author_id=author_id,
            chapter_number=1,
            chapter_title='Test Chapter',
            content='Chapter content'
        )
        assert 'chapter_id' in chapter
        chapter_id = chapter['chapter_id']

        # 查询章节
        fetched = mysql_service.fetch_chapter_by_id(chapter_id)
        assert fetched is not None
        assert fetched['chapter_title'] == 'Test Chapter'
        assert fetched['chapter_number'] == 1

        # 更新章节
        update_data = {'chapter_title': 'Updated Chapter', 'content': 'Updated content'}
        updated = mysql_service.update_chapter(chapter_id, update_data)
        assert updated is not None
        assert updated['chapter_title'] == 'Updated Chapter'

        # 删除章节
        deleted = mysql_service.delete_chapter(chapter_id)
        assert deleted is True

        # 验证删除
        fetched_after = mysql_service.fetch_chapter_by_id(chapter_id)
        assert fetched_after is None

        # 清理作品
        mysql_service.delete_work(work_id)

        print('MySQL chapter CRUD test passed')

def test_mongo_work_details():
    """测试 MongoDB work_details 操作"""
    with app.app_context():
        work_id = str(uuid.uuid4())
        asset_ids = [str(uuid.uuid4()) for _ in range(3)]
        chapter_ids = [str(uuid.uuid4()) for _ in range(2)]

        # 插入 work_details
        mongo_service.insert_work_details(work_id, asset_ids=asset_ids, chapter_ids=chapter_ids)

        # 查询 work_details
        details = mongo_service.fetch_work_details(work_id)
        assert details is not None
        assert details['work_id'] == work_id
        assert details['asset_ids'] == asset_ids
        assert details['chapter_ids'] == chapter_ids

        # 更新 work_details
        new_asset_ids = [str(uuid.uuid4())]
        updated = mongo_service.update_work_details(work_id, asset_ids=new_asset_ids)
        assert updated is True

        # 验证更新
        updated_details = mongo_service.fetch_work_details(work_id)
        assert updated_details['asset_ids'] == new_asset_ids
        # chapter_ids 应保持不变
        assert updated_details['chapter_ids'] == chapter_ids

        # 测试添加资产到作品
        new_asset_id = str(uuid.uuid4())
        added = mongo_service.add_asset_to_work(work_id, new_asset_id)
        assert added is True
        details_after_add = mongo_service.fetch_work_details(work_id)
        assert new_asset_id in details_after_add['asset_ids']

        # 测试从作品中移除资产
        removed = mongo_service.remove_asset_from_work(work_id, new_asset_id)
        assert removed is True
        details_after_remove = mongo_service.fetch_work_details(work_id)
        assert new_asset_id not in details_after_remove['asset_ids']

        # 删除 work_details
        deleted = mongo_service.delete_work_details(work_id)
        assert deleted is True

        # 验证删除
        details_after_delete = mongo_service.fetch_work_details(work_id)
        assert details_after_delete is None

        print('MongoDB work_details test passed')

def test_cross_database_interaction():
    """测试 MySQL 和 MongoDB 之间的交互：创建资产并在两边存储数据"""
    with app.app_context():
        user_id = str(uuid.uuid4())
        asset_type = 'cross_test'

        # 在 MySQL 中创建资产
        asset = mysql_service.insert_asset(user_id=user_id, asset_type=asset_type)
        asset_id = asset['asset_id']

        # 在 MongoDB 中存储 asset_data
        asset_data = {'description': 'Cross database test', 'metadata': {'size': 100}}
        mongo_service.insert_asset_data(asset_id, asset_data)

        # 验证 MySQL 中的数据
        mysql_asset = mysql_service.fetch_asset_by_id(asset_id)
        assert mysql_asset is not None
        assert mysql_asset['asset_id'] == asset_id
        assert mysql_asset['user_id'] == user_id

        # 验证 MongoDB 中的数据
        mongo_data = mongo_service.fetch_asset_data(asset_id)
        assert mongo_data is not None
        assert mongo_data['description'] == 'Cross database test'
        assert mongo_data['metadata']['size'] == 100

        # 清理
        mysql_service.delete_asset(asset_id)
        mongo_service.delete_asset_data(asset_id)

        print('Cross-database interaction test passed')

if __name__ == '__main__':
    # 运行所有测试
    setup_module()
    try:
        test_mysql_asset_crud()
        test_mongo_asset_data_crud()
        test_mysql_work_crud_with_tags()
        test_mysql_work_tags_storage()
        test_mysql_chapter_crud()
        test_mongo_work_details()
        test_cross_database_interaction()
        print('All database integration tests passed successfully!')
    except Exception as e:
        print(f'Test failed with error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
