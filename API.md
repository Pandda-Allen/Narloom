# API 接口文档

**项目名称**: Narloom API
**版本**: 2.0
**更新日期**: 2026-03-21
**基础路径**: `/`

---

## 目录

1. [认证说明](#认证说明)
2. [用户模块 (User)](#用户模块-user)
3. [资产模块 (Asset)](#资产模块-asset)
4. [作品模块 (Work)](#作品模块-work)
5. [章节模块 (Chapter)](#章节模块-chapter)
6. [AI 服务 (AI)](#ai-服务-ai)
7. [动漫工具 (Anime Tool)](#动漫工具-anime-tool)
8. [数据库说明](#数据库说明)

---

## 认证说明

### JWT Token 认证

大多数需要用户身份验证的接口需要在请求头中携带 JWT Token：

```
Authorization: Bearer <access_token>
```

### Token 类型

| Token 类型 | 有效期 | 用途 |
|-----------|--------|------|
| access_token | 30 分钟 | 访问受保护的 API |
| refresh_token | 7 天 | 刷新 access_token |

### OAuth2.0 第三方登录

支持以下第三方登录平台：
- **微信 (WeChat)**: `snsapi_login` scope
- **QQ**: `get_user_info` scope

---

## 用户模块 (User)

**基础路径**: `/user`

### 1. 用户注册

**端点**: `POST /user/register`

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "用户名",
  "bio": "个人简介"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Registration successful",
  "data": {
    "user": {
      "user_id": "uuid",
      "email": "user@example.com",
      "name": "用户名",
      "bio": "个人简介",
      "phone": null,
      "avatar_url": null,
      "created_at": "2026-03-21T00:00:00",
      "last_login_provider": "email"
    },
    "access_token": "<JWT>",
    "refresh_token": "<JWT>",
    "token_type": "Bearer",
    "expires_in": 1800
  }
}
```

---

### 2. 用户登录

**端点**: `POST /user/login`

**请求体**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**响应**: 同注册响应

---

### 3. 刷新 Token

**端点**: `POST /user/refresh`

**权限**: 需要 refresh_token

**请求体**:
```json
{
  "refresh_token": "<JWT>"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Token refreshed successfully",
  "data": {
    "access_token": "<新 JWT>",
    "refresh_token": "<新 JWT>",
    "token_type": "Bearer",
    "expires_in": 1800
  }
}
```

---

### 4. 用户登出

**端点**: `POST /user/logout`

**权限**: `@jwt_required`

**请求体**:
```json
{
  "refresh": false  // 可选，是否同时使 refresh_token 失效
}
```

**响应**:
```json
{
  "success": true,
  "message": "Logout successful"
}
```

---

### 5. 获取当前用户资料

**端点**: `GET /user/me`

**权限**: `@jwt_required`

**响应**:
```json
{
  "success": true,
  "message": "Current user fetched successfully",
  "data": {
    "user_id": "uuid",
    "email": "user@example.com",
    "name": "用户名",
    "bio": "个人简介",
    "phone": null,
    "avatar_url": null,
    "created_at": "2026-03-21T00:00:00",
    "last_login_provider": "email"
  }
}
```

---

### 6. 获取用户资料

**端点**: `GET /user/:user_id`

**请求参数**:
- `user_id` (路径参数): 用户 ID

**响应**: 同获取当前用户资料

---

### 7. 更新用户资料

**端点**: `PUT /user/:user_id`

**请求体** (所有字段可选):
```json
{
  "name": "新用户名",
  "bio": "新的个人简介",
  "email": "newemail@example.com",
  "phone": "13800138000",
  "avatar_url": "https://example.com/avatar.jpg"
}
```

---

### 8. 删除用户

**端点**: `DELETE /user/:user_id`

**说明**: 级联删除用户相关的所有数据

---

### 9. 获取微信 OAuth 授权 URL

**端点**: `GET /user/oauth/wechat/redirect`

**响应**:
```json
{
  "success": true,
  "message": "WeChat auth URL generated",
  "data": {
    "authorization_url": "https://open.weixin.qq.com/connect/qrconnect?...",
    "state": "random_state_string"
  }
}
```

---

### 10. 获取 QQ OAuth 授权 URL

**端点**: `GET /user/oauth/qq/redirect`

**响应**: 类似微信授权 URL 响应

---

### 11. 微信 OAuth 回调

**端点**: `POST /user/oauth/wechat/callback`

**请求体**:
```json
{
  "code": "authorization_code",
  "state": "state_string"
}
```

**响应**:
```json
{
  "success": true,
  "message": "WeChat login successful",
  "data": {
    "user": {...},
    "access_token": "<JWT>",
    "refresh_token": "<JWT>",
    "token_type": "Bearer",
    "expires_in": 1800
  }
}
```

---

### 12. QQ OAuth 回调

**端点**: `POST /user/oauth/qq/callback`

**请求体**: 同微信回调

---

### 13. 绑定 OAuth 账号

**端点**: `POST /user/oauth/bind`

**权限**: `@jwt_required`

**请求体**:
```json
{
  "provider": "wechat",  // 或 "qq"
  "code": "authorization_code"
}
```

---

### 14. 解绑 OAuth 账号

**端点**: `POST /user/oauth/unbind/:provider`

**权限**: `@jwt_required`

**路径参数**:
- `provider`: `wechat` 或 `qq`

---

### 15. 获取绑定的 OAuth 账号列表

**端点**: `GET /user/oauth/accounts`

**权限**: `@jwt_required`

**响应**:
```json
{
  "success": true,
  "message": "Bound accounts fetched successfully",
  "data": {
    "accounts": [
      {
        "provider": "wechat",
        "open_id": "xxx",
        "union_id": "xxx",
        "created_at": "2026-03-21T00:00:00"
      }
    ]
  }
}
```

---

## 资产模块 (Asset)

**基础路径**: `/asset`

### 1. 创建新资产

**端点**: `POST /asset/createNewAsset`

**请求体**:
```json
{
  "type": "character",  // 或 "world"
  "user_id": "uuid",
  "work_id": "uuid",  // 可选
  "asset_data": {}  // MongoDB 存储的详细数据
}
```

**响应**:
```json
{
  "success": true,
  "message": "Asset created successfully",
  "data": {
    "asset_id": "uuid",
    "user_id": "uuid",
    "work_id": "uuid",
    "asset_type": "character",
    "created_at": "2026-03-21T00:00:00",
    "updated_at": "2026-03-21T00:00:00",
    "asset_data": {}
  },
  "count": 1
}
```

---

### 2. 更新资产

**端点**: `POST /asset/updateAssetById`

**请求体**:
```json
{
  "asset_id": "uuid",
  "work_id": "uuid",  // 可选
  "type": "character",  // 可选
  "asset_data": {}  // 可选
}
```

---

### 3. 获取资产详情

**端点**: `GET /asset/getAssetById`

**请求参数**:
- `asset_id`: 资产 ID

---

### 4. 获取用户资产列表

**端点**: `GET /asset/getAssetsByUserId`

**请求参数**:
- `user_id`: 用户 ID
- `type`: 资产类型 (可选)
- `work_id`: 作品 ID (可选)
- `limit`: 数量限制 (可选，默认 10)
- `offset`: 偏移量 (可选，默认 0)

---

### 5. 删除资产

**端点**: `POST /asset/deleteAssetById`

**请求体**:
```json
{
  "asset_id": "uuid"
}
```

---

## 作品模块 (Work)

**基础路径**: `/work`

### 1. 创建新作品

**端点**: `POST /work/createNovel`

**请求体**:
```json
{
  "author_id": "uuid",
  "title": "作品标题",
  "genre": "类型",
  "tags": "标签 1,标签 2",
  "status": "draft",  // draft, published, completed
  "description": "作品简介"
}
```

---

### 2. 更新作品

**端点**: `POST /work/updateNovelById`

**请求体**:
```json
{
  "work_id": "uuid",
  "title": "新标题",
  "genre": "新类型",
  "tags": "新标签",
  "status": "published",
  "chapter_count": 10,
  "word_count": 100000,
  "description": "新简介"
}
```

---

### 3. 获取作品详情

**端点**: `GET /work/getNovelById`

**请求参数**:
- `novel_id`: 作品 ID

---

### 4. 获取作者作品列表

**端点**: `GET /work/getNovelsByAuthorId`

**请求参数**:
- `author_id`: 作者 ID
- `status`: 状态筛选 (可选)
- `limit`: 数量限制 (可选)
- `offset`: 偏移量 (可选)

---

### 5. 删除作品

**端点**: `POST /work/deleteNovelById`

**请求体**:
```json
{
  "work_id": "uuid"
}
```

---

### 6. 添加资产到作品

**端点**: `POST /work/addAssetToNovel`

**请求体**:
```json
{
  "work_id": "uuid",
  "asset_id": "uuid"
}
```

---

### 7. 获取作品关联资产

**端点**: `GET /work/getAssetsByWorkId`

**请求参数**:
- `work_id`: 作品 ID

---

### 8. 从作品移除资产

**端点**: `POST /work/removeAssetFromNovel`

**请求体**:
```json
{
  "work_id": "uuid",
  "asset_id": "uuid"
}
```

---

## 章节模块 (Chapter)

**基础路径**: `/chapter`

### 1. 创建章节

**端点**: `POST /chapter/createChapter`

**请求体**:
```json
{
  "work_id": "uuid",
  "author_id": "uuid",
  "chapter_number": 1,
  "chapter_title": "第一章",
  "content": "章节内容",
  "status": "published",
  "word_count": 3000,
  "description": "章节简介"
}
```

---

### 2. 更新章节

**端点**: `POST /chapter/updateChapterById`

**请求体**:
```json
{
  "chapter_id": "uuid",
  "chapter_number": 1,
  "chapter_title": "新标题",
  "content": "新内容",
  "status": "published",
  "word_count": 3500
}
```

---

### 3. 获取章节列表

**端点**: `GET /chapter/getChapterByNovelId`

**请求参数**:
- `work_id`: 作品 ID
- `status`: 状态筛选 (可选)
- `limit`: 数量限制 (可选)
- `offset`: 偏移量 (可选)

---

### 4. 删除章节

**端点**: `POST /chapter/deleteChapterById`

**请求体**:
```json
{
  "chapter_id": "uuid"
}
```

---

## AI 服务 (AI)

**基础路径**: `/ai`

### 1. 处理 AI 请求

**端点**: `POST /ai/process`

**请求体**:
```json
{
  "task_type": "chat",  // chat, enhance, abstract, generate, translate, summarize, rewrite, code, analysis
  "model": "qwen3.5-plus",
  "content": {
    "user_prompt": "用户提示词",
    "system_prompt": "系统提示词 (可选)",
    "context": []  // 对话历史 (可选)
  },
  "parameters": {
    "max_tokens": 2000,
    "temperature": 0.7
  }
}
```

---

### 2. 获取支持的模型列表

**端点**: `GET /ai/models`

**响应**:
```json
{
  "success": true,
  "message": "Models fetched successfully",
  "data": {
    "models": ["qwen3.5-plus", "qwen-max", ...]
  },
  "count": 2
}
```

---

### 3. 健康检查

**端点**: `GET /ai/health`

---

### 4. 测试 AI 接口

**端点**: `POST /ai/test`

---

### 5. 获取 AI 能力列表

**端点**: `GET /ai/capabilities`

**响应**:
```json
{
  "success": true,
  "message": "Capabilities fetched successfully",
  "data": {
    "capabilities": {
      "supported_tasks": ["chat", "enhance", "abstract", "generate", "translate", "summarize", "rewrite", "code", "analysis"],
      "supported_languages": ["zh-CN", "en-US", "ja-JP", "ko-KR", "fr-FR", "es-ES", "de-DE", "ru-RU"],
      "max_tokens": 16384,
      "supports_streaming": true,
      "provider": "阿里云通义千问",
      "api_version": "v1"
    }
  }
}
```

---

## 动漫工具 (Anime Tool)

**基础路径**: `/anime-tool`

### 1. 上传漫画图片

**端点**: `POST /anime-tool/uploadPicture`

**Content-Type**: `multipart/form-data`

**请求参数**:
- `picture`: 图片文件 (必填)
- `user_id`: 用户 ID (必填)
- `work_id`: 作品 ID (可选)

**响应**:
```json
{
  "success": true,
  "message": "Picture uploaded successfully",
  "data": {
    "asset_id": "uuid",
    "user_id": "uuid",
    "work_id": "uuid",
    "url": "https://example.com/image.jpg",
    "object_key": "oss/object/key",
    "original_filename": "image.jpg",
    "file_size": 102400
  },
  "count": 1
}
```

---

### 2. 获取漫画图片列表

**端点**: `GET /anime-tool/fetchPicture`

**请求参数**:
- `user_id`: 用户 ID (必填)
- `work_id`: 作品 ID (可选)
- `limit`: 数量限制 (可选，默认 100)
- `offset`: 偏移量 (可选，默认 0)
- `oss_list`: 是否直接从 OSS 获取 (可选，默认 false)

---

### 3. 生成动画

**端点**: `POST /anime-tool/generateAnime`

**Content-Type**: `multipart/form-data` 或 `application/json`

**请求参数**:
- `user_id`: 用户 ID (必填)
- `session_id`: 会话 ID (可选)
- `mode`: 模式 (analyze|generate|chat|confirm)，默认 generate
- `asset_id`: 已上传图片的资产 ID (可选)
- `oss_object_key`: OSS 对象键 (可选)
- `picture`: 新图片文件 (可选)
- `message`: 用户消息 (chat 模式必填)
- `parameters`: 生成参数 (可选)

**模式说明**:
- `analyze`: 分析漫画图片，检测分格
- `generate`: 为分格生成动画
- `chat`: 多轮对话交互
- `confirm`: 确认保存生成的视频

---

### 4. 删除漫画图片

**端点**: `POST /anime-tool/deletePicture`

**请求体**:
```json
{
  "asset_id": "uuid",
  "user_id": "uuid"
}
```

---

### 5. 健康检查

**端点**: `GET /anime-tool/health`

---

## 数据库说明

### MySQL 数据库

**数据库名**: `narloom`

#### 表结构

| 表名 | 说明 |
|------|------|
| `users` | 用户基础信息表 |
| `user_oauth_accounts` | 用户 OAuth 账号绑定表 |
| `token_blacklist` | JWT 令牌黑名单表 |
| `oauth_states` | OAuth state 参数存储表 (CSRF 防护) |
| `assets` | 资产表 (character/world) |
| `works` | 作品表 |
| `chapters` | 章节表 |

### MongoDB 数据库

**数据库名**: `narloom`

#### 集合结构

| 集合名 | 说明 |
|--------|------|
| `asset_data` | 资产详细数据 |
| `work_details` | 作品详细信息 (关联 asset_ids, chapter_ids) |

---

## 错误响应格式

所有错误响应遵循以下格式：

```json
{
  "success": false,
  "message": "错误描述信息"
}
```

### 常见 HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 (Token 缺失或无效) |
| 403 | 禁止访问 (Token 已撤销) |
| 404 | 资源不存在 |
| 409 | 资源冲突 (如邮箱已注册) |
| 500 | 服务器内部错误 |

---

## 环境变量配置

```bash
# JWT 配置
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRES=30
JWT_REFRESH_TOKEN_EXPIRES=7
JWT_ALGORITHM=HS256
JWT_ISSUER=narloom-api
JWT_AUDIENCE=narloom-client

# 微信 OAuth2.0
WECHAT_OAUTH_APP_ID=wx_xxxxx
WECHAT_OAUTH_APP_SECRET=xxxxx
WECHAT_OAUTH_REDIRECT_URI=http://localhost:5000/user/oauth/wechat/callback

# QQ OAuth2.0
QQ_OAUTH_APP_ID=1xxxxx
QQ_OAUTH_APP_KEY=xxxxx
QQ_OAUTH_REDIRECT_URI=http://localhost:5000/user/oauth/qq/callback

# MySQL 配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=xxxxx
MYSQL_DB=narloom

# MongoDB 配置
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=narloom
MONGO_ASSET_DATA_COLLECTION=asset_data
MONGO_WORK_DETAILS_COLLECTION=work_details

# 阿里云 OSS 配置
ALIYUN_OSS_ENDPOINT=oss-cn-shanghai.aliyuncs.com
ALIYUN_OSS_ACCESS_KEY_ID=xxxxx
ALIYUN_OSS_ACCESS_KEY_SECRET=xxxxx
ALIYUN_OSS_BUCKET_NAME=narloom001

# 阿里云 DashScope 配置
DASHSCOPE_API_KEY=xxxxx
DASHSCOPE_DEFAULT_MODEL=qwen3.5-plus
```
