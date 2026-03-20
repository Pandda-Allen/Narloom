# api/routes/anime_tool.py
"""
Anime Tool 路由模块
提供漫画图片上传、获取、生成视频、删除等功能
"""
from flask import Blueprint, request, current_app
from utils.response_helper import error_response, api_response
from utils.decorators import handle_errors
from utils.general_helper import validate_required_fields
from services.anime_tool_service import anime_tool_service
from services.mysql_service import MySQLService
from services.mongo_service import MongoService
import logging
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple

anime_tool_bp = Blueprint('anime-tool', __name__)
logger = logging.getLogger(__name__)


@anime_tool_bp.route('/uploadPicture', methods=['POST'])
@handle_errors
def upload_picture():
    """
    上传漫画图片到阿里云 OSS

    请求参数：
    - picture: 图片文件 (multipart/form-data)
    - user_id: 用户 ID (必填)
    - work_id: 作品 ID (可选，关联到特定作品)

    返回：
    - asset_id: 创建的资产 ID
    - url: 图片访问 URL
    - object_key: OSS 中的对象键
    """
    # 检查是否有文件上传
    if 'picture' not in request.files:
        return error_response('No picture file provided', 400)

    file = request.files['picture']
    if file.filename == '':
        return error_response('No file selected', 400)

    # 获取表单数据
    data = request.form
    validate_required_fields(data, ['user_id'])

    user_id = data.get('user_id')
    work_id = data.get('work_id', None)

    # 读取文件内容
    file_content = file.read()
    file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'jpg'

    # 生成 OSS 对象键
    object_key = anime_tool_service.generate_object_key(user_id, file_extension)

    # 上传到 OSS
    upload_result = anime_tool_service.upload_picture(
        file_content=file_content,
        object_key=object_key,
        content_type=file.content_type or 'image/jpeg'
    )

    if not upload_result.get('success'):
        return error_response(f"Failed to upload picture: {upload_result.get('error')}", 500)

    # 创建 asset 记录（类型：comic）
    mysql_row = MySQLService().insert_asset(user_id, 'comic', work_id)
    asset_id = mysql_row['asset_id']

    # 创建 asset_data 记录
    asset_data = {
        'type': 'comic_picture',
        'oss_url': upload_result['url'],
        'oss_object_key': object_key,
        'original_filename': file.filename,
        'file_size': len(file_content),
        'upload_timestamp': datetime.now().isoformat()
    }

    try:
        MongoService().insert_asset_data(asset_id, asset_data)
    except Exception as e:
        logger.error(f"Error inserting asset data to MongoDB: {str(e)}")
        # 回滚：删除 MySQL 和 OSS 中的数据
        MySQLService().delete_asset(asset_id)
        anime_tool_service.delete_picture(object_key)
        return error_response('Failed to create asset record', 500)

    result = {
        'asset_id': asset_id,
        'user_id': user_id,
        'work_id': work_id,
        'url': upload_result['url'],
        'object_key': object_key,
        'original_filename': file.filename,
        'file_size': len(file_content)
    }

    return api_response(
        success=True,
        message='Picture uploaded successfully',
        data=result,
        count=1
    )


