# API 接口文档

**项目名称**: Narloom API
**版本**: 2.1
**更新日期**: 2026-03-24
**基础路径**: `/`

---

## 目录

1. [认证说明](#认证说明)
2. [用户模块 (User)](#用户模块-user)
3. [资产模块 (Asset)](#资产模块-asset)
4. [作品模块 (Work)](#作品模块-work)
5. [章节模块 (Chapter)](#章节模块-chapter)
6. [AI 服务 (AI)](#ai-服务-ai)
7. [图片服务 (Picture)](#图片服务-picture)
8. [动画生成 (Anime)](#动画生成-anime)
9. [数据库说明](#数据库说明)

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
      "created_at": "2026-03-21T00:00:00"
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
  "refresh": false
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

---

### 6. 获取用户资料

**端点**: `GET /user/:user_id`

**请求参数**:
- `user_id` (路径参数): 用户 ID

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

## 资产模块 (Asset)

**基础路径**: `/rest/v1/asset`

| 端点 | 说明 |
|------|------|
| `POST /createNewAsset` | 创建新资产 |
| `POST /updateAssetById` | 更新资产 |
| `GET /getAssetById` | 获取资产详情 |
| `GET /getAssetsByUserId` | 获取用户资产列表 |
| `POST /deleteAssetById` | 删除资产 |

---

## 作品模块 (Work)

**基础路径**: `/rest/v1/work`

| 端点 | 说明 |
|------|------|
| `POST /createNovel` | 创建新作品 |
| `POST /updateNovelById` | 更新作品 |
| `GET /getNovelById` | 获取作品详情 |
| `GET /getNovelsByAuthorId` | 获取作者作品列表 |
| `POST /deleteNovelById` | 删除作品 |
| `POST /addAssetToNovel` | 添加资产到作品 |
| `GET /getAssetsByWorkId` | 获取作品关联资产 |
| `POST /removeAssetFromNovel` | 从作品移除资产 |

---

## 章节模块 (Chapter)

**基础路径**: `/rest/v1/chapter`

| 端点 | 说明 |
|------|------|
| `POST /createChapter` | 创建章节 |
| `POST /updateChapterById` | 更新章节 |
| `GET /getChapterByNovelId` | 获取章节列表 |
| `POST /deleteChapterById` | 删除章节 |

---

## AI 服务 (AI)

**基础路径**: `/rest/v1/ai`

### 1. 处理 AI 请求

**端点**: `POST /process`

**请求体**:
```json
{
  "task_type": "chat",
  "model": "qwen3.5-plus",
  "content": {
    "user_prompt": "用户提示词",
    "system_prompt": "系统提示词 (可选)",
    "context": []
  },
  "parameters": {
    "max_tokens": 2000,
    "temperature": 0.7
  }
}
```

### 其他接口

| 端点 | 说明 |
|------|------|
| `GET /models` | 获取支持的模型列表 |
| `GET /health` | 健康检查 |
| `POST /test` | 测试 AI 接口 |
| `GET /capabilities` | 获取 AI 能力列表 |

---

## 图片服务 (Picture)

**基础路径**: `/rest/v1/picture`

### 1. 上传漫画图片

**端点**: `POST /uploadPicture`

**Content-Type**: `multipart/form-data`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `picture` | File | 是 | 图片文件 |
| `user_id` | String | 是 | 用户 ID |
| `work_id` | String | 否 | 作品 ID |

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

### 2. 通过 asset_id 获取图片

**端点**: `GET /fetchPictureByAssetId`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `asset_id` | String | 是 | 资产 ID |
| `user_id` | String | 是 | 用户 ID (用于权限验证) |

**响应**:
```json
{
  "success": true,
  "message": "Picture fetched successfully",
  "data": {
    "asset": {
      "asset_id": "uuid",
      "user_id": "uuid",
      "work_id": "uuid",
      "asset_type": "picture",
      "created_at": "2026-03-21T00:00:00",
      "updated_at": "2026-03-21T00:00:00",
      "asset_data": {
        "type": "picture",
        "oss_url": "https://...",
        "oss_object_key": "...",
        "original_filename": "image.jpg",
        "file_size": 102400,
        "upload_timestamp": "2026-03-21T00:00:00"
      }
    }
  },
  "count": 1
}
```

---

### 3. 通过 work_id 获取图片列表

**端点**: `GET /fetchPicturesByWorkId`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `work_id` | String | 是 | 作品 ID |
| `user_id` | String | 是 | 用户 ID |
| `limit` | Integer | 否 | 数量限制 (默认 100) |
| `offset` | Integer | 否 | 偏移量 (默认 0) |

---

### 4. 通过 user_id 获取图片列表

**端点**: `GET /fetchPicturesByUserId`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | String | 是 | 用户 ID |
| `work_id` | String | 否 | 作品 ID (筛选) |
| `limit` | Integer | 否 | 数量限制 (默认 100) |
| `offset` | Integer | 否 | 偏移量 (默认 0) |

---

### 5. 删除漫画图片

**端点**: `POST /deletePicture`

**请求体**:
```json
{
  "asset_id": "uuid",
  "user_id": "uuid"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Picture deleted successfully",
  "data": null,
  "count": 1
}
```

---

### 6. 健康检查

**端点**: `GET /health`

**响应**:
```json
{
  "success": true,
  "message": "Health check completed",
  "data": {
    "service": "picture",
    "status": "healthy",
    "bucket": "narloom001",
    "endpoint": "oss-cn-shanghai.aliyuncs.com"
  }
}
```

---

## 动画生成 (Anime)

**基础路径**: `/rest/v1/anime`

### 1. 生成动画

**端点**: `POST /generateAnime`

**Content-Type**: `multipart/form-data` 或 `application/json`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | String | 是 | 用户 ID |
| `session_id` | String | 否 | 会话 ID (不传则自动创建) |
| `asset_id` | String | 否 | 已上传图片的资产 ID |
| `oss_object_key` | String | 否 | OSS 对象键 |
| `picture` | File | 否 | 新图片文件 |
| `parameters` | Object | 否 | 生成参数 |

**parameters 参数说明**:
```json
{
  "prompt": "用户自定义提示词",
  "style": "anime",
  "duration": 5,
  "motion_strength": 0.5
}
```

**响应**:
```json
{
  "success": true,
  "message": "Anime generation completed",
  "data": {
    "session_id": "uuid",
    "video_url": "https://example.com/video.mp4",
    "preview_url": "https://example.com/preview.jpg",
    "panel_count": 1,
    "total_duration": 5
  },
  "count": 1
}
```

**图片来源优先级**:
1. `asset_id` - 从数据库获取
2. `oss_object_key` - 直接生成 URL
3. `picture` - 上传新图片到 OSS

---

### 2. 多轮对话

**端点**: `POST /chat`

**Content-Type**: `multipart/form-data` 或 `application/json`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | String | 是 | 用户 ID |
| `session_id` | String | 否 | 会话 ID (不传则自动创建) |
| `message` | String | 是 | 用户消息 |
| `asset_id` | String | 否 | 图片资产 ID |
| `oss_object_key` | String | 否 | OSS 对象键 |
| `picture` | File | 否 | 新图片文件 |

**响应**:
```json
{
  "success": true,
  "message": "Chat response generated",
  "data": {
    "session_id": "uuid",
    "response": "AI 回复内容",
    "summary": "对话总结",
    "turn_count": 5
  },
  "count": 1
}
```

---

### 3. 确认保存视频

**端点**: `POST /confirm`

**Content-Type**: `application/json`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | String | 是 | 用户 ID |
| `video_url` | String | 是 | 视频 URL |
| `preview_url` | String | 否 | 预览图 URL |
| `parameters` | Object | 否 | 其他参数 |

**响应**:
```json
{
  "success": true,
  "message": "Video saved successfully",
  "data": {
    "asset_id": "uuid",
    "video_url": "https://example.com/video.mp4",
    "preview_url": "https://example.com/preview.jpg"
  },
  "count": 1
}
```

---

### 4. 健康检查

**端点**: `GET /health`

**响应**:
```json
{
  "success": true,
  "message": "Health check completed",
  "data": {
    "service": "anime"
  }
}
```

---

## 数据库说明

### MySQL 数据库

**数据库名**: `narloom`

#### 表结构

| 表名 | 说明 |
|------|------|
| `users` | 用户基础信息表 |
| `token_blacklist` | JWT 令牌黑名单表 |
| `assets` | 资产表 |
| `works` | 作品表 |
| `chapters` | 章节表 |

### MongoDB 数据库

**数据库名**: `narloom`

#### 集合结构

| 集合名 | 说明 | 索引 |
|--------|------|------|
| `asset_data` | 资产详细数据 | `asset_id` (唯一) |
| `work_details` | 作品详细信息 | `work_id` (唯一), 复合索引 |
| `conversation_history` | 对话历史 | `session_id` (唯一), `user_id`, `expires_at` |

---

## 错误响应格式

所有错误响应遵循以下格式:

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
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未授权 (Token 缺失或无效) |
| 403 | 禁止访问 (Token 已撤销) |
| 404 | 资源不存在 |
| 409 | 资源冲突 |
| 500 | 服务器内部错误 |

---

## 环境变量配置

```bash
# JWT 配置
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRES=30
JWT_REFRESH_TOKEN_EXPIRES=7

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
MONGO_CONVERSATION_COLLECTION=conversation_history

# 阿里云 OSS 配置
ALIYUN_OSS_ENDPOINT=oss-cn-shanghai.aliyuncs.com
ALIYUN_OSS_ACCESS_KEY_ID=xxxxx
ALIYUN_OSS_ACCESS_KEY_SECRET=xxxxx
ALIYUN_OSS_BUCKET_NAME=narloom001
ALIYUN_OSS_CDN_DOMAIN=cdn.example.com

# 阿里云 DashScope 配置
DASHSCOPE_API_KEY=xxxxx
DASHSCOPE_DEFAULT_MODEL=qwen3.5-plus
```

---

## 更新日志

### v2.1 (2026-03-24)
- 拆分 Picture 和 Anime 为两个独立模块
- Picture 模块路由：`/rest/v1/picture`
- Anime 模块路由：`/rest/v1/anime`
- 新增 `/generateAnime` - 生成动画 (支持自动创建会话)
- 新增 `/chat` - 多轮对话交互
- 新增 `/confirm` - 确认保存视频
- 移除 `analyze` 模式
- 新增 `conversation_history` MongoDB 集合
