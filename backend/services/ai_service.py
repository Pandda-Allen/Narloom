import os
import json
import requests
from typing import Dict, Any, Optional, List, Union
from flask import current_app, g
from datetime import datetime
import uuid
import time

class DeepSeekAIService:
    """DeepSeek AI服务类，处理DeepSeek API调用"""
    
    def __init__(self):
        self.api_base = "https://api.deepseek.com"
        self.api_key = None
        self.default_model = "deepseek-chat"
        self._initialized = False
        self._last_request_time = 0
        self._rate_limit_delay = 0.1  # 100ms between requests
        
        # DeepSeek支持的模型
        self.supported_models = {
            "deepseek-chat": {
                "id": "deepseek-chat",
                "name": "DeepSeek Chat",
                "description": "通用对话模型，适合各种文本生成任务",
                "max_tokens": 4096,
                "context_window": 8192,
                "supports_functions": False,
                "supports_streaming": True
            },
            "deepseek-coder": {
                "id": "deepseek-coder",
                "name": "DeepSeek Coder",
                "description": "代码生成专用模型",
                "max_tokens": 4096,
                "context_window": 8192,
                "supports_functions": False,
                "supports_streaming": True
            }
        }
        
    def init_app(self, app):
        """初始化DeepSeek AI服务"""
        with app.app_context():
            self.api_key = app.config.get('DEEPSEEK_API_KEY') or os.getenv('DEEPSEEK_API_KEY')
            self.api_base = app.config.get('DEEPSEEK_API_BASE') or os.getenv('DEEPSEEK_API_BASE', 'https://api.deepseek.com/v1')
            self.default_model = app.config.get('DEEPSEEK_DEFAULT_MODEL') or os.getenv('DEEPSEEK_DEFAULT_MODEL', 'deepseek-chat')
            
            if self.api_key:
                self._initialized = True
                current_app.logger.info(f"DeepSeek AI Service initialized successfully. Using model: {self.default_model}")
            else:
                current_app.logger.warning("DeepSeek API key not found. AI Service will not work.")
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理AI请求
        
        Args:
            request_data: 包含AI处理参数的字典
            
        Returns:
            Dict[str, Any]: 包含响应结果和元数据的字典
        """
        try:
            # 生成任务ID
            task_id = request_data.get('task_id', str(uuid.uuid4()))
            
            # 验证请求数据
            validated_data = self._validate_request(request_data)
            validated_data['task_id'] = task_id
            
            # 根据任务类型选择处理方法
            task_type = validated_data.get('task_type', 'chat')
            
            # 记录请求开始
            start_time = time.time()
            
            # 处理不同类型的任务
            if task_type == 'enhance':
                result = self._enhance_content(validated_data)
            elif task_type == 'abstract':
                result = self._abstract_content(validated_data)
            elif task_type == 'generate':
                result = self._generate_content(validated_data)
            elif task_type == 'translate':
                result = self._translate_content(validated_data)
            elif task_type == 'summarize':
                result = self._summarize_content(validated_data)
            elif task_type == 'rewrite':
                result = self._rewrite_content(validated_data)
            elif task_type == 'code':
                result = self._generate_code(validated_data)
            elif task_type == 'analysis':
                result = self._analyze_content(validated_data)
            else:  # 默认聊天模式
                result = self._chat_completion(validated_data)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 添加元数据
            result['processing_time'] = round(processing_time, 2)
            result['task_id'] = task_id
            result['timestamp'] = datetime.now().isoformat()
            
            # 记录成功日志
            current_app.logger.info(
                f"AI task completed: {task_id}, "
                f"model: {result.get('model_used', 'unknown')}, "
                f"tokens: {result.get('total_tokens', 0)}, "
                f"time: {processing_time:.2f}s"
            )
            
            return result
                
        except Exception as e:
            current_app.logger.error(f"Error in DeepSeek AI service: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "task_id": request_data.get('task_id', str(uuid.uuid4())),
                "timestamp": datetime.now().isoformat(),
                "suggestion": "请检查DeepSeek API密钥是否有效，或尝试稍后重试。"
            }
    
    def _chat_completion(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """调用DeepSeek聊天完成API"""
        if not self._initialized or not self.api_key:
            raise Exception("AI Service not initialized or API key missing")
        
        # 遵守速率限制
        self._respect_rate_limit()
        
        # 构建消息
        messages = self._build_messages(data)
        
        # 准备请求参数
        model = data.get('model', self.default_model)
        if model not in self.supported_models:
            current_app.logger.warning(f"Model {model} not in supported list, using default")
            model = self.default_model
        
        # 获取模型限制
        model_config = self.supported_models.get(model, {})
        max_tokens = model_config.get('max_tokens', 4096)
        
        # 构建请求体（DeepSeek API格式）
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": min(data.get('parameters', {}).get('max_tokens', 2000), max_tokens),
            "temperature": data.get('parameters', {}).get('temperature', 0.7),
            "top_p": data.get('parameters', {}).get('top_p', 0.9),
            "frequency_penalty": data.get('parameters', {}).get('frequency_penalty', 0),
            "presence_penalty": data.get('parameters', {}).get('presence_penalty', 0),
            "stream": False  # 暂时不支持流式响应
        }
        
        # 设置停止词
        stop_sequences = data.get('parameters', {}).get('stop', [])
        if stop_sequences:
            payload["stop"] = stop_sequences
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Flask-AI-Service/1.0"
        }
        
        current_app.logger.debug(f"DeepSeek request: model={model}, messages={len(messages)}")
        
        try:
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=data.get('timeout', 60)
            )
            
            current_app.logger.debug(f"DeepSeek response status: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.json() if response.content else {}
                error_msg = error_detail.get('error', {}).get('message', response.text)
                
                if response.status_code == 401:
                    raise Exception(f"DeepSeek API认证失败: {error_msg}")
                elif response.status_code == 429:
                    raise Exception(f"DeepSeek API速率限制: {error_msg}")
                elif response.status_code == 400:
                    raise Exception(f"DeepSeek API请求参数错误: {error_msg}")
                else:
                    raise Exception(f"DeepSeek API错误 {response.status_code}: {error_msg}")
            
            result = response.json()
            
            # 解析响应
            if 'choices' not in result or len(result['choices']) == 0:
                raise Exception("DeepSeek API返回了无效的响应格式")
            
            ai_response = result['choices'][0]['message']['content']
            
            # 记录使用情况
            usage = result.get('usage', {})
            
            return {
                "success": True,
                "result": ai_response,
                "model_used": model,
                "prompt_tokens": usage.get('prompt_tokens', 0),
                "completion_tokens": usage.get('completion_tokens', 0),
                "total_tokens": usage.get('total_tokens', 0),
                "finish_reason": result['choices'][0].get('finish_reason', 'stop')
            }
            
        except requests.exceptions.Timeout:
            raise Exception("DeepSeek API请求超时，请稍后重试")
        except requests.exceptions.ConnectionError:
            raise Exception("无法连接到DeepSeek API，请检查网络连接")
        except Exception as e:
            raise Exception(f"DeepSeek API请求失败: {str(e)}")
    
    def _enhance_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """增强/优化内容"""
        content = data['content']['user_prompt']
        
        # 构建增强提示
        constraints = data.get('constraints', {})
        language = constraints.get('language', 'zh-CN')
        tone = constraints.get('tone', '专业')
        
        language_map = {
            'zh-CN': '中文',
            'en-US': '英文',
            'ja-JP': '日文'
        }
        
        target_language = language_map.get(language, language)
        
        system_prompt = f"""你是一位专业的文本优化专家，请帮我优化以下内容：