@anime_tool_bp.route('/fetchPicture', methods=['GET'])
@handle_errors
def fetch_picture():
    """
    获取用户已上传的漫画图片列表

    请求参数：
    - user_id: 用户 ID (必填)
    - work_id: 作品 ID (可选，筛选特定作品的图片)
    - limit: 返回数量限制 (可选，默认 100)
    - offset: 偏移量 (可选，默认 0)
    - oss_list: 是否从 OSS 直接获取列表 (可选，默认 false，设为 true 时直接从 OSS 获取)

    返回：
    - pictures: 图片列表
    """
    validate_required_fields(request.args, ['user_id'])

    user_id = request.args.get('user_id')
    work_id = request.args.get('work_id', None)
    oss_list = request.args.get('oss_list', 'false').lower() == 'true'

    # 如果直接从 OSS 获取
    if oss_list:
        prefix = f"comic/{user_id}/"
        limit_str = request.args.get('limit', '100')
        marker = request.args.get('marker', '')

        try:
            limit = int(limit_str)
        except ValueError:
            return error_response('limit must be an integer', 400)

        oss_result = anime_tool_service.list_pictures(prefix=prefix, max_keys=limit, marker=marker)

        if not oss_result.get('success'):
            return error_response(f"Failed to fetch pictures: {oss_result.get('error')}", 500)

        return api_response(
            success=True,
            message='Pictures fetched successfully from OSS',
            data={
                'pictures': oss_result['pictures'],
                'is_truncated': oss_result['is_truncated'],
                'next_marker': oss_result['next_marker']
            },
            count=oss_result['count']
        )

    # 从数据库获取（默认方式）
    try:
        # 解析分页参数
        limit_str = request.args.get('limit', '100')
        offset_str = request.args.get('offset', '0')
        limit = int(limit_str)
        offset = int(offset_str)
    except ValueError:
        return error_response('limit and offset must be integers', 400)

    # 从 MySQL 获取资产列表
    mysql_rows = MySQLService().fetch_assets(user_id, asset_type='comic', work_id=work_id, limit=limit, offset=offset)

    if not mysql_rows:
        return api_response(
            success=True,
            message='No pictures found',
            data=[],
            count=0
        )

    # 获取 MongoDB 中的 asset_data
    asset_ids = [row['asset_id'] for row in mysql_rows]
    asset_data_map = MongoService().fetch_multiple_asset_data(asset_ids)

    # 构建返回结果
    results = []
    for row in mysql_rows:
        asset_data = asset_data_map.get(row['asset_id'], {})
        results.append({
            'asset_id': row['asset_id'],
            'user_id': row['user_id'],
            'work_id': row.get('work_id'),
            'url': asset_data.get('oss_url', ''),
            'object_key': asset_data.get('oss_object_key', ''),
            'original_filename': asset_data.get('original_filename', ''),
            'file_size': asset_data.get('file_size', 0),
            'upload_timestamp': asset_data.get('upload_timestamp', ''),
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        })

    return api_response(
        success=True,
        message='Pictures fetched successfully',
        data=results,
        count=len(results)
    )


@anime_tool_bp.route('/generateAnime', methods=['POST'])
@handle_errors
def generate_anime():
    """
    生成动画（图生视频）- 主入口函数

    支持三种模式：
    1. analyze: 分析漫画图片，检测分格
    2. generate: 为分格生成动画
    3. chat: 多轮对话交互
    4. confirm: 确认保存生成的视频

    请求参数：
    - user_id: 用户 ID (必填)
    - session_id: 会话 ID (可选，用于多轮对话)
    - mode: 模式 (analyze|generate|chat|confirm)，默认 generate
    - asset_id: 已上传图片的资产 ID (可选)
    - oss_object_key: OSS 对象键 (可选)
    - picture: 新图片文件 (可选)
    - message: 用户消息 (用于 chat 模式)
    - parameters: 生成参数 (可选)
    """
    from services.video_generation_service import video_generation_service
    from services.conversation_history import conversation_history

    # 解析请求数据
    data = request.form if request.files else request.get_json() or {}
    if data is None:
        return error_response('Request body must be JSON or multipart/form-data', 400)

    validate_required_fields(data, ['user_id'])

    # 提取公共参数
    user_id = data.get('user_id')
    session_id = data.get('session_id') or str(uuid.uuid4())
    mode = data.get('mode', 'generate')
    asset_id = data.get('asset_id')
    oss_object_key = data.get('oss_object_key')
    parameters = data.get('parameters', {})

    # 获取图片 URL
    picture_url, oss_object_key = _get_picture_url(user_id, asset_id, oss_object_key, request)

    if not picture_url and mode != 'confirm':
        return error_response('Must provide either asset_id, oss_object_key, or picture file', 400)

    # 根据模式调用不同的处理函数
    if mode == 'analyze':
        return _handle_analyze_mode(
            session_id, user_id, picture_url, oss_object_key,
            conversation_history, video_generation_service
        )
    elif mode == 'generate':
        return _handle_generate_mode(
            session_id, user_id, picture_url, oss_object_key, parameters,
            conversation_history, video_generation_service
        )
    elif mode == 'chat':
        return _handle_chat_mode(
            session_id, user_id, picture_url, oss_object_key, data.get('message', ''),
            conversation_history
        )
    elif mode == 'confirm':
        return _handle_confirm_mode(
            user_id, parameters,
            conversation_history
        )
    else:
        return error_response(f'Unknown mode: {mode}', 400)


