# 代码框架与功能点分析报告

## 一、整体架构

### 1.1 技术栈

- **Web 框架**: Flask (应用工厂模式)
- **数据库**: MySQL + MongoDB 双数据库架构
- **存储**: 阿里云 OSS (图片 + 视频)
- **AI 服务**: DashScope API (Qwen AI 对话 + Wan2.6 视频生成)
- **认证**: JWT + Token Blacklist

### 1.2 目录结构

```
trial/
├── api/
│   └── routes/          # 路由层 (8 个模块)
│       ├── ai.py        # AI 对话
│       ├── anime.py     # 动画生成 (待废弃)
│       ├── asset.py     # 资产管理
│       ├── chapter.py   # 章节管理
│       ├── pictures.py  # 图片上传
│       ├── shots.py     # 镜头管理 (新)
│       ├── user.py      # 用户认证
│       └── work.py      # 作品管理
├── services/            # 服务层
│   ├── db/              # 数据库访问层
│   │   ├── base_service.py      # MySQL 基类
│   │   ├── user_service.py      # MySQL 用户表
│   │   ├── asset_service.py     # MySQL 资产表
│   │   ├── work_service.py      # MySQL 作品表
│   │   ├── chapter_service.py   # MySQL 章节表
│   │   ├── shot_service.py      # MySQL 镜头表 (新)
│   │   ├── mongo_service.py     # MongoDB 统一接口 (40+ 方法)
│   │   ├── mongo_asset_service.py
│   │   ├── mongo_work_service.py
│   │   ├── mongo_novel_service.py  # 新
│   │   ├── mongo_anime_service.py  # 新
│   │   └── mongo_shot_service.py   # 新
│   ├── storage/         # 存储服务
│   │   ├── oss_service.py       # OSS 统一接口
│   │   ├── picture_service.py   # 图片服务
│   │   └── video_service.py     # 视频服务
│   ├── ai_service.py            # Qwen AI 对话
│   ├── anime_service.py         # 动画生成逻辑
│   ├── video_generation_service.py  # 视频生成 API 调用
│   ├── jwt_service.py           # JWT 认证
│   ├── token_blacklist_service.py
│   └── conversation_history.py  # 对话历史管理
├── utils/
│   ├── constants.py     # 系统常量
│   ├── decorators.py    # 装饰器
│   ├── response_helper.py  # 响应格式化
│   └── general_helper.py   # 通用工具
├── app.py               # Flask 应用工厂
└── config.py            # 配置管理
```

---

## 二、数据库架构

### 2.1 MySQL 表结构

| 表名              | 用途       | 关键字段                                                |
| ----------------- | ---------- | ------------------------------------------------------- |
| `users`           | 用户信息   | user_id, username, email, password_hash, created_at     |
| `assets`          | 资产记录   | asset_id, user_id, work_id, asset_type, created_at      |
| `works`           | 作品信息   | work_id, author_id, title, genre, **work_type**, status |
| `chapters`        | 章节信息   | chapter_id, work_id, author_id, chapter_number          |
| `shots` (新)      | 镜头信息   | shot_id, work_id, author_id, shot_number, description   |
| `token_blacklist` | JWT 黑名单 | id, token, expires_at                                   |

### 2.2 MongoDB 集合

| 集合名                 | 用途          | 存储内容                                               |
| ---------------------- | ------------- | ------------------------------------------------------ |
| `asset_data`           | 资产详情      | oss_url, oss_object_key, original_filename, parameters |
| `work_details`         | 作品详情 (旧) | asset_ids[], chapter_ids[]                             |
| `novel_details` (新)   | 小说作品详情  | asset_ids[], chapter_ids[]                             |
| `anime_details` (新)   | 动画作品详情  | shots_ids[]                                            |
| `shot_details` (新)    | 镜头详情      | asset_ids[], video_assets[], picture_assets[]          |
| `conversation_history` | 对话历史      | session_id, user_id, messages[]                        |

---

## 三、路由模块功能点

### 3.1 路由注册

