# api/routes/anime.py
"""
Anime 路由模块（原 Shots 模块）
统一使用 MySQL/MongoDB 存储
"""
from flask import Blueprint, request
from utils.response_helper import error_response, api_response
from utils.decorators import handle_errors, audit_log
from utils.general_helper import validate_required_fields
from db import MySQLService, MongoService, asset_service
from db.anime import anime_service
from db.mongo_anime import anime_details_service
from services.video_generation_service import video_generation_service
from utils.constants import RequestParams
from utils.picture_uploader import upload_picture_file
import logging
import uuid

anime_bp = Blueprint('anime', __name__)
logger = logging.getLogger(__name__)


def _get_picture_source(picture_data):
    """获取 picture 的资源来源（cos_url 或 cloudflare_url）"""
    if not picture_data:
        return None
    if isinstance(picture_data, dict):
        return picture_data.get('cos_url') or picture_data.get('cloudflare_url')
    return None


def _get_picture_for_video_generation(data, user_id, work_id):
    """
    获取视频生成所需的图片信息

    优先级：
    1. 通过 asset_id 从数据库获取（验证用户权限）
    2. 从前端回传的 picture 对象获取（url）
    3. 从前端回传的图片文件上传获取
    4. 从前端回传的 picture_url 创建新 asset

    Args:
        data: 请求数据
        user_id: 用户 ID
        work_id: 作品 ID

    Returns:
        tuple: (picture_url, picture_id, error_response)
        - 成功：(url, id, None)
        - 失败：(None, None, error_response)
    """
    # 1. 尝试从 asset_id 获取
    asset_id = data.get('asset_id')
    if not asset_id and isinstance(data.get('picture'), dict):
        asset_id = data['picture'].get('asset_id')

    if asset_id:
        asset = asset_service.fetch_asset_by_id(asset_id)

        if not asset:
            return None, None, error_response(f'Asset not found: {asset_id}', 404)

        if asset.get('user_id') != user_id:
            return None, None, error_response('Unauthorized: This asset does not belong to the user', 403)

        if asset.get('asset_type') != 'picture':
            return None, None, error_response('Invalid asset type: expected picture', 400)

        asset_data = MongoService().fetch_asset_data(asset_id)
        if asset_data and asset_data.get('oss_url'):
            return asset_data['oss_url'], asset_id, None
        else:
            return None, None, error_response('Asset data not found or missing oss_url', 404)

    # 2. 尝试从 picture 对象获取（url 形式）
    picture_data = data.get('picture')
    if picture_data and isinstance(picture_data, dict):
        picture_url = _get_picture_source(picture_data)
        picture_id = picture_data.get('id') or picture_data.get('asset_id')
        if picture_url:
            return picture_url, picture_id, None

    # 3. 尝试从图片文件上传获取
    if request.files and 'picture' in request.files:
        file = request.files['picture']
        picture_url, picture_id, error = upload_picture_file(file, user_id, work_id)
        if error:
            return None, None, error
        if picture_url:
            return picture_url, picture_id, None

    # 所有方式都失败
    return None, None, error_response('Picture is required for video generation. Provide asset_id, picture file, or picture_url', 400)


@anime_bp.route('/createAnime', methods=['POST'])
@handle_errors
@audit_log(action_name='create_anime')
def create_anime():
    """创建新的 anime 镜头"""
    data = request.get_json()
    validate_required_fields(data, ['work_id', 'author_id', 'anime_number'])

    work_id = data['work_id']
    author_id = data['author_id']
    anime_number = data['anime_number']
    description = data.get('description', '')
    notes = data.get('notes', '')

    anime = anime_service.insert_anime(
        work_id=work_id,
        author_id=author_id,
        anime_number=anime_number,
        description=description,
        notes=notes
    )

    # 添加到 MongoDB work_details
    try:
        MongoService().add_chapter_to_work(work_id, anime['anime_id'])
    except Exception as e:
        logger.warning(f"Failed to update work_details: {str(e)}")

    return api_response(
        success=True,
        message='Anime created successfully',
        data=anime,
        count=1
    )


@anime_bp.route('/getAnimesByWorkId', methods=['GET'])
@handle_errors
def get_animes_by_work_id():
    """根据 work_id 获取 anime 镜头列表"""
    validate_required_fields(request.args, ['work_id'])
    work_id = request.args.get('work_id')

    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
    except ValueError:
        return error_response('Invalid limit or offset', 400)

    animes = anime_service.fetch_anime_by_work_id(work_id, limit, offset)
    return api_response(
        success=True,
        message='Animes fetched successfully',
        data=animes,
        count=len(animes)
    )


