# api/routes/anime.py
"""
Anime 路由模块（原 Shots 模块）
统一使用 MySQL/MongoDB 存储
"""
from flask import Blueprint, request
from utils.response_helper import error_response, api_response
from utils.decorators import handle_errors, audit_log
from utils.general_helper import validate_required_fields
from db import MySQLService, MongoService
from db.anime import anime_service
from db.mongo_anime import anime_details_service
import logging

anime_bp = Blueprint('anime', __name__)
logger = logging.getLogger(__name__)


def _get_picture_source(picture_data):
    """获取 picture 的资源来源（cos_url 或 cloudflare_url）"""
    if not picture_data:
        return None
    if isinstance(picture_data, dict):
        return picture_data.get('cos_url') or picture_data.get('cloudflare_url')
    return None


def _get_picture_from_request(data):
    """从请求数据中提取 picture 信息"""
    picture = data.get('picture')
    if not picture:
        return None, None

    if isinstance(picture, dict):
        picture_url = _get_picture_source(picture)
        picture_id = picture.get('id') or picture.get('asset_id')
        return picture_url, picture_id

    return None, None


def _get_pictures_from_request(data):
    """从请求数据中提取多张图片信息（用于多图片视频生成）"""
    pictures = data.get('pictures', [])
    if not pictures:
        return [], []

    picture_urls = []
    picture_ids = []

    for pic in pictures:
        if isinstance(pic, dict):
            url = _get_picture_source(pic)
            pic_id = pic.get('id') or pic.get('asset_id')
            if url:
                picture_urls.append(url)
                picture_ids.append(pic_id)

    return picture_urls, picture_ids


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
    status = request.args.get('status')

    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
    except ValueError:
        return error_response('Invalid limit or offset', 400)

    animes = anime_service.fetch_anime_by_work_id(work_id, status, limit, offset)
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
    validate_required_fields(data, ['shot_id', 'prompt'])

    shot_id = data['shot_id']
    prompt = data['prompt']
    negative_prompt = data.get('negative_prompt', '')
    style = data.get('style', '')
    creativity = data.get('creativity', 0.3)
    ratio = data.get('ratio', '16:9')

    # 获取 shot 信息
    anime = anime_service.fetch_anime_by_id(shot_id)
    if not anime:
        return error_response('Anime not found', 404)

    # 获取 picture 信息
    picture_url, picture_id = _get_picture_from_request(data)
    if not picture_url:
        return error_response('Picture is required for video generation', 400)

    # 调用视频生成服务
    try:
        video_result = video_generation_service.generate_single_image_anime(
            image_url=picture_url,
            prompt=prompt
        )

        # 更新 MongoDB 中的 anime_details
        if picture_id:
            anime_details_service.add_asset_to_anime(
                anime_id=shot_id,
                asset_id=picture_id,
                asset_type='picture',
                asset_data={'asset_id': picture_id, 'url': picture_url}
            )

        return api_response(
            success=True,
            message='Video generation task created',
            data=video_result,
            count=1
        )
    except Exception as e:
        logger.error(f"Video generation failed: {str(e)}")
        return error_response(f'Video generation failed: {str(e)}', 500)


@anime_bp.route('/generateMultiImageVideo', methods=['POST'])
@handle_errors
@audit_log(action_name='generate_multi_image_video')
def generate_multi_image_video_endpoint():
    """生成多图片视频"""
    data = request.get_json()
    validate_required_fields(data, ['shot_id', 'prompt', 'pictures'])

    shot_id = data['shot_id']
    prompt = data['prompt']
    picture_urls, picture_ids = _get_pictures_from_request(data)

    if not picture_urls:
        return error_response('At least one picture is required', 400)

    # 获取 shot 信息
    anime = anime_service.fetch_anime_by_id(shot_id)
    if not anime:
        return error_response('Anime not found', 404)

    try:
        video_result = video_generation_service.merge_videos(picture_urls)

        # 更新 MongoDB 中的 anime_details
        for i, pic_id in enumerate(picture_ids):
            if pic_id and i < len(picture_urls):
                anime_details_service.add_asset_to_anime(
                    anime_id=shot_id,
                    asset_id=pic_id,
                    asset_type='picture',
                    asset_data={'asset_id': pic_id, 'url': picture_urls[i]}
                )

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
    validate_required_fields(data, ['shot_id'])

    shot_id = data['shot_id']

    # 更新 anime 状态
    updated = anime_service.update_anime(shot_id, {'status': 'confirmed'})
    if not updated:
        return error_response('Anime not found', 404)

    return api_response(
        success=True,
        message='Anime confirmed successfully',
        data=updated,
        count=1
    )


@anime_bp.route('/getAnimeDetails', methods=['GET'])
@handle_errors
def get_anime_details():
    """获取 anime 镜头详情（包含 asset 信息）"""
    validate_required_fields(request.args, ['shot_id'])
    shot_id = request.args.get('shot_id')

    # 获取 anime 基本信息
    anime = anime_service.fetch_anime_by_id(shot_id)
    if not anime:
        return error_response('Anime not found', 404)

    # 获取 MongoDB 中的 details
    details = anime_details_service.fetch_anime_details(shot_id)

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
        message='Anime details fetched successfully',
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