```python
# app.py 中注册
app.register_blueprint(user_bp)                         # 根路径
app.register_blueprint(asset_bp, url_prefix='/rest/v1/asset')
app.register_blueprint(work_bp, url_prefix='/rest/v1/work')
app.register_blueprint(chapter_bp, url_prefix='/rest/v1/chapter')
app.register_blueprint(ai_bp, url_prefix='/rest/v1/ai')
app.register_blueprint(picture_bp, url_prefix='/rest/v1/picture')
app.register_blueprint(anime_bp, url_prefix='/rest/v1/anime')
app.register_blueprint(shots_bp, url_prefix='/rest/v1/shots')
```

### 3.2 各模块 API 端点

#### User 模块 (user.py)

- `POST /register` - 用户注册
- `POST /login` - 用户登录
- `POST /logout` - 用户登出 (加入黑名单)
- `GET /getUserInfo` - 获取用户信息
- `POST /updateUserInfo` - 更新用户信息
- `GET /health` - 健康检查

#### Work 模块 (work.py)

- `POST /createWork` - 创建作品 (支持 work_type)
- `GET /getWorksByAuthorId` - 获取作者作品列表
- `GET /getWorkById` - 获取作品详情
- `POST /updateWork` - 更新作品信息
- `POST /deleteWork` - 删除作品
- `GET /health` - 健康检查

#### Chapter 模块 (chapter.py)

- `POST /createChapter` - 创建章节
- `GET /getChaptersByWorkId` - 获取章节列表
- `POST /updateChapter` - 更新章节
- `POST /deleteChapter` - 删除章节
- `GET /health` - 健康检查

#### Asset 模块 (asset.py)

- `POST /createAsset` - 创建资产记录
- `GET /getAssetsByUserId` - 获取用户资产
- `GET /getAssetsByWorkId` - 获取作品资产
- `GET /getAssetById` - 获取资产详情
- `POST /deleteAsset` - 删除资产
- `GET /health` - 健康检查

#### Pictures 模块 (pictures.py)

- `POST /uploadPicture` - 上传图片到 OSS
- `GET /fetchPictureByAssetId` - 获取图片 URL
- `GET /fetchPicturesByWorkId` - 获取作品图片列表
- `POST /deletePicture` - 删除图片
- `GET /health` - 健康检查

#### AI 模块 (ai.py)

- `POST /chat` - AI 对话 (支持上下文)
- `POST /analyze` - 图片分析
- `GET /health` - 健康检查

#### Anime 模块 (anime.py) - 待废弃

- `POST /generateAnime` - 生成动画
- `POST /chat` - 动画对话
- `POST /confirm` - 确认保存视频
- `GET /health` - 健康检查

#### Shots 模块 (shots.py) - 新

- `POST /createShot` - 创建镜头
- `GET /getShotsByWorkId` - 获取镜头列表
- `POST /generateAnime` - 为镜头生成动画
- `POST /generateMultiImageAnime` - 多图片动画生成
- `POST /confirm` - 确认保存到 shot_details
- `GET /getShotDetails` - 获取镜头详情
- `GET /health` - 健康检查

---

## 四、服务层依赖关系

```
┌─────────────────────────────────────────────────────────┐
│                    Route Layer                          │
│  (api/routes/ - 8 个模块)                                │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                   Service Layer                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │anime_service│  │video_generation│  │ oss_service   │  │
│  │             │← │_service       │  │               │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
│         │                  │                 │          │
│         └──────────────────┴─────────────────┘          │
│                            │                            │
│  ┌─────────────────────────────────────────────────┐    │
│  │           Database Service Layer                 │    │
│  │  ┌─────────────┐  ┌──────────────────────┐      │    │
│  │  │MySQLService │  │MongoService          │      │    │
│  │  │(user,asset, │  │(asset_data,work_,    │      │    │
│  │  │work,chapter,│  │novel_,anime_,shot_)  │      │    │
│  │  │shot)        │  │                      │      │    │
│  │  └─────────────┘  └──────────────────────┘      │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

### 关键服务依赖

1. **anime_service** → video_generation_service → DashScope Wan2.6 API
2. **shots.py** → anime_service → video_generation_service
3. **oss_service** → picture_service + video_service → 阿里云 OSS
4. **所有路由** → MySQLService / MongoService

---

## 五、核心业务流程

### 5.1 动画生成流程 (shots 模块)

```
1. 前端 → POST /generateAnime
   - 参数：user_id, work_id, shot_id, picture (或 asset_id/oss_object_key)