def _handle_analyze_mode(session_id, user_id, picture_url, oss_object_key,
                         conversation_history, video_generation_service):
    """
    处理分析模式：分析漫画图片，检测分格

    Args:
        session_id: 会话 ID
        user_id: 用户 ID
        picture_url: 图片 URL
        oss_object_key: OSS 对象键
        conversation_history: 对话历史服务
        video_generation_service: 视频生成服务

    Returns:
        API 响应
    """
    # 获取或初始化会话
    session = conversation_history.get_session(session_id)
    if not session:
        conversation_history.create_session(
            session_id=session_id,
            user_id=user_id,
            context_type='anime_generation',
            context_data={
                'asset_id': None,
                'oss_object_key': oss_object_key,
                'image_url': picture_url
            }
        )

    # 分析漫画图片
    result = video_generation_service.analyze_comic_image(picture_url)

    if result.get('success'):
        # 将分析结果添加到会话历史
        conversation_history.add_message(
            session_id=session_id,
            role='assistant',
            content=f"图片分析完成：检测到 {len(result.get('analysis', {}).get('panels', []))} 个分格",
            metadata={'analysis': result}
        )

        return api_response(
            success=True,
            message='Comic analysis completed',
            data={
                'session_id': session_id,
                'analysis': result.get('analysis'),
                'model_used': result.get('model_used')
            }
        )
    else:
        return error_response(f"Analysis failed: {result.get('error')}", 500)


def _handle_generate_mode(session_id, user_id, picture_url, oss_object_key, parameters,
                          conversation_history, video_generation_service):
    """
    处理生成模式：为分格生成动画

    Args:
        session_id: 会话 ID
        user_id: 用户 ID
        picture_url: 图片 URL
        oss_object_key: OSS 对象键
        parameters: 生成参数
        conversation_history: 对话历史服务
        video_generation_service: 视频生成服务

    Returns:
        API 响应
    """
    # 获取会话历史
    messages = conversation_history.get_messages(session_id)

    # 检测分格
    panel_result = video_generation_service.detect_comic_panels(picture_url)

    if not panel_result.get('success'):
        return error_response(f"Panel detection failed: {panel_result.get('error')}", 500)

    panels = panel_result.get('panels', [])

    if not panels:
        return error_response('No panels detected in the image', 400)

    # 为每个分格生成动画提示词
    prompts = _generate_panel_prompts(
        panels,
        parameters.get('prompt', ''),
        parameters.get('style', 'anime'),
        messages
    )

    # 生成多分格动画
    result = video_generation_service.generate_multi_panel_anime(
        image_url=picture_url,
        panels=panels,
        prompts=prompts,
        transition_style=parameters.get('transition_style', 'smooth')
    )

    if result.get('success'):
        # 记录生成结果到会话
        conversation_history.add_message(
            session_id=session_id,
            role='assistant',
            content=f"动画生成完成：{len(panels)} 个分格，总时长 {result.get('total_duration')} 秒",
            metadata={'video_result': result}
        )

        return api_response(
            success=True,
            message='Anime generation completed (preview - not saved)',
            data={
                'session_id': session_id,
                'video_url': result.get('video_url'),
                'preview_url': result.get('preview_url'),
                'panel_count': result.get('panel_count'),
                'total_duration': result.get('total_duration'),
                'transition_style': result.get('transition_style'),
                'is_preview': True,
                'note': 'Please confirm to save the generated video'
            },
            count=1
        )
    else:
        return error_response(f"Animation generation failed: {result.get('error')}", 500)


