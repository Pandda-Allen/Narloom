# API 接口文档

**项目名称**: Narloom API
**版本**: 2.6
**更新日期**: 2026-04-07
**基础路径**: `/`

---

## 项目结构

```
project/
├── db/                        # 数据库访问层（与 services 平级）
│   ├── __init__.py            # 导出所有 MySQL/MongoDB/OSS services
│   ├── base_service.py        # MySQL 基础服务
│   ├── user.py                # 用户数据库操作
│   ├── asset.py               # 资产数据库操作
│   ├── work.py                # 作品数据库操作
│   ├── novel.py               # 小说数据库操作
│   ├── anime.py               # 动画数据库操作
│   ├── mongo_asset.py         # MongoDB 资产操作
│   ├── mongo_work.py          # MongoDB 作品操作
│   ├── mongo_novel.py         # MongoDB 小说操作
│   ├── mongo_anime.py         # MongoDB 动画操作
│   └── storage/               # OSS 存储实现
│       ├── __init__.py
│       ├── oss.py             # OSS 统一接口
│       ├── picture.py         # 图片存储操作
│       └── video.py           # 视频存储操作
├── services/                  # 业务逻辑层
│   ├── anime_service.py       # 动画生成业务逻辑
│   ├── video_generation_service.py  # 视频生成底层服务
│   ├── mysql_service.py       # MySQL 兼容层（引用 db）
│   ├── mongo_service.py       # MongoDB 兼容层（引用 db）
│   ├── ai_service.py
│   ├── jwt_service.py
│   ├── token_blacklist_service.py
│   ├── base_service.py
│   └── conversation_history.py
├── api/
│   └── routes/                # 路由层
├── utils/                     # 工具类
├── config.py                  # 配置文件
└── app.py                     # Flask 应用入口
```

### 架构说明

1. **数据持久化层 (db/)**: 与 services 平级的独立文件夹
   - MySQL 操作 → `db/user.py`, `db/asset.py`, etc.
   - MongoDB 操作 → `db/mongo_asset.py`, `db/mongo_work.py`, etc.
   - OSS 存储操作 → `db/storage/oss.py`, `db/storage/picture.py`, etc.

2. **统一对外接口**:
   - MySQL → `mysql_service` (通过 services/mysql_service.py 引用 db)
   - MongoDB → `mongo_service` (通过 services/mongo_service.py 引用 db)
   - OSS → `oss_service` (通过 db 导出)

3. **业务逻辑层 (services/)**:
   - `anime_service.py` - 动画生成业务逻辑
   - `video_generation_service.py` - 视频生成底层服务
   - 其他服务：ai_service, jwt_service, etc.

### Import 规则

| 来源 | 目标 | Import 语句 |
|------|------|------------|
| 路由层 | MySQL/MongoDB/OSS | `from db import xxx_service` |
| 路由层 | 业务服务 | `from services import xxx_service` |
| services | db | `from db import xxx_service` |
| db | services.base_service | `from services.base_service import BaseService` |

---

## 目录

