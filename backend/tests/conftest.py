import os
import pytest
from flask import Flask
from unittest.mock import patch, Mock, MagicMock

@pytest.fixture
def app():
    """创建并配置一个新的Flask应用实例用于测试"""
    from app import create_app

    os.environ['TESTING'] = 'True'
    os.environ['SUPABASE_KEY'] = ''
    os.environ['SUPABASE_URL'] = ''

    app = create_app('testing')
    app.config.update({
        "TESTING": True,
        'DEBUG': True,
        'API_PREFIX': '/api/v1',
    })

    yield app