@anime_bp.route('/generateVideo', methods=['POST'])
@handle_errors
@audit_log(action_name='generate_video')
def generate_video_endpoint():
    """生成 anime 视频（单图 + 参考视频）"""
    data = request.get_json()
    # 必填参数：anime_id, prompt, user_id
    # picture 可以是 asset_id 或直接提供图片信息
    validate_required_fields(data, ['anime_id', 'prompt', 'user_id'])

    anime_id = data['anime_id']
    user_id = data['user_id']
    prompt = data['prompt']
    negative_prompt = data.get('negative_prompt', '')
    style = data.get('style', '')
    creativity = data.get('creativity', 0.3)
    ratio = data.get('ratio', '16:9')

    # 获取 anime 信息
    anime = anime_service.fetch_anime_by_id(anime_id)
    if not anime:
        return error_response('Anime not found', 404)

    # 获取图片信息
    picture_url, picture_id, error = _get_picture_for_video_generation(
        data=data,
        user_id=user_id,
        work_id=anime.get('work_id')
    )
    if error:
        return error

    # 调用视频生成服务
    try:
        video_result = video_generation_service.generate_single_image_anime(
            image_url=picture_url,
            prompt=prompt
        )

        # 更新 MongoDB 中的 anime_details
        if picture_id:
            anime_details_service.add_asset_to_anime(
                anime_id=anime_id,
                asset_id=picture_id,
                asset_type='picture',
                asset_data={'asset_id': picture_id, 'url': picture_url}
            )

        # 保存生成的视频信息到 MongoDB
        if video_result.get('success') and video_result.get('video_url'):
            video_asset_id = str(uuid.uuid4())
            anime_details_service.add_asset_to_anime(
                anime_id=anime_id,
                asset_id=video_asset_id,
                asset_type='video',
                asset_data={
                    'video_url': video_result.get('video_url'),
                    'task_id': video_result.get('task_id'),
                    'prompt': prompt,
                    'model_used': video_result.get('model_used', 'wan2.6-i2v')
                }
            )
            video_result['video_asset_id'] = video_asset_id

        return api_response(
            success=True,
            message='Video generation task created',
            data=video_result,
            count=1
        )
    except Exception as e:
        logger.error(f"Video generation failed: {str(e)}")
        return error_response(f'Video generation failed: {str(e)}', 500)


def _get_pictures_for_video_generation(pictures_input, user_id):
    """
    获取多图片视频生成所需的所有图片信息

    支持格式：
    1. asset_id 字符串列表
    2. 包含图片信息的对象列表

    Args:
        pictures_input: 请求中的 pictures 参数
        user_id: 用户 ID

    Returns:
        tuple: (picture_urls, picture_ids, error_response)
        - 成功：([url1, url2, ...], [id1, id2, ...], None)
        - 失败：([], [], error_response)
    """
    picture_urls = []
    picture_ids = []

    for pic in pictures_input:
        if isinstance(pic, str):
            # 字符串：asset_id
            asset_id = pic
            asset = asset_service.fetch_asset_by_id(asset_id)
            if not asset:
                return [], [], error_response(f'Asset not found: {asset_id}', 404)

            if asset.get('user_id') != user_id:
                return [], [], error_response('Unauthorized: This asset does not belong to the user', 403)

            if asset.get('asset_type') != 'picture':
                return [], [], error_response(f'Invalid asset type for {asset_id}: expected picture', 400)

            asset_data = MongoService().fetch_asset_data(asset_id)
            if asset_data and asset_data.get('oss_url'):
                picture_urls.append(asset_data['oss_url'])
                picture_ids.append(asset_id)
            else:
                logger.warning(f"Asset {asset_id} missing oss_url, skipping")

        elif isinstance(pic, dict):
            # 对象：尝试获取 asset_id
            asset_id = pic.get('asset_id') or pic.get('id')
            if asset_id:
                asset = asset_service.fetch_asset_by_id(asset_id)

                
                if asset and asset.get('user_id') == user_id:
                    asset_data = MongoService().fetch_asset_data(asset_id)
                    if asset_data and asset_data.get('oss_url'):
                        picture_urls.append(asset_data['oss_url'])
                        picture_ids.append(asset_id)
                        continue

            # 回退到直接使用 url
            url = _get_picture_source(pic)
            if url:
                picture_urls.append(url)
                picture_ids.append(asset_id or str(uuid.uuid4()))

    if not picture_urls:
        return [], [], error_response('At least one valid picture is required', 400)

    return picture_urls, picture_ids, None