1. [认证说明](#认证说明)
2. [用户模块 (User)](#用户模块-user)
3. [资产模块 (Asset)](#资产模块-asset)
4. [作品模块 (Work)](#作品模块-work)
5. [小说章节模块 (Novel)](#小说章节模块-novel)
6. [动画镜头模块 (Anime)](#动画镜头模块-anime)
7. [AI 服务 (AI)](#ai-服务-ai)
8. [图片服务 (Picture)](#图片服务-picture)
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

**说明**: 级联删除用户相关的所有数据（assets、works 等）

---

## 资产模块 (Asset)

**基础路径**: `/rest/v1/asset`

资产是系统中的基础资源单元，可用于表示角色 (character)、世界观 (world)、图片 (picture)、视频 (video) 等。

### 1. 创建新资产

**端点**: `POST /createNewAsset`

**请求体**:
```json
{
  "type": "character",
  "user_id": "uuid",
  "work_id": "uuid",
  "asset_data": {
    "name": "角色名称",
    "description": "角色描述",
    "image_url": "https://..."
  }
}
```

**请求参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | String | 是 | 资产类型 (character/world/picture/video 等) |
| `user_id` | String | 是 | 用户 ID |
| `work_id` | String | 否 | 关联的作品 ID |
| `asset_data` | Object | 否 | 资产详细数据 (存储到 MongoDB) |

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
    "created_at": "2026-03-31T00:00:00",
    "updated_at": "2026-03-31T00:00:00",
    "asset_data": {
      "name": "角色名称",
      "description": "角色描述"
    }
  },
  "count": 1
}
```

---

### 2. 更新资产

**端点**: `POST /updateAssetById`

**请求体**:
```json
{
  "asset_id": "uuid",
  "work_id": "uuid",
  "type": "character",
  "asset_data": {
    "name": "新角色名称",
    "description": "新描述"
  }
}
```

**请求参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `asset_id` | String | 是 | 资产 ID |
| `work_id` | String | 否 | 新的作品 ID |
| `type` | String | 否 | 资产类型 |
| `asset_data` | Object | 否 | 更新的详细数据 |

**响应**:
```json
{
  "success": true,
  "message": "Asset updated successfully",
  "data": {
    "asset_id": "uuid",
    "user_id": "uuid",
    "work_id": "uuid",
    "asset_type": "character",
    "created_at": "2026-03-31T00:00:00",
    "updated_at": "2026-03-31T00:00:00",
    "asset_data": {...}
  },
  "count": 1
}
```

---

### 3. 获取资产详情

**端点**: `GET /getAssetById`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `asset_id` | String | 是 | 资产 ID |

**响应**:
```json
{
  "success": true,
  "message": "Asset fetched successfully",
  "data": {
    "asset_id": "uuid",
    "user_id": "uuid",
    "work_id": "uuid",
    "asset_type": "character",
    "created_at": "2026-03-31T00:00:00",
    "updated_at": "2026-03-31T00:00:00",
    "asset_data": {...}
  },
  "count": 1
}
```

---

### 4. 获取用户资产列表

**端点**: `GET /getAssetsByUserId`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | String | 是 | 用户 ID |
| `type` | String | 否 | 资产类型筛选 |
| `work_id` | String | 否 | 作品 ID 筛选 |
| `limit` | Integer | 否 | 数量限制 (默认 100) |
| `offset` | Integer | 否 | 偏移量 (默认 0) |

**响应**:
```json
{
  "success": true,
  "message": "Assets fetched successfully",
  "data": [
    {
      "asset_id": "uuid",
      "user_id": "uuid",
      "work_id": "uuid",
      "asset_type": "character",
      "created_at": "2026-03-31T00:00:00",
      "updated_at": "2026-03-31T00:00:00",
      "asset_data": {...}
    }
  ],
  "count": 10
}
```

---

### 5. 删除资产

**端点**: `POST /deleteAssetById`

**请求体**:
```json
{
  "asset_id": "uuid",
  "user_id": "uuid"
}
```

**说明**: 级联删除 MySQL 中的资产记录和 MongoDB 中的 asset_data

**响应**:
```json
{
  "success": true,
  "message": "Asset deleted successfully",
  "data": null,
  "count": 1
}
```

---

## 作品模块 (Work)

**基础路径**: `/rest/v1/work`

作品是内容的集合，可以包含多个资产 (assets) 和章节 (chapters)。

### 1. 创建新作品

**端点**: `POST /createNovel`

**请求体**:
```json
{
  "author_id": "uuid",
  "title": "作品标题",
  "genre": "类型",
  "tags": ["标签 1", "标签 2"],
  "status": "连载中",
  "description": "作品描述",
  "work_type": "novel"
}
```

**请求参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `author_id` | String | 是 | 作者 ID |
| `title` | String | 是 | 作品标题 |
| `genre` | String | 否 | 类型/体裁 |
| `tags` | Array | 否 | 标签列表 |
| `status` | String | 否 | 状态 (连载中/已完结) |
| `description` | String | 否 | 作品描述 |
| `work_type` | String | 否 | 作品类型：`novel`(小说) / `anime`(动画)，默认 `novel` |

**响应**:
```json
{
  "success": true,
  "message": "Novel created successfully",
  "data": {
    "work_id": "uuid",
    "author_id": "uuid",
    "title": "作品标题",
    "genre": "类型",
    "tags": ["标签 1", "标签 2"],
    "status": "连载中",
    "description": "作品描述",
    "created_at": "2026-03-31T00:00:00",
    "updated_at": "2026-03-31T00:00:00",
    "work_details": {
      "asset_ids": [],
      "chapter_ids": []
    }
  },
  "count": 1
}
```

---

### 2. 更新作品

**端点**: `POST /updateNovelById`

**请求体**:
```json
{
  "work_id": "uuid",
  "title": "新标题",
  "genre": "新类型",
  "tags": ["新标签"],
  "status": "已完结",
  "description": "新描述"
}
```

**可更新字段**: `title`, `genre`, `tags`, `status`, `chapter_count`, `word_count`, `description`

**响应**:
```json
{
  "success": true,
  "message": "Work updated successfully",
  "data": {...},
  "count": 1
}
```

---

### 3. 获取作品详情

**端点**: `GET /getNovelById`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `novel_id` | String | 是 | 作品 ID |

**响应**:
```json
{
  "success": true,
  "message": "Novel fetched successfully",
  "data": {
    "work_id": "uuid",
    "author_id": "uuid",
    "title": "作品标题",
    "genre": "类型",
    "tags": ["标签 1", "标签 2"],
    "status": "连载中",
    "description": "作品描述",
    "created_at": "2026-03-31T00:00:00",
    "updated_at": "2026-03-31T00:00:00",
    "work_details": {
      "asset_ids": ["asset-uuid-1", "asset-uuid-2"],
      "chapter_ids": ["chapter-uuid-1", "chapter-uuid-2"]
    }
  },
  "count": 1
}
```

---

### 4. 获取作者作品列表

**端点**: `GET /getNovelsByAuthorId`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `author_id` | String | 是 | 作者 ID |
| `limit` | Integer | 否 | 数量限制 (默认 100) |
| `offset` | Integer | 否 | 偏移量 (默认 0) |

**响应**:
```json
{
  "success": true,
  "message": "Novels fetched successfully",
  "data": [...],
  "count": 10
}
```

---

### 5. 删除作品

**端点**: `POST /deleteNovelById`

**请求体**:
```json
{
  "novel_id": "uuid"
}
```

**说明**: 级联删除作品、关联的章节和资产

**响应**:
```json
{
  "success": true,
  "message": "Novel deleted successfully",
  "data": null,
  "count": 1
}
```

---

### 6. 添加资产到作品

**端点**: `POST /addAssetToNovel`

**请求体**:
```json
{
  "novel_id": "uuid",
  "asset_id": "uuid"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Asset added to novel successfully",
  "data": {...},
  "count": 1
}
```

---

### 7. 获取作品关联资产

**端点**: `GET /getAssetsByWorkId`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `work_id` | String | 是 | 作品 ID |
| `limit` | Integer | 否 | 数量限制 |
| `offset` | Integer | 否 | 偏移量 |

**响应**:
```json
{
  "success": true,
  "message": "Work assets fetched successfully",
  "data": [...],
  "count": 5
}
```

---

### 8. 从作品移除资产

**端点**: `POST /removeAssetFromNovel`

**请求体**:
```json
{
  "novel_id": "uuid",
  "asset_id": "uuid"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Asset removed from novel successfully",
  "data": null,
  "count": 1
}
```

---

## 小说章节模块 (Novel)

**基础路径**: `/rest/v1/novel`

小说章节是作品的基本内容单元，属于特定作品。

### 1. 创建章节

**端点**: `POST /createNovel`

**请求体**:
```json
{
  "work_id": "uuid",
  "author_id": "uuid",
  "novel_number": 1,
  "novel_title": "第一章：开始",
  "content": "章节内容...",
  "status": "published",
  "description": "章节简介"
}
```

**请求参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `work_id` | String | 是 | 作品 ID |
| `author_id` | String | 是 | 作者 ID |
| `novel_number` | Integer | 是 | 章节序号 |
| `novel_title` | String | 否 | 章节标题 |
| `content` | String | 否 | 章节内容 |
| `status` | String | 否 | 状态 (draft/published) |
| `description` | String | 否 | 章节简介 |

**响应**:
```json
{
  "success": true,
  "message": "Novel created successfully",
  "data": {
    "novel_id": "uuid",
    "work_id": "uuid",
    "author_id": "uuid",
    "novel_number": 1,
    "novel_title": "第一章：开始",
    "content": "章节内容...",
    "status": "published",
    "word_count": 1000,
    "created_at": "2026-03-31T00:00:00",
    "updated_at": "2026-03-31T00:00:00"
  },
  "count": 1
}
```

---

### 2. 更新章节

**端点**: `POST /updateNovelById`

**请求体**:
```json
{
  "novel_id": "uuid",
  "novel_number": 2,
  "novel_title": "新标题",
  "content": "新内容...",
  "status": "published",
  "word_count": 1500,
  "description": "新简介"
}
```

**可更新字段**: `novel_number`, `novel_title`, `content`, `status`, `word_count`, `description`

**响应**:
```json
{
  "success": true,
  "message": "Chapter updated successfully",
  "data": {...},
  "count": 1
}
```

---

### 3. 获取章节列表

**端点**: `GET /getNovelByWorkId`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `work_id` | String | 是 | 作品 ID |
| `status` | String | 否 | 状态筛选 |
| `limit` | Integer | 否 | 数量限制 |
| `offset` | Integer | 否 | 偏移量 |

**响应**:
```json
{
  "success": true,
  "message": "Novels fetched successfully",
  "data": [
    {
      "novel_id": "uuid",
      "work_id": "uuid",
      "author_id": "uuid",
      "novel_number": 1,
      "novel_title": "第一章：开始",
      "content": "...",
      "status": "published",
      "word_count": 1000,
      "created_at": "2026-03-31T00:00:00",
      "updated_at": "2026-03-31T00:00:00"
    }
  ],
  "count": 10
}
```

---

### 4. 删除章节

**端点**: `POST /deleteNovelById`

**请求体**:
```json
{
  "novel_id": "uuid"
}
```

**说明**: 级联删除章节并从作品的章节列表中移除

**响应**:
```json
{
  "success": true,
  "message": "Novel deleted successfully",
  "data": null,
  "count": 1
}
```

---

## 动画镜头模块 (Anime)

**基础路径**: `/rest/v1/anime`

镜头 (Anime) 是动画作品的基本组成单位，一个 anime 类型的 work 由多个 anime 镜头组成。
每个 anime 镜头包含多个 asset（anime 视频 + 上传的 picture）。

### 1. 创建镜头

**端点**: `POST /createAnime`

**请求体**:
```json
{
  "work_id": "uuid",
  "author_id": "uuid",
  "anime_number": 1,
  "description": "镜头描述",
  "notes": "备注"
}
```

**请求参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `work_id` | String | 是 | 作品 ID |
| `author_id` | String | 是 | 作者 ID |
| `anime_number` | Integer | 是 | 镜头编号 |
| `description` | String | 否 | 镜头描述 |
| `notes` | String | 否 | 备注 |

**响应**:
```json
{
  "success": true,
  "message": "Anime created successfully",
  "data": {
    "anime_id": "uuid",
    "work_id": "uuid",
    "author_id": "uuid",
    "anime_number": 1,
    "description": "镜头描述",
    "notes": "备注",
    "created_at": "2026-04-07T00:00:00",
    "updated_at": "2026-04-07T00:00:00"
  },
  "count": 1
}
```

---

### 2. 获取镜头列表

**端点**: `GET /getAnimesByWorkId`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `work_id` | String | 是 | 作品 ID |
| `limit` | Integer | 否 | 每页数量 (默认 100) |
| `offset` | Integer | 否 | 偏移量 (默认 0) |

**响应**:
```json
{
  "success": true,
  "message": "Animes fetched successfully",
  "data": [
    {
      "anime_id": "uuid",
      "work_id": "uuid",
      "author_id": "uuid",
      "anime_number": 1,
      "description": "镜头描述",
      "notes": "备注",
      "created_at": "2026-04-07T00:00:00",
      "updated_at": "2026-04-07T00:00:00"
    }
  ],
  "count": 1
}
```

---

### 3. 生成视频（单图）

**端点**: `POST /generateVideo`

**Content-Type**: `application/json`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `shot_id` | String | 是 | 镜头 ID (anime_id) |
| `prompt` | String | 是 | 动画生成提示词 |
| `negative_prompt` | String | 否 | 负向提示词 |
| `style` | String | 否 | 动画风格 |
| `creativity` | Float | 否 | 创意度 (0-1, 默认 0.3) |
| `ratio` | String | 否 | 视频比例 (默认 16:9) |
| `picture` | Object | 是 | 图片信息 |

**picture 参数说明**:
```json
{
  "asset_id": "uuid",
  "cos_url": "https://...",
  "cloudflare_url": "https://..."
}
```

**响应**:
```json
{
  "success": true,
  "message": "Video generation task created",
  "data": {
    "task_id": "uuid",
    "video_url": "https://example.com/video.mp4",
    "status": "processing"
  },
  "count": 1
}
```

---

### 4. 生成视频（多图片）

**端点**: `POST /generateMultiImageVideo`

**Content-Type**: `application/json`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `shot_id` | String | 是 | 镜头 ID (anime_id) |
| `prompt` | String | 是 | 动画生成提示词 |
| `pictures` | Array | 是 | 图片信息列表 |

**pictures 参数说明**:
```json
[
  {
    "asset_id": "uuid",
    "cos_url": "https://...",
    "cloudflare_url": "https://..."
  }
]
```

**响应**:
```json
{
  "success": true,
  "message": "Multi-image video generation task created",
  "data": {
    "task_id": "uuid",
    "video_url": "https://example.com/merged_video.mp4",
    "status": "processing"
  },
  "count": 1
}
```

---

### 5. 确认镜头

**端点**: `POST /confirm`

**请求体**:
```json
{
  "shot_id": "uuid"
}
```

**说明**: 确认镜头完成

**响应**:
```json
{
  "success": true,
  "message": "Anime confirmed successfully",
  "data": {...},
  "count": 1
}
```

---

### 6. 获取镜头详情

**端点**: `GET /getAnimeDetails`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `shot_id` | String | 是 | 镜头 ID (anime_id) |

**响应**:
```json
{
  "success": true,
  "message": "Anime details fetched successfully",
  "data": {
    "anime_id": "uuid",
    "work_id": "uuid",
    "anime_number": 1,
    "description": "镜头描述",
    "notes": "备注",
    "asset_ids": ["asset-id-1", "asset-id-2"],
    "video_assets": [...],
    "picture_assets": [...]
  },
  "count": 1
}
```

---

### 7. 健康检查

**端点**: `GET /health`

**响应**:
```json
{
  "success": true,
  "message": "Anime service is healthy",
  "data": {
    "status": "ok"
  }
}
```

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

---

### 6. 健康检查

**端点**: `GET /health`

---

## 动画生成 (Anime)

> **注意**: 动画生成功能已迁移至 [镜头模块 (Shots)](#镜头模块-shots)。
> `/rest/v1/anime` 路径下的接口保留用于向后兼容，建议新使用 `/rest/v1/shots` 路径下的接口。
>
> 主要变更：
> - 动画现在按 `shot_id` 组织，每个镜头可以包含多个动画资产
> - 新增 `work_type` 字段区分 `novel`(小说) 和 `anime`(动画) 作品
> - 新增 `anime_details` MongoDB 集合记录作品的 `shots_ids` 列表
> - 新增 `shot_details` MongoDB 集合记录每个镜头的 `video_assets` 和 `picture_assets`

**基础路径**: `/rest/v1/anime` (保留，建议迁移至 `/rest/v1/shots`)

### 1. 生成动画（单张/首尾帧）

**端点**: `POST /generateAnime`

> 已迁移至 `POST /rest/v1/shots/generateAnime`
> 新增必填参数：`shot_id`

**基础路径**: `/rest/v1/anime` (保留，建议迁移至 `/rest/v1/shots')

### 1. 生成动画（单张/首尾帧） - 已弃用

**端点**: `POST /generateAnime`

> **已弃用**: 请使用 `/rest/v1/shots/generateAnime`
>
> 主要变更：
> - 动画现在按 `shot_id` 组织，每个镜头可以包含多个动画资产
> - 新增 `work_type` 字段区分 `novel`(小说) 和 `anime`(动画) 作品
> - 新增 `anime_details` MongoDB 集合记录作品的 `shots_ids` 列表
> - 新增 `shot_details` MongoDB 集合记录每个镜头的 `video_assets` 和 `picture_assets`

**基础路径**: `/rest/v1/anime`

**Content-Type**: `multipart/form-data` 或 `application/json`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | String | 是 | 用户 ID |
| `work_id` | String | 是 | 作品 ID (用于关联作品) |
| `session_id` | String | 否 | 会话 ID (不传则自动创建) |
| `frame_mode` | String | 否 | 帧模式：`single`(单帧) / `start_end`(首尾帧)，默认 `single` |
| **首帧图片参数** (三选一) |
| `asset_id` | String | 否 | 已上传图片的资产 ID |
| `oss_object_key` | String | 否 | OSS 对象键 |
| `picture` | File | 否 | 新图片文件 |
| **尾帧图片参数** (`frame_mode=start_end` 时必填，三选一) |
| `end_asset_id` | String | 否 | 尾帧图片的资产 ID |
| `end_oss_object_key` | String | 否 | 尾帧图片的 OSS 对象键 |
| `end_picture` | File | 否 | 尾帧图片文件 |
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
    "total_duration": 5,
    "frame_mode": "start_end",
    "work_id": "work-uuid"
  },
  "count": 1
}
```

**图片来源优先级** (首帧和尾帧相同):
1. `asset_id` / `end_asset_id` - 从数据库获取
2. `oss_object_key` / `end_oss_object_key` - 直接生成 URL
3. `picture` / `end_picture` - 上传新图片到 OSS

**示例 1 - 单帧模式**:
```json
{
  "user_id": "uuid",
  "work_id": "work-uuid",
  "asset_id": "asset-uuid",
  "parameters": {
    "prompt": "流畅的动画效果",
    "duration": 5
  }
}
```

**示例 2 - 首尾帧模式 (使用 asset_id)**:
```json
{
  "user_id": "uuid",
  "work_id": "work-uuid",
  "frame_mode": "start_end",
  "asset_id": "start-asset-uuid",
  "end_asset_id": "end-asset-uuid",
  "parameters": {
    "prompt": "从第一帧平滑过渡到最后一帧",
    "duration": 5
  }
}
```

**示例 3 - 首尾帧模式 (使用文件上传)**:
```
POST /generateAnime
Content-Type: multipart/form-data

user_id=uuid
work_id=work-uuid
frame_mode=start_end
picture=@start.jpg
end_picture=@end.jpg
parameters={"prompt": "流畅过渡", "duration": 5}
```

**说明**:
- 单帧模式：只需提供首帧图片参数，调用 `generate_single_image_anime` 方法
- 首尾帧模式：需要提供首帧和尾帧图片参数，调用 `generate_start_end_frame_anime` 方法

---

### 2. 生成动画（多张图片）

**端点**: `POST /generateMultiImageAnime`

**Content-Type**: `multipart/form-data` 或 `application/json`

**说明**: 为多张图片依次生成动画，并合并成一个完整视频

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | String | 是 | 用户 ID |
| `work_id` | String | 是 | 作品 ID (用于关联作品) |
| `session_id` | String | 否 | 会话 ID |
| `frame_mode` | String | 否 | 帧模式：`single`(单帧) / `start_end`(首尾帧)，默认 `single` |
| `pictures` | File[] | 否 | 多张图片文件 |
| `asset_ids` | String | 否 | 资产 ID 列表 (逗号分隔) |
| `oss_object_keys` | String | 否 | OSS 对象键列表 (逗号分隔) |
| `parameters` | Object | 否 | 生成参数 |

**parameters 参数说明**:
```json
{
  "prompt": "用户自定义提示词",
  "style": "anime",
  "duration": 5,
  "motion_strength": 0.5,
  "transition": "fade",
  "transition_duration": 0.5
}
```

**响应**:
```json
{
  "success": true,
  "message": "Multi-image anime generation completed",
  "data": {
    "session_id": "uuid",
    "video_url": "https://example.com/merged_video.mp4",
    "preview_url": "https://example.com/preview.jpg",
    "panel_count": 5,
    "total_duration": 25,
    "individual_videos": [
      {
        "video_url": "https://example.com/video1.mp4",
        "preview_url": "https://example.com/preview1.jpg",
        "duration": 5
      }
    ],
    "frame_mode": "single",
    "work_id": "work-uuid"
  },
  "count": 5
}
```

**frame_mode 说明**:
- `single` (默认): 每张图片单独生成动画
- `start_end`: 相邻两张图片作为首尾帧生成动画（例如：图片 1→图片 2，图片 2→图片 3）

**图片来源**:
- 可以混合使用 `pictures` (上传文件)、`asset_ids` (数据库资产)、`oss_object_keys` (OSS 对象键)
- 至少提供一种来源的一张图片

---

### 3. 多轮对话

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

### 4. 确认保存视频

**端点**: `POST /confirm`

**Content-Type**: `application/json`

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `user_id` | String | 是 | 用户 ID |
| `work_id` | String | 是 | 作品 ID (用于关联作品) |
| `video_url` | String | 是 | 视频 URL (临时 URL，需保存到 OSS) |
| `preview_url` | String | 否 | 预览图 URL |
| `parameters` | Object | 否 | 其他参数 |

**响应**:
```json
{
  "success": true,
  "message": "Video saved successfully",
  "data": {
    "asset_id": "uuid",
    "video_url": "https://oss.example.com/permanent_video.mp4",
    "preview_url": "https://example.com/preview.jpg",
    "oss_object_key": "video/user_id/asset_id.mp4",
    "work_id": "work-uuid"
  },
  "count": 1
}
```

**说明**: 此接口会将临时视频 URL 下载到 OSS 永久存储，并创建资产记录

---

### 5. 健康检查

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
| `works` | 作品表（新增 `work_type` 字段） |
| `chapters` | 章节表 |
| `shots` | 镜头表（v2.4 新增） |

### MongoDB 数据库

**数据库名**: `narloom`

#### 集合结构

| 集合名 | 说明 | 索引 |
|--------|------|------|
| `asset_data` | 资产详细数据 | `asset_id` (唯一) |
| `work_details` | 作品详细信息（已弃用） | `work_id` (唯一), 复合索引 |
| `novel_details` | 小说作品详细信息（v2.4 新增） | `work_id` (唯一), 复合索引 |
| `anime_details` | 动画作品详细信息（v2.4 新增） | `work_id` (唯一), 复合索引 |
| `shot_details` | 镜头详细信息（v2.4 新增） | `shot_id` (唯一), `work_id` 索引 |
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
MYSQL_TABLE_NOVELS=novels
MYSQL_TABLE_ANIME=anime

# MongoDB 配置
MONGO_URI=mongodb://localhost:27017/
MONGO_DB=narloom
MONGO_ASSET_DATA_COLLECTION=asset_data
MONGO_WORK_DETAILS_COLLECTION=work_details
MONGO_NOVEL_DETAILS_COLLECTION=novel_details
MONGO_ANIME_DETAILS_COLLECTION=anime_details
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

### v2.6 (2026-04-07) - 架构重构

- **目录结构重构**
  - `db/` 目录上移至项目根层级，与 `services/` 平级
  - 移除 `business/` 文件夹
  - `anime_service.py` 和 `video_generation_service.py` 保留在 `services/` 目录下

- **文件命名规范化**
  - `db/` 目录下所有文件去掉 `_service` 后缀
  - `user_service.py` → `user.py`
  - `asset_service.py` → `asset.py`
  - `work_service.py` → `work.py`
  - `novel_service.py` → `novel.py`
  - `anime_service.py` → `anime.py`
  - `mongo_asset_service.py` → `mongo_asset.py`
  - `mongo_work_service.py` → `mongo_work.py`
  - `mongo_novel_service.py` → `mongo_novel.py`
  - `mongo_anime_service.py` → `mongo_anime.py`

- **Import 路径更新**
  - 路由层引用 db 层：`from db import xxx_service`
  - 路由层引用 services 层：`from services import xxx_service`
  - services 引用 db: `from db import xxx_service`
  - db 引用 base_service: `from services.base_service import BaseService`

### v2.5 (2026-04-07) - 模块重构
- **章节模块重命名**: `Chapter` → `Novel`
  - 路由变更：`/rest/v1/chapter` → `/rest/v1/novel`
  - 数据库表变更：`chapters` → `novels`
  - 接口变更：
    - `POST /createChapter` → `POST /createNovel`
    - `POST /updateChapterById` → `POST /updateNovelById`
    - `GET /getChapterByNovelId` → `GET /getNovelByWorkId`
    - `POST /deleteChapterById` → `POST /deleteNovelById`
  - 响应字段变更：`chapter_id` → `novel_id`, `chapter_number` → `novel_number`, `chapter_title` → `novel_title`

- **镜头模块重命名**: `Shots` → `Anime`
  - 路由变更：`/rest/v1/shots` → `/rest/v1/anime`
  - 数据库表变更：`shots` → `anime`
  - MongoDB 集合变更：`shot_details` → `anime_details`
  - 接口变更：
    - `POST /createShot` → `POST /createAnime`
    - `GET /getShotsByWorkId` → `GET /getAnimesByWorkId`
    - `POST /generateAnime` → `POST /generateVideo`
    - `POST /generateMultiImageAnime` → `POST /generateMultiImageVideo`
    - `GET /getShotDetails` → `GET /getAnimeDetails`
  - 响应字段变更：`shot_id` → `anime_id`, `shot_number` → `anime_number`

- **服务层重构**
  - `ChapterService` → `NovelService`
  - `ShotService` → `AnimeService`
  - `ShotDetailsService` → `AnimeDetailsService`

### v2.4 (2026-04-07)
- **新增 Shots 模块** (`/rest/v1/shots`)
  - 新增 `shots` MySQL 表存储镜头信息
  - 新增 `shot_details` MongoDB 集合存储每个镜头的资产列表
  - 镜头 (Shot) 是动画作品的基本组成单位，一个 anime 类型的 work 由多个 shots 组成
- **新增 work_type 字段**
  - `works` 表新增 `work_type` 字段，支持 `novel`(小说) 和 `anime`(动画)
  - `novel` 类型作品使用 `novel_details` MongoDB 集合
  - `anime` 类型作品使用 `anime_details` MongoDB 集合
- **MongoDB 集合拆分**
  - 原 `work_details` 拆分为 `novel_details` 和 `anime_details`
  - `novel_details`: 继承原 `work_details` 功能，记录 `asset_ids` 和 `chapter_ids`
  - `anime_details`: 记录 `shots_ids` 列表
- **Shots 模块接口**
  - `POST /createShot` - 创建镜头
  - `GET /getShotsByWorkId` - 获取镜头列表
  - `POST /generateAnime` - 为镜头生成动画
  - `POST /generateMultiImageAnime` - 多张图片生成动画
  - `POST /confirm` - 确认保存视频到镜头
  - `GET /getShotDetails` - 获取镜头详情
- **Anime 模块迁移**
  - Anime 模块原有接口保留用于向后兼容
  - 建议新使用 `/rest/v1/shots` 路径下的接口
  - 新增 `shot_id` 参数支持镜头关联

### v2.3 (2026-03-31)
- 新增 `frame_mode` 参数支持单帧/首尾帧动画生成
  - `single`: 单张图片作为首帧生成动画（默认）
  - `start_end`: 两张图片作为首尾帧生成动画
- 新增首帧图片参数：`first_frame_asset_id`, `first_frame_oss_object_key`, `first_frame_picture`
- 新增尾帧图片参数：`last_frame_asset_id`, `last_frame_oss_object_key`, `last_frame_picture`
- 首帧和尾帧参数平级，都在 request 层级，不在 `parameters` 内
- 更新 `/generateAnime` 接口文档
- 更新 `/generateMultiImageAnime` 接口文档

### v2.2 (2026-03-31)
- 新增 `/generateMultiImageAnime` - 支持多张图片依次生成动画并合并
- 完善 Asset 模块接口文档
- 完善 Work 模块接口文档
- 完善 Chapter 模块接口文档
- 新增 `_poll_task_status` 方法支持视频任务轮询
- 新增 `_call_video_generation_api_for_merge` 方法支持视频合并

### v2.1 (2026-03-24)
- 拆分 Picture 和 Anime 为两个独立模块
- Picture 模块路由：`/rest/v1/picture`
- Anime 模块路由：`/rest/v1/anime`
- 新增 `/generateAnime` - 生成动画 (支持自动创建会话)
- 新增 `/chat` - 多轮对话交互
- 新增 `/confirm` - 确认保存视频
- 移除 `analyze` 模式
- 新增 `conversation_history` MongoDB 集合