优化要求：
1. 语言：请使用{target_language}进行优化
2. 风格：{tone}风格
3. 保持原文核心意思不变
4. 使表达更加清晰、流畅和专业

请直接输出优化后的内容，不要添加额外的解释或说明。

需要优化的内容："""
        
        data['content']['system_prompt'] = system_prompt
        data['model'] = data.get('model', 'deepseek-chat')
        
        return self._chat_completion(data)
    
    def _abstract_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """摘要生成"""
        content = data['content']['user_prompt']
        
        system_prompt = """你是一位专业的摘要生成助手，请为以下内容生成简洁明了的摘要：

摘要要求：
1. 提取核心信息和关键点
2. 保持原文主旨不变
3. 语言简洁，逻辑清晰
4. 如果是长文本，可以分点摘要

请直接输出摘要内容，不要添加额外的解释或说明。

需要摘要的内容："""
        
        data['content']['system_prompt'] = system_prompt
        data['parameters']['max_tokens'] = min(data.get('parameters', {}).get('max_tokens', 500), 1000)
        
        return self._chat_completion(data)
    
    def _generate_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """内容生成"""
        prompt = data['content']['user_prompt']
        
        system_prompt = f"""你是一位创意内容生成助手，请根据以下提示生成内容：

生成要求：
1. 语言：{data.get('constraints', {}).get('language', 'zh-CN')}
2. 风格：{data.get('constraints', {}).get('tone', '创意')}风格
3. 保持内容原创性和逻辑性
4. 如果涉及事实，请确保准确性