def _handle_chat_mode(session_id, user_id, picture_url, oss_object_key, user_message,
                      conversation_history):
    """
    处理对话模式：多轮对话交互

    Args:
        session_id: 会话 ID
        user_id: 用户 ID
        picture_url: 图片 URL
        oss_object_key: OSS 对象键
        user_message: 用户消息
        conversation_history: 对话历史服务

    Returns:
        API 响应
    """
    if not user_message:
        return error_response('Message is required for chat mode', 400)

    # 获取或创建会话
    session = conversation_history.get_session(session_id)
    if not session:
        conversation_history.create_session(
            session_id=session_id,
            user_id=user_id,
            context_type='anime_generation',
            context_data={
                'asset_id': None,
                'oss_object_key': oss_object_key,
                'image_url': picture_url
            }
        )

    # 添加用户消息
    conversation_history.add_message(
        session_id=session_id,
        role='user',
        content=user_message,
        metadata={'image_url': picture_url}
    )

    # 获取更新后的历史（包含自动总结）
    updated_messages = conversation_history.get_messages(session_id, include_summaries=True)

    # 使用 AI 生成回复
    ai_response = _generate_chat_response(user_message, updated_messages, picture_url)

    # 添加 AI 回复到历史
    conversation_history.add_message(
        session_id=session_id,
        role='assistant',
        content=ai_response,
        metadata={}
    )

    # 重新获取历史以获取总结
    _, summary = conversation_history.get_messages(session_id, include_summaries=True)

    return api_response(
        success=True,
        message='Chat response generated',
        data={
            'session_id': session_id,
            'response': ai_response,
            'summary': summary,
            'turn_count': len(updated_messages)
        },
        count=1
    )


def _handle_confirm_mode(_user_id, parameters, _conversation_history):
    """
    处理确认模式：用户确认保存生成的视频

    Args:
        _user_id: 用户 ID (保留用于未来扩展)
        parameters: 包含视频 URL 等参数
        _conversation_history: 对话历史服务 (保留用于未来扩展)

    Returns:
        API 响应
    """
    video_url = parameters.get('video_url')
    preview_url = parameters.get('preview_url')

    if not video_url:
        return error_response('video_url is required for confirm mode', 400)

    # 创建资产记录保存视频
    mysql_row = MySQLService().insert_asset(_user_id, 'comic_video', None)
    asset_id = mysql_row['asset_id']

    # 保存视频信息到 MongoDB
    video_asset_data = {
        'type': 'comic_video',
        'video_url': video_url,
        'preview_url': preview_url,
        'source_asset_id': None,
        'parameters': parameters,
        'created_at': datetime.now().isoformat()
    }

    try:
        MongoService().insert_asset_data(asset_id, video_asset_data)
    except Exception as e:
        logger.error(f"Error saving video asset data: {e}")
        MySQLService().delete_asset(asset_id)
        return error_response('Failed to save video', 500)

    # 更新会话历史（记录保存操作）
    # TODO: 未来可添加更详细的会话记录
    if _conversation_history:
        pass  # 预留扩展位置

    return api_response(
        success=True,
        message='Video saved successfully',
        data={
            'asset_id': asset_id,
            'video_url': video_url,
            'preview_url': preview_url
        },
        count=1
    )


def _get_picture_url(user_id: str, asset_id: str, oss_object_key: str, request) -> Tuple[Optional[str], Optional[str]]:
    """获取图片 URL 的辅助函数"""
    # 1. 如果提供了 asset_id，从数据库获取
    if asset_id:
        mysql_row = MySQLService().fetch_asset_by_id(asset_id)
        if mysql_row and mysql_row['user_id'] == user_id:
            asset_data = MongoService().fetch_asset_data(asset_id)
            if asset_data:
                return asset_data.get('oss_url'), asset_data.get('oss_object_key')

    # 2. 如果提供了 oss_object_key，直接使用
    if oss_object_key:
        url_result = anime_tool_service.get_picture_url(oss_object_key)
        if url_result.get('success'):
            return url_result['url'], oss_object_key

    # 3. 如果提供了新文件，先上传到 OSS
    if 'picture' in request.files:
        file = request.files['picture']
        if file.filename:
            file_content = file.read()
            file_extension = file.filename.split('.')[-1].lower() if '.' in file.filename else 'jpg'
            object_key = anime_tool_service.generate_object_key(user_id, file_extension)

            upload_result = anime_tool_service.upload_picture(
                file_content=file_content,
                object_key=object_key,
                content_type=file.content_type or 'image/jpeg'
            )

            if upload_result.get('success'):
                return upload_result['url'], object_key

    return None, None