@anime_bp.route('/generateMultiImageVideo', methods=['POST'])
@handle_errors
@audit_log(action_name='generate_multi_image_video')
def generate_multi_image_video_endpoint():
    """生成多图片视频"""
    data = request.get_json()
    # 必填参数：anime_id, prompt, user_id, pictures (asset_id 列表)
    validate_required_fields(data, ['anime_id', 'user_id', 'pictures'])

    anime_id = data['anime_id']
    user_id = data['user_id']
    prompt = data.get('prompt', '')

    # 获取 anime 信息
    anime = anime_service.fetch_anime_by_id(anime_id)
    if not anime:
        return error_response('Anime not found', 404)

    # 处理 pictures 列表
    pictures_input = data.get('pictures', [])
    picture_urls, picture_ids, error = _get_pictures_for_video_generation(pictures_input, user_id)
    if error:
        return error

    # 调用视频生成服务
    try:
        video_result = video_generation_service.merge_videos(picture_urls)

        # 更新 MongoDB 中的 anime_details
        for i, pic_id in enumerate(picture_ids):
            if pic_id and i < len(picture_urls):
                anime_details_service.add_asset_to_anime(
                    anime_id=anime_id,
                    asset_id=pic_id,
                    asset_type='picture',
                    asset_data={'asset_id': pic_id, 'url': picture_urls[i]}
                )

        # 保存生成的视频信息到 MongoDB
        if video_result.get('success') and video_result.get('video_url'):
            video_asset_id = str(uuid.uuid4())
            anime_details_service.add_asset_to_anime(
                anime_id=anime_id,
                asset_id=video_asset_id,
                asset_type='video',
                asset_data={
                    'video_url': video_result.get('video_url'),
                    'model_used': video_result.get('model_used', 'wan2.6-i2v')
                }
            )
            video_result['video_asset_id'] = video_asset_id

        return api_response(
            success=True,
            message='Multi-image video generation task created',
            data=video_result,
            count=1
        )
    except Exception as e:
        logger.error(f"Multi-image video generation failed: {str(e)}")
        return error_response(f'Video generation failed: {str(e)}', 500)


@anime_bp.route('/confirm', methods=['POST'])
@handle_errors
@audit_log(action_name='confirm_anime')
def confirm_anime():
    """确认 anime 镜头（标记为完成）"""
    data = request.get_json()
    validate_required_fields(data, ['anime_id'])

    anime_id = data['anime_id']

    # 更新 anime 状态
    updated = anime_service.update_anime(anime_id, {'status': 'confirmed'})
    if not updated:
        return error_response('Anime not found', 404)

    return api_response(
        success=True,
        message='Anime confirmed successfully',
        data=updated,
        count=1
    )


@anime_bp.route('/getVideoDetails', methods=['GET'])
@handle_errors
def get_video_details():
    """获取视频镜头详情（包含 asset 信息）"""
    validate_required_fields(request.args, ['anime_id'])
    anime_id = request.args.get('anime_id')

    # 获取 anime 基本信息
    anime = anime_service.fetch_anime_by_id(anime_id)
    if not anime:
        return error_response('Anime not found', 404)

    # 获取 MongoDB 中的 details
    details = anime_details_service.fetch_anime_details(anime_id)

    # 合并数据
    if details:
        anime['asset_ids'] = details.get('asset_ids', [])
        anime['video_assets'] = details.get('video_assets', [])
        anime['picture_assets'] = details.get('picture_assets', [])
    else:
        anime['asset_ids'] = []
        anime['video_assets'] = []
        anime['picture_assets'] = []

    return api_response(
        success=True,
        message='Video details fetched successfully',
        data=anime,
        count=1
    )


@anime_bp.route('/health', methods=['GET'])
@handle_errors
def health_check():
    """健康检查"""
    return api_response(
        success=True,
        message='Anime service is healthy',
        data={'status': 'ok'},
        count=1
    )
