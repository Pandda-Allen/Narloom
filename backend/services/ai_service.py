import os
import json
import requests
from typing import Dict, Any, Optional, List
from flask import current_app
import openai
from openai import OpenAI

class AIService:
    """AI服务处理类"""
    
    def __init__(self, app=None):
        self.client = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化AI服务"""
        self.app = app
        
        # 根据配置选择AI模型
        ai_type = app.config.get('AI_MODEL_TYPE', 'openai').lower()
        
        if ai_type == 'openai':
            self._init_openai(app)
        elif ai_type == 'claude':
            self._init_claude(app)
        else:
            current_app.logger.warning(f"不支持的AI类型: {ai_type}")
    
    def _init_openai(self, app):
        """初始化OpenAI客户端"""
        api_key = app.config.get('OPENAI_API_KEY')
        base_url = app.config.get('OPENAI_BASE_URL')
        
        if not api_key:
            current_app.logger.warning("OpenAI API密钥未配置")
            return
        
        try:
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            current_app.logger.info("OpenAI客户端初始化成功")
        except Exception as e:
            current_app.logger.error(f"OpenAI客户端初始化失败: {str(e)}")
    
    def _init_claude(self, app):
        """初始化Claude客户端（如果需要）"""
        # 这里可以添加Claude或其他AI模型的初始化逻辑
        pass
    
    def enhance_content(self, content: str, style: str = "优美流畅") -> Dict[str, Any]:
        """
        美化小说内容
        
        Args:
            content: 原始小说内容
            style: 美化风格
            
        Returns:
            包含美化后内容的字典
        """
        system_prompt = f"""你是一位专业的文学编辑，擅长将小说内容美化为{style}的风格。
        请对以下小说内容进行美化润色，保持原意不变，但使其更加生动、优美、富有文学性。"""
        
        return self._call_ai_model(system_prompt, content, "content_enhanced")
    
    def refine_content(self, content: str, target_length: str = "简洁") -> Dict[str, Any]:
        """
        提炼小说内容
        
        Args:
            content: 原始小说内容
            target_length: 目标长度（简洁/中等/详细）
            
        Returns:
            包含提炼后内容的字典
        """
        length_map = {
            "简洁": "约100-200字",
            "中等": "约300-500字",
            "详细": "约800-1000字"
        }
        
        system_prompt = f"""你是一位专业的文学总结专家，擅长提炼小说核心内容。
        请将以下小说内容提炼为{length_map.get(target_length, "简洁")}的版本，保留核心情节和关键信息。"""
        
        return self._call_ai_model(system_prompt, content, "content_refined")
    
    def extract_key_info(self, content: str) -> Dict[str, Any]:
        """
        提取关键信息
        
        Args:
            content: 小说内容
            
        Returns:
            包含关键信息的字典
        """
        system_prompt = """请从以下小说内容中提取关键信息，并以JSON格式返回：
        {
            "characters": ["角色1", "角色2", ...],
            "plot_points": ["情节要点1", "情节要点2", ...],
            "settings": ["场景1", "场景2", ...],
            "themes": ["主题1", "主题2", ...],
            "keywords": ["关键词1", "关键词2", ...]
        }
        请确保信息准确、简洁。"""
        
        return self._call_ai_model(system_prompt, content, "key_info", is_json=True)
    
    def analyze_style(self, content: str) -> Dict[str, Any]:
        """
        分析写作风格
        
        Args:
            content: 小说内容
            
        Returns:
            包含风格分析的字典
        """
        system_prompt = """请分析以下小说内容的写作风格，并以JSON格式返回：
        {
            "style_type": "风格类型",
            "tone": "情感基调",
            "pace": "节奏快慢",
            "vocabulary_level": "词汇水平",
            "description_intensity": "描写强度",
            "dialogue_ratio": "对话比例",
            "strengths": ["优点1", "优点2", ...],
            "suggestions": ["改进建议1", "改进建议2", ...]
        }"""
        
        return self._call_ai_model(system_prompt, content, "style_analysis", is_json=True)
    
    def generate_continuation(self, content: str, length: int = 200) -> Dict[str, Any]:
        """
        续写小说内容
        
        Args:
            content: 原始小说内容
            length: 续写长度（字数）
            
        Returns:
            包含续写内容的字典
        """
        system_prompt = f"""你是一位专业的小说作家，擅长延续故事的风格和情节。
        请根据以下小说内容，以相同风格续写约{length}字的内容。"""
        
        return self._call_ai_model(system_prompt, content, "continuation")
    
    def _call_ai_model(self, system_prompt: str, user_content: str, 
                       operation_type: str, is_json: bool = False) -> Dict[str, Any]:
        """
        调用AI模型的通用方法
        
        Args:
            system_prompt: 系统提示词
            user_content: 用户输入内容
            operation_type: 操作类型
            is_json: 是否期望JSON响应
            
        Returns:
            AI处理结果
        """
        if not self.client:
            return {
                "success": False,
                "error": "AI服务未初始化",
                "operation": operation_type
            }
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
            
            response_format = {"type": "json_object"} if is_json else None
            
            completion = self.client.chat.completions.create(
                model=current_app.config.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
                messages=messages,
                max_tokens=current_app.config.get('AI_MAX_TOKENS', 1000),
                temperature=current_app.config.get('AI_TEMPERATURE', 0.7),
                response_format=response_format
            )
            
            result_text = completion.choices[0].message.content
            
            if is_json:
                try:
                    result_data = json.loads(result_text)
                    return {
                        "success": True,
                        "operation": operation_type,
                        "data": result_data,
                        "usage": {
                            "prompt_tokens": completion.usage.prompt_tokens,
                            "completion_tokens": completion.usage.completion_tokens,
                            "total_tokens": completion.usage.total_tokens
                        }
                    }
                except json.JSONDecodeError:
                    # 如果JSON解析失败，返回原始文本
                    return {
                        "success": True,
                        "operation": operation_type,
                        "data": {"raw_output": result_text},
                        "usage": {
                            "prompt_tokens": completion.usage.prompt_tokens,
                            "completion_tokens": completion.usage.completion_tokens,
                            "total_tokens": completion.usage.total_tokens
                        }
                    }
            else:
                return {
                    "success": True,
                    "operation": operation_type,
                    "data": {"result": result_text},
                    "usage": {
                        "prompt_tokens": completion.usage.prompt_tokens,
                        "completion_tokens": completion.usage.completion_tokens,
                        "total_tokens": completion.usage.total_tokens
                    }
                }
                
        except Exception as e:
            current_app.logger.error(f"AI处理失败 ({operation_type}): {str(e)}")
            return {
                "success": False,
                "error": f"AI处理失败: {str(e)}",
                "operation": operation_type
            }

# 创建全局AI服务实例
ai_service = AIService()