def _generate_panel_prompts(panels: List[Dict], user_prompt: str, style: str, messages: List[Dict]) -> List[str]:
    """
    为每个分格生成动画提示词

    Args:
        panels: 分格列表
        user_prompt: 用户自定义提示词
        style: 风格类型
        messages: 对话历史

    Returns:
        List[str]: 每个分格对应的提示词列表
    """
    # 为每个分格生成提示词
    prompts = []
    for panel in panels:
        description = panel.get('description', '漫画分格')
        base_prompt = f"{description}，{style}风格，自然流畅的动画效果，{user_prompt}"
        prompts.append(base_prompt)

    return prompts


def _generate_chat_response(user_message: str, messages: List[Dict], image_url: str) -> str:
    """
    使用 AI 生成聊天回复

    Args:
        user_message: 用户消息
        messages: 对话历史
        image_url: 关联的图片 URL

    Returns:
        str: AI 生成的回复
    """
    from services.ai_service import qwen_ai_service

    # 构建系统提示
    system_prompt = """你是一位专业的漫画动画生成助手。你可以帮助用户：
1. 分析漫画图片内容和分格
2. 为静态漫画分格生成动态动画
3. 调整动画的风格、转场效果等参数
4. 提供创作建议和技术支持

请用友好、专业的语气回答用户的问题。如果涉及技术参数，请提供清晰的说明。"""

    # 构建消息
    content = []
    if image_url:
        content.append({"type": "text", "text": f"参考图片：{image_url}\n"})
    content.append({"type": "text", "text": user_message})

    try:
        result = qwen_ai_service.process_request({
            "task_type": "chat",
            "content": {
                "system_prompt": system_prompt,
                "user_prompt": user_message,
                "context": messages[-10:] if len(messages) > 10 else messages  # 限制上下文长度
            },
            "parameters": {
                "max_tokens": 1000,
                "temperature": 0.7
            }
        })

        if result.get('success'):
            return result.get('result', '抱歉，我暂时无法生成回复。')
        return f"抱歉，生成回复时出错：{result.get('error', '未知错误')}"

    except Exception as e:
        logger.error(f"Error generating chat response: {e}")
        return '抱歉，我暂时无法生成回复，请稍后重试。'


@anime_tool_bp.route('/deletePicture', methods=['POST'])
@handle_errors
def delete_picture():
    """
    删除用户已上传的漫画图片

    请求参数：
    - asset_id: 资产 ID (必填)
    - user_id: 用户 ID (必填，用于权限验证)

    返回：
    - success: 是否删除成功
    - message: 删除结果信息
    """
    data = request.get_json()
    validate_required_fields(data, ['asset_id', 'user_id'])

    asset_id = data.get('asset_id')
    user_id = data.get('user_id')

    # 获取资产信息
    mysql_row = MySQLService().fetch_asset_by_id(asset_id)
    if not mysql_row:
        return error_response('Asset not found', 404)

    # 验证权限
    if mysql_row['user_id'] != user_id:
        return error_response('Unauthorized: This asset does not belong to the user', 403)

    # 获取 asset_data 中的 OSS 信息
    asset_data = MongoService().fetch_asset_data(asset_id)
    oss_object_key = asset_data.get('oss_object_key') if asset_data else None

    # 删除 OSS 中的图片
    if oss_object_key:
        try:
            delete_result = anime_tool_service.delete_picture(oss_object_key)
            if not delete_result.get('success'):
                logger.warning(f"Failed to delete picture from OSS: {delete_result.get('error')}")
                # 继续删除数据库记录，即使 OSS 删除失败
        except Exception as e:
            logger.error(f"Error deleting picture from OSS: {str(e)}")

    # 级联删除数据库中的记录
    try:
        MongoService().delete_asset_data(asset_id)
    except Exception as e:
        logger.error(f"Error deleting asset data from MongoDB: {str(e)}")

    deleted = MySQLService().delete_asset(asset_id)

    if deleted:
        return api_response(
            success=True,
            message='Picture deleted successfully',
            data=None,
            count=1
        )
    else:
        return error_response('Failed to delete asset record', 500)


@anime_tool_bp.route('/health', methods=['GET'])
@handle_errors
def health_check():
    """健康检查"""
    health_status = anime_tool_service.health_check()

    return api_response(
        success=True,
        message='Health check completed',
        data={
            'service': 'anime-tool',
            **health_status
        }
    )
