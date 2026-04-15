"""
系统常量定义模块
集中管理系统中使用的各类常量、字符串、配置项等
"""

# ==================== 资产类型常量 ====================
class AssetType:
    """资产类型常量"""
    PICTURE = 'picture'
    COMIC = 'comic'
    COMIC_VIDEO = 'comic_video'
    VIDEO = 'video'
    AUDIO = 'audio'
    TEXT = 'text'


# ==================== 资产数据类型常量 ====================
class AssetDataType:
    """资产数据类型常量"""
    TYPE = 'type'
    PICTURE = 'picture'
    COMIC_VIDEO = 'comic_video'
    VIDEO_URL = 'video_url'
    PREVIEW_URL = 'preview_url'
    OSS_URL = 'oss_url'
    OSS_OBJECT_KEY = 'oss_object_key'
    ORIGINAL_FILENAME = 'original_filename'
    FILE_SIZE = 'file_size'
    UPLOAD_TIMESTAMP = 'upload_timestamp'
    PARAMETERS = 'parameters'
    CREATED_AT = 'created_at'
    SOURCE_ASSET_ID = 'source_asset_id'


# ==================== 响应消息常量 ====================
class ResponseMessage:
    """API 响应消息常量"""
    # 成功消息
    SUCCESS = 'Success'
    UPLOAD_SUCCESS = 'Picture uploaded successfully'
    FETCH_SUCCESS = 'Picture fetched successfully'
    DELETE_SUCCESS = 'Picture deleted successfully'
    GENERATE_SUCCESS = 'Anime generation completed'
    CHAT_SUCCESS = 'Chat response generated'
    CONFIRM_SUCCESS = 'Video saved successfully'
    HEALTH_CHECK_SUCCESS = 'Health check completed'

    # 错误消息
    NOT_FOUND = 'Asset not found'
    UNAUTHORIZED = 'Unauthorized: This asset does not belong to the user'
    MISSING_PICTURE = 'No picture file provided'
    NO_FILE_SELECTED = 'No file selected'
    INVALID_REQUEST = 'Request body must be JSON or multipart/form-data'
    MISSING_REQUIRED_FIELD = 'Missing required field'
    ANALYSIS_FAILED = 'Analysis failed'
    GENERATION_FAILED = 'Animation generation failed'
    SAVE_FAILED = 'Failed to save video'
    DATABASE_ERROR = 'Database error'
    OSS_ERROR = 'OSS operation failed'


# ==================== 路由路径常量 ====================
class RoutePaths:
    """API 路由路径常量"""
    # Picture 路由
    PICTURE_UPLOAD = '/uploadPicture'
    PICTURE_FETCH_BY_ASSET_ID = '/fetchPictureByAssetId'
    PICTURE_FETCH_BY_WORK_ID = '/fetchPicturesByWorkId'
    PICTURE_FETCH_BY_USER_ID = '/fetchPicturesByUserId'
    PICTURE_DELETE = '/deletePicture'
    PICTURE_HEALTH = '/health'

    # Anime 路由
    ANIME_GENERATE = '/generateAnime'
    ANIME_CHAT = '/chat'
    ANIME_CONFIRM = '/confirm'
    ANIME_HEALTH = '/health'

    # URL 前缀
    PREFIX_REST_V1 = '/rest/v1'
    PREFIX_PICTURE = '/rest/v1/picture'
    PREFIX_ANIME = '/rest/v1/anime'


# ==================== 请求参数常量 ====================
class RequestParams:
    """请求参数常量"""
    # 通用参数
    USER_ID = 'user_id'
    SESSION_ID = 'session_id'
    ASSET_ID = 'asset_id'
    WORK_ID = 'work_id'

    # 图片相关参数
    PICTURE = 'picture'
    OSS_OBJECT_KEY = 'oss_object_key'
    ORIGINAL_FILENAME = 'original_filename'
    FILE_SIZE = 'file_size'

    # 生成参数
    MODE = 'mode'
    FRAME_MODE = 'frame_mode'  # 视频生成模式：single(单帧) / start_end(首尾帧)
    PROMPT = 'prompt'
    STYLE = 'style'
    DURATION = 'duration'
    MOTION_STRENGTH = 'motion_strength'
    PARAMETERS = 'parameters'

    # 聊天参数
    MESSAGE = 'message'

    # 分页参数
    LIMIT = 'limit'
    OFFSET = 'offset'

    # 视频参数
    VIDEO_URL = 'video_url'
    PREVIEW_URL = 'preview_url'


# ==================== 模式常量 ====================
class Modes:
    """操作模式常量"""
    ANALYZE = 'analyze'
    GENERATE = 'generate'
    CHAT = 'chat'
    CONFIRM = 'confirm'


# ==================== HTTP 方法常量 ====================
class HTTPMethods:
    """HTTP 方法常量"""
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'
    PATCH = 'PATCH'


# ==================== 文件类型常量 ====================
class FileTypes:
    """文件类型常量"""
    # 图片
    IMAGE_JPEG = 'image/jpeg'
    IMAGE_PNG = 'image/png'
    IMAGE_GIF = 'image/gif'
    IMAGE_WEBP = 'image/webp'

    # 视频
    VIDEO_MP4 = 'video/mp4'
    VIDEO_WEBM = 'video/webm'

    # 默认扩展名
    DEFAULT_IMAGE_EXTENSION = 'jpg'
    DEFAULT_VIDEO_EXTENSION = 'mp4'


