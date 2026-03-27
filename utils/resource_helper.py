"""
资源辅助函数模块
提供常用的资源操作辅助函数，减少路由代码重复
"""
from services.db import MySQLService, MongoService


# ========== 资源获取辅助函数 ==========

def get_full_asset_by_id(asset_id):
    """
    获取完整的资产信息（MySQL + MongoDB）

    Args:
        asset_id: 资产 ID

    Returns:
        dict: 完整的资产信息，如果不存在则返回 None
    """
    mysql_row = MySQLService().fetch_asset_by_id(asset_id)
    if not mysql_row:
        return None

    asset_data = MongoService().fetch_asset_data(asset_id) or {}

    return {
        'asset_id': mysql_row['asset_id'],
        'user_id': mysql_row['user_id'],
        'work_id': mysql_row['work_id'],
        'asset_type': mysql_row['asset_type'],
        'created_at': mysql_row['created_at'],
        'updated_at': mysql_row['updated_at'],
        'asset_data': asset_data
    }


def get_full_work_by_id(work_id):
    """
    获取完整的作品信息（MySQL + MongoDB）

    Args:
        work_id: 作品 ID

    Returns:
        dict: 完整的作品信息，如果不存在则返回 None
    """
    work = MySQLService().fetch_work_by_id(work_id)
    if not work:
        return None

    work_details = MongoService().fetch_work_details(work_id)
    if work_details:
        work['asset_ids'] = work_details.get('asset_ids', [])
        work['chapter_ids'] = work_details.get('chapter_ids', [])
    else:
        work['asset_ids'] = []
        work['chapter_ids'] = []

    return work


def get_full_chapter_by_id(chapter_id):
    """
    获取完整的章节信息

    Args:
        chapter_id: 章节 ID

    Returns:
        dict: 完整的章节信息，如果不存在则返回 None
    """
    return MySQLService().fetch_chapter_by_id(chapter_id)


# ========== 数据构建辅助函数 ==========

def build_novel_data(data):
    """
    从请求数据构建小说数据

    Args:
        data: 请求数据 dict

    Returns:
        dict: 过滤后的小说数据，只包含有效字段
    """
    novel_data = {
        'author_id': data.get('author_id'),
        'title': data.get('title'),
        'genre': data.get('genre', ''),
        'tags': data.get('tags', []),
        'status': data.get('status', 'draft'),
        'chapter_count': data.get('chapter_count', 0),
        'word_count': data.get('word_count', 0),
        'description': data.get('description', ''),
    }
    return {k: v for k, v in novel_data.items() if v is not None}


def build_chapter_data(data):
    """
    从请求数据构建章节数据

    Args:
        data: 请求数据 dict

    Returns:
        dict: 过滤后的章节数据，只包含有效字段
    """
    return {
        'work_id': data.get('work_id'),
        'author_id': data.get('author_id'),
        'chapter_number': data.get('chapter_number'),
        'chapter_title': data.get('chapter_title', ''),
        'content': data.get('content', ''),
        'status': data.get('status', 'draft'),
        'word_count': data.get('word_count', 0),
        'description': data.get('description', ''),
    }


# ========== 分页参数解析 ==========

def parse_pagination_args(args, default_limit=100, max_limit=1000):
    """
    解析分页参数

    Args:
        args: Flask request.args
        default_limit: 默认每页数量
        max_limit: 最大每页数量

    Returns:
        tuple: (limit, offset) 或 (None, None) 如果参数无效

    Raises:
        ValueError: 当参数无效时抛出
    """
    limit_str = args.get('limit', str(default_limit))
    offset_str = args.get('offset', '0')

    try:
        limit = int(limit_str)
        offset = int(offset_str)
    except ValueError:
        raise ValueError("limit and offset must be integers")

    if limit < 0 or offset < 0:
        raise ValueError("limit and offset must be non-negative integers")

    if limit > max_limit:
        limit = max_limit

    return limit, offset


# ========== 资源存在性检查 ==========

def check_resource_exists(resource_id, resource_type='asset'):
    """
    检查资源是否存在

    Args:
        resource_id: 资源 ID
        resource_type: 资源类型 (asset, work, chapter)

    Returns:
        bool: 资源是否存在
    """
    if resource_type == 'asset':
        return MySQLService().fetch_asset_by_id(resource_id) is not None
    elif resource_type == 'work':
        return MySQLService().fetch_work_by_id(resource_id) is not None
    elif resource_type == 'chapter':
        return MySQLService().fetch_chapter_by_id(resource_id) is not None
    return False


# ========== 资源删除辅助函数 ==========

def delete_asset_cascade(asset_id):
    """
    级联删除资产（MySQL + MongoDB）

    Args:
        asset_id: 资产 ID

    Returns:
        bool: 删除是否成功
    """
    logger = __import__('logging').getLogger(__name__)

    # 先删除 MongoDB 中的数据
    try:
        MongoService().delete_asset_data(asset_id)
    except Exception as e:
        logger.error(f'Error deleting asset data from MongoDB: {e}')

    # 删除 MySQL 中的记录
    return MySQLService().delete_asset(asset_id)


def delete_work_cascade(work_id):
    """
    级联删除作品（MySQL + MongoDB）

    Args:
        work_id: 作品 ID

    Returns:
        bool: 删除是否成功
    """
    logger = __import__('logging').getLogger(__name__)

    # 删除 MySQL 中的记录
    deleted = MySQLService().delete_work(work_id)

    if deleted:
        # 删除 MongoDB 中的 work_details
        try:
            MongoService().delete_work_details(work_id)
        except Exception as e:
            logger.error(f"Error deleting work details: {str(e)}")

    return deleted


def delete_chapter_cascade(chapter_id):
    """
    级联删除章节（MySQL + MongoDB work_details 更新）

    Args:
        chapter_id: 章节 ID

    Returns:
        tuple: (deleted, work_id) 删除是否成功和所属作品 ID
    """
    logger = __import__('logging').getLogger(__name__)

    chapter = MySQLService().fetch_chapter_by_id(chapter_id)
    if not chapter:
        return False, None

    work_id = chapter['work_id']

    # 删除 MySQL 中的章节
    deleted = MySQLService().delete_chapter(chapter_id)

    if deleted:
        # 从 MongoDB work_details 中移除 chapter_id
        try:
            MongoService().remove_chapter_from_work(work_id, chapter_id)
        except Exception as e:
            logger.error(f"Error updating work details after chapter deletion: {str(e)}")

    return deleted, work_id
