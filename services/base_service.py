"""
基础服务类，提供配置获取、日志记录等通用功能。
"""
import os
import logging
from typing import Optional
from flask import current_app


class BaseService:
    """所有服务的基类，提供通用功能"""

    def __init__(self):
        self._initialized = False

    def init_app(self, app):
        """初始化应用配置（子类应重写此方法）"""
        with app.app_context():
            self._initialize()

    def _initialize(self):
        """初始化服务（子类必须实现）"""
        raise NotImplementedError("Subclasses must implement _initialize")

    def _get_config(self, key: str, default=None):
        """从 Flask 配置或环境变量获取配置值，保持原始类型"""
        try:
            if current_app:
                value = current_app.config.get(key, default)
                if value is not None:
                    return value
        except RuntimeError:
            # current_app 不可用
            pass

        # 从环境变量获取
        env_value = os.getenv(key)
        if env_value is not None:
            # 尝试保持与默认值相同的类型
            if isinstance(default, int):
                try:
                    return int(env_value)
                except ValueError:
                    return default
            elif isinstance(default, float):
                try:
                    return float(env_value)
                except ValueError:
                    return default
            elif isinstance(default, bool):
                return env_value.lower() in ('true', '1', 'yes', 'on')
            else:
                return env_value
        return default

    def _log(self, message: str, level: str = 'info'):
        """统一日志输出，兼容 Flask 和非 Flask 环境"""
        try:
            if current_app:
                logger = current_app.logger
                getattr(logger, level)(message)
                return
        except (RuntimeError, AttributeError):
            pass

        # 回退到标准 logging
        logging.basicConfig(level=logging.INFO)
        getattr(logging, level)(message)

    def _ensure_initialized(self):
        """确保服务已初始化"""
        if not self._initialized:
            self._initialize()