# ==================== OSS 相关常量 ====================
class OSSConfig:
    """OSS 配置常量"""
    # 对象键路径前缀
    COMIC_PATH_PREFIX = 'comic'
    VIDEO_PATH_PREFIX = 'video'

    # URL 过期时间（秒）
    URL_EXPIRES_DEFAULT = 3600
    URL_EXPIRES_LONG = 86400 * 7  # 7 天
    URL_EXPIRES_PERMANENT = 86400 * 365  # 1 年

    # 文件大小限制（字节）
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB


# ==================== MongoDB 集合名称常量 ====================
class MongoCollections:
    """MongoDB 集合名称常量"""
    WORK_DETAILS = 'work_details'
    NOVEL_DETAILS = 'novel_details'
    ANIME_DETAILS = 'anime_details'
    ASSET_DATA = 'asset_data'


# ==================== 分页常量 ====================
class Pagination:
    """分页常量"""
    DEFAULT_LIMIT = 100
    MIN_LIMIT = 1
    MAX_LIMIT = 1000
    DEFAULT_OFFSET = 0


# ==================== 会话相关常量 ====================
class SessionConfig:
    """会话配置常量"""
    CONTEXT_TYPE_ANIME_GENERATION = 'anime_generation'
    ROLE_USER = 'user'
    ROLE_ASSISTANT = 'assistant'
    ROLE_SYSTEM = 'system'
    MAX_CONTEXT_LENGTH = 10


# ==================== AI 相关常量 ====================
class AIConfig:
    """AI 配置常量"""
    # 系统提示
    SYSTEM_PROMPT_CHAT = """你是一位专业的漫画动画生成助手。你可以帮助用户：
1. 分析漫画图片内容和分格
2. 为静态漫画分格生成动态动画
3. 调整动画的风格、转场效果等参数
4. 提供创作建议和技术支持

请用友好、专业的语气回答用户的问题。如果涉及技术参数，请提供清晰的说明。"""

    # 请求参数
    MAX_TOKENS_DEFAULT = 1000
    TEMPERATURE_DEFAULT = 0.7

    # 任务类型
    TASK_TYPE_CHAT = 'chat'
    TASK_TYPE_GENERATE = 'generate'
    TASK_TYPE_ANALYZE = 'analyze'


# ==================== 默认值常量 ====================
class Defaults:
    """默认值常量"""
    # 动画生成默认值
    ANIME_DURATION = 5
    ANIME_MOTION_STRENGTH = 0.5
    ANIME_STYLE = 'anime'

    # 分页默认值
    PAGE_LIMIT = 100
    PAGE_OFFSET = 0

    # 文件扩展名默认值
    IMAGE_EXTENSION = 'jpg'


# ==================== 状态码常量 ====================
class StatusCodes:
    """HTTP 状态码常量"""
    OK = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    INTERNAL_SERVER_ERROR = 500


# ==================== 日志相关常量 ====================
class LogMessages:
    """日志消息常量"""
    # 初始化日志
    SERVICE_INITIALIZED = '{} service initialized successfully'
    SERVICE_INIT_FAILED = 'Failed to initialize {} service'

    # 操作日志
    ASSET_DELETED = 'Deleted asset: {}'
    ASSET_DELETE_FAILED = 'Failed to delete asset: {}'
    OSS_PICTURE_DELETED = 'Deleted OSS picture for asset: {}'
    OSS_PICTURE_DELETE_FAILED = 'Failed to delete OSS picture for asset: {}'
    MONGODB_ASSET_DATA_DELETED = 'Deleted MongoDB asset_data for asset: {}'

    # 错误日志
    DATABASE_ERROR = 'Database error: {}'
    OSS_ERROR = 'OSS error: {}'
    MONGODB_ERROR = 'MongoDB error: {}'
    REQUEST_ERROR = 'Request error: {}'


# ==================== 数据库相关常量 ====================
class DatabaseConfig:
    """数据库配置常量"""
    # 表名
    TABLE_ASSETS = 'assets'
    TABLE_USERS = 'users'
    TABLE_WORKS = 'works'
    TABLE_NOVELS = 'novels'
    TABLE_ANIME = 'anime'

    # 字段名
    FIELD_ASSET_ID = 'asset_id'
    FIELD_USER_ID = 'user_id'
    FIELD_WORK_ID = 'work_id'
    FIELD_ASSET_TYPE = 'asset_type'
    FIELD_CREATED_AT = 'created_at'
    FIELD_UPDATED_AT = 'updated_at'


# ==================== 动画风格常量 ====================
class AnimeStyles:
    """动画风格常量"""
    ANIME = 'anime'
    REALISTIC = 'realistic'
    CARTOON = 'cartoon'
    WATERCOLOR = 'watercolor'
    OIL_PAINTING = 'oil_painting'
    SKETCH = 'sketch'
    PIXEL_ART = 'pixel_art'
    STUDIO_GHIBLI = 'studio_ghibli'
    CYBERPUNK = 'cyberpunk'
    FANTASY = 'fantasy'


# ==================== 视频参数常量 ====================
class VideoConfig:
    """视频配置常量"""
    # 时长范围
    MIN_DURATION = 1
    MAX_DURATION = 30
    DEFAULT_DURATION = 5

    # 运动强度范围
    MIN_MOTION = 0.0
    MAX_MOTION = 1.0
    DEFAULT_MOTION = 0.5

    # 支持的格式
    SUPPORTED_FORMATS = ['mp4', 'webm', 'gif']