2. shots.py → _get_picture_source() 获取图片 URL
   - 优先级：asset_id → oss_object_key → picture 文件

3. shots.py → anime_service.generate_anime()
   - 临时传递 shot_id 和 work_id 到 parameters

4. anime_service → video_generation_service
   - 调用 DashScope Wan2.6 API

5. 生成成功后 → MongoService.add_asset_to_shot()
   - 保存到 shot_details 集合

6. 返回结果给前端
```

### 5.2 图片上传流程

```
1. 前端 → POST /uploadPicture (multipart/form-data)
2. pictures.py → oss_service.upload_picture()
3. oss_service → picture_service.upload() → 阿里云 OSS
4. 返回 oss_url 和 oss_object_key
```

### 5.3 JWT 认证流程

```
1. 用户登录 → jwt_service.generate_token()
2. 请求验证 → @jwt_required 装饰器
3. 登出 → token_blacklist_service.add_token()
```

---

## 六、待重构问题

### 6.1 架构问题

1. **anime_service 与 shots.py 职责不清**
   - anime_service 实际处理动画生成逻辑
   - shots.py 又重复了部分保存逻辑
   - 建议：anime_service 只保留视频生成，shots.py 负责完整的 shot 业务

2. **数据库服务层冗余**
   - mongo_service.py 有 40+ 方法，实际是各 detail_service 的包装
   - 建议：直接使用各 detail_service，减少中间层

3. **视频生成路径不统一**
   - anime.py → anime_service → video_generation_service
   - shots.py → anime_service → video_generation_service
   - 建议：统一为单一入口

### 6.2 代码质量问题

1. **错误处理不统一**
   - 部分端点返回 error_response
   - 部分端点抛出异常
   - 建议：统一错误处理机制

2. **参数验证分散**
   - 各路由手动验证 required_fields
   - 建议：使用装饰器或中间件统一处理

3. **日志记录不足**
   - 关键操作缺少审计日志
   - 建议：添加操作日志记录

---

## 七、重构建议

### 7.1 短期重构 (保持兼容性)

1. 完成 anime 模块到 shots 模块的迁移
2. 废弃 anime.py，保留路由重定向
3. 清理 work_details，使用 novel_details + anime_details

### 7.2 中期重构 (优化架构)

1. 统一视频生成入口
2. 精简数据库服务层
3. 添加统一的错误处理和日志记录

### 7.3 长期重构 (功能扩展)

1. 添加任务队列支持异步生成
2. 支持更多视频生成模型
3. 添加用户配额管理

---

## 八、关键文件清单

### 核心文件 (修改频率高)

- `services/anime_service.py` - 动画生成逻辑
- `services/db/mongo_anime_service.py` - 动画作品详情
- `services/db/mongo_shot_service.py` - 镜头详情
- `api/routes/shots.py` - 镜头 API

### 配置文件 (修改频率低)

- `config.py` - 应用配置
- `utils/constants.py` - 系统常量

### 文档文件

- `API.md` - API 文档
- `.claude/plans/drifting-knitting-pudding.md` - 重构计划

---

## 九、验证检查点

### 数据库初始化

- [ ] MySQL 表创建包含 work_type 字段
- [ ] MySQL shots 表正确创建
- [ ] MongoDB 集合正确初始化

### API 功能

- [ ] shots 模块 7 个端点正常工作
- [ ] anime 模块保持向后兼容
- [ ] work_type 参数正确传递

### 数据一致性

- [ ] 动画生成后保存到 shot_details
- [ ] work_type 与 detail 集合匹配
- [ ] asset_id 关联正确