请直接输出生成的内容，不要添加额外的解释或说明。

生成提示："""
        
        data['content']['system_prompt'] = system_prompt
        data['model'] = data.get('model', 'deepseek-chat')
        
        return self._chat_completion(data)
    
    def _translate_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """翻译内容"""
        content = data['content']['user_prompt']
        target_lang = data.get('constraints', {}).get('language', 'en-US')
        
        language_map = {
            'zh-CN': '简体中文',
            'en-US': '英文',
            'ja-JP': '日文',
            'ko-KR': '韩文',
            'fr-FR': '法文',
            'es-ES': '西班牙文',
            'de-DE': '德文',
            'ru-RU': '俄文'
        }
        
        target_language = language_map.get(target_lang, target_lang)
        
        system_prompt = f"""你是一位专业的翻译专家，请将以下内容翻译成{target_language}：

翻译要求：
1. 准确传达原文意思
2. 语言自然流畅，符合目标语言的表达习惯
3. 专业术语翻译准确
4. 保持原文的格式和风格

请直接输出翻译结果，不要添加额外的解释或说明。

需要翻译的内容："""
        
        data['content']['system_prompt'] = system_prompt
        data['model'] = data.get('model', 'deepseek-chat')
        
        return self._chat_completion(data)
    
    def _summarize_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """总结内容（同摘要）"""
        return self._abstract_content(data)
    
    def _rewrite_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """重写内容"""
        content = data['content']['user_prompt']
        
        system_prompt = """你是一位专业的文本重写助手，请帮我重写以下内容：

重写要求：
1. 保持原文核心意思不变
2. 改进表达方式，使语言更加优美流畅
3. 优化句子结构，增强可读性
4. 可以适当调整段落结构

请直接输出重写后的内容，不要添加额外的解释或说明。

需要重写的内容："""
        
        data['content']['system_prompt'] = system_prompt
        data['model'] = data.get('model', 'deepseek-chat')
        
        return self._chat_completion(data)
    
    def _generate_code(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成代码"""
        prompt = data['content']['user_prompt']
        
        system_prompt = """你是一位专业的编程助手，请根据以下要求生成代码：

代码生成要求：
1. 代码规范，有清晰的注释
2. 遵循最佳实践和编程规范
3. 考虑性能和安全性
4. 如果需要，提供简要的使用说明
5. 使用合适的编程语言和框架

请直接输出代码，如果需要说明请在代码注释中添加。

编程要求："""
        
        data['content']['system_prompt'] = system_prompt
        data['model'] = data.get('model', 'deepseek-coder')  # 使用coder模型
        
        return self._chat_completion(data)
    
    def _analyze_content(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析内容"""
        content = data['content']['user_prompt']
        
        system_prompt = """你是一位专业的内容分析师，请分析以下内容：

请提供以下分析：
1. 内容主题和核心观点总结
2. 关键信息和数据提取
3. 情感倾向分析（正面/负面/中性）
4. 逻辑结构和论证分析
5. 改进建议或潜在问题

请以结构化的方式返回分析结果，可以使用列表、分类等方式。

需要分析的内容："""
        
        data['content']['system_prompt'] = system_prompt
        data['model'] = data.get('model', 'deepseek-chat')
        
        return self._chat_completion(data)
    
    def _build_messages(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """构建消息列表（DeepSeek API格式）"""
        messages = []
        
        # 添加系统提示
        system_prompt = data['content'].get('system_prompt', '')
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            # 默认系统提示
            messages.append({"role": "system", "content": "你是一个有用的人工智能助手，请根据用户的要求提供准确、有用的回答。"})
        
        # 添加上下文历史
        context = data['content'].get('context', [])
        for msg in context:
            messages.append({"role": msg.get('role', 'user'), "content": msg.get('content', '')})
        
        # 添加用户当前输入
        user_prompt = data['content'].get('user_prompt', '')
        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})
        
        return messages
    
    def _validate_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证和补全请求数据"""
        # 确保必要字段存在
        if 'content' not in data:
            data['content'] = {}
        
        # 兼容旧版参数名
        if 'prompt' in data and 'user_prompt' not in data['content']:
            data['content']['user_prompt'] = data.pop('prompt')
        
        if 'role' in data and 'system_prompt' not in data['content']:
            data['content']['system_prompt'] = f"你扮演{data.pop('role')}的角色。"
        
        # 确保用户输入不为空
        if 'user_prompt' not in data['content'] or not data['content']['user_prompt']:
            raise Exception("用户输入内容不能为空")
        
        # 设置默认参数
        if 'parameters' not in data:
            data['parameters'] = {}
        
        # DeepSeek API参数
        default_params = {
            'temperature': 0.7,
            'max_tokens': 2000,
            'top_p': 0.9,
            'frequency_penalty': 0,
            'presence_penalty': 0
        }
        
        for key, value in default_params.items():
            if key not in data['parameters']:
                data['parameters'][key] = value
        
        # 设置默认模型
        if 'model' not in data or not data['model']:
            data['model'] = self.default_model
        
        # 验证模型是否支持
        if data['model'] not in self.supported_models:
            current_app.logger.warning(f"Model {data['model']} is not in supported list, using default")
            data['model'] = self.default_model
        
        # 设置默认任务类型
        if 'task_type' not in data:
            data['task_type'] = 'chat'
        
        # 设置超时时间
        if 'timeout' not in data:
            data['timeout'] = 60
        
        return data
    
    def _respect_rate_limit(self):
        """遵守速率限制"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._rate_limit_delay:
            sleep_time = self._rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self._last_request_time = time.time()
    
    def get_supported_models(self) -> List[Dict[str, Any]]:
        """获取支持的AI模型列表"""
        models_list = []
        
        for model_id, config in self.supported_models.items():
            models_list.append({
                "id": model_id,
                "name": config.get('name', model_id),
                "description": config.get('description', ''),
                "max_tokens": config.get('max_tokens', 4096),
                "context_window": config.get('context_window', 8192)
            })
        
        return models_list
    
    def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        if not self._initialized:
            return {
                "status": "not_initialized",
                "message": "AI Service not initialized",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            # 尝试一个简单的API调用测试连接
            headers = {"Authorization": f"Bearer {self.api_key}"}
            response = requests.get(
                f"{self.api_base}/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "message": "DeepSeek API connection successful",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"DeepSeek API returned {response.status_code}",
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

# 全局实例
deepseek_ai_service = DeepSeekAIService()