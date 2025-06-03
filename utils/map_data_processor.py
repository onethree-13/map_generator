# MIT License
#
# Copyright (c) 2024 Map Generator
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import json
import base64
import time
import re
from openai import OpenAI
from .geo_service import create_geocoding_service
from config import get_config
from .data_manager import clean_text, clean_tags, clean_url


def create_openai_client(api_key: str):
    """创建OpenAI客户端"""
    base_url = get_config(
        "OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    return OpenAI(
        api_key=api_key,
        base_url=base_url,
    )


class MapDataProcessor:
    """地图数据处理器 - 负责AI相关的数据处理功能"""
    
    def __init__(self):
        self.extracted_text = ""
        self.json_data = None
        self.confirmed_data = []
        self.geo_service = None
        self.openai_client = None
        self.current_map_service = get_config("DEFAULT_MAP_SERVICE", "amap")

    def initialize_geo_service(self, api_key: str, service_type: str = None):
        """初始化地理编码服务"""
        if service_type is None:
            service_type = self.current_map_service
        
        self.current_map_service = service_type
        self.geo_service = create_geocoding_service(api_key, service_type)

    def get_current_map_service_info(self):
        """获取当前地图服务信息"""
        if self.geo_service:
            return self.geo_service.get_service_info()
        return {
            "service_type": self.current_map_service,
            "service_name": "未初始化",
            "base_url": ""
        }

    def initialize_openai_client(self, api_key: str):
        """初始化OpenAI客户端"""
        self.openai_client = create_openai_client(api_key)

    def encode_image(self, image_file):
        """将图片编码为base64"""
        return base64.b64encode(image_file.read()).decode("utf-8")

    def process_text_input(self, text_content: str):
        """处理直接文本输入"""
        if not text_content.strip():
            raise ValueError("请输入要处理的文本内容")

        self.extracted_text = clean_text(text_content)
        return self.extracted_text

    def download_image_from_url(self, image_url: str):
        """从URL下载图片"""
        try:
            import requests
            from PIL import Image
            import io

            # 下载图片
            response = requests.get(image_url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()

            # 验证是否为图片
            image = Image.open(io.BytesIO(response.content))
            image.verify()  # 验证图片完整性

            # 重新读取图片（verify后需要重新打开）
            image = Image.open(io.BytesIO(response.content))

            # 转换为RGB模式（如果需要）
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')

            # 转换为字节流
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            return img_byte_arr, image

        except requests.exceptions.RequestException as e:
            raise ValueError(f"图片下载失败: {str(e)}")
        except Exception as e:
            raise ValueError(f"图片处理失败: {str(e)}")

    def extract_text_from_url(self, image_url: str, progress_placeholder):
        """从图片URL提取文字"""
        if not self.openai_client:
            raise ValueError("OpenAI客户端未初始化，请检查通义千问API密钥配置")

        progress_placeholder.text("正在下载图片...")
        img_stream, img_pil = self.download_image_from_url(image_url)

        progress_placeholder.text("正在编码图片...")
        base64_image = base64.b64encode(img_stream.read()).decode("utf-8")

        progress_placeholder.text("正在分析图片...")
        completion = self.openai_client.chat.completions.create(
            model="qwen-vl-max-latest",
            messages=[
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "You are a helpful assistant specialized in OCR and text extraction."}]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                        },
                        {"type": "text", "text": "请详细提取图片中的所有文字信息，包括地点名称、地址、电话号码、网站信息、营业时间、标签等。请保持原始格式和结构。"},
                    ],
                }
            ],
            stream=True,
        )

        full_content = ""
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                # 只显示最后5行
                lines = full_content.split('\n')
                display_lines = lines[-5:] if len(lines) > 5 else lines
                display_content = '\n'.join(display_lines)
                progress_placeholder.text(f"正在提取文字...\n{display_content}")
                time.sleep(0.05)

        self.extracted_text = full_content
        return full_content, img_pil

    def extract_text_from_image(self, image_file, progress_placeholder):
        """从上传的图片文件提取文字（流式返回）"""
        if not self.openai_client:
            raise ValueError("OpenAI客户端未初始化，请检查通义千问API密钥配置")

        base64_image = self.encode_image(image_file)

        completion = self.openai_client.chat.completions.create(
            model="qwen-vl-max-latest",
            messages=[
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "You are a helpful assistant specialized in OCR and text extraction."}]
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                        },
                        {"type": "text", "text": "请详细提取图片中的所有文字信息，包括地点名称、地址、电话号码、网站信息、营业时间、标签等。请保持原始格式和结构。"},
                    ],
                }
            ],
            stream=True,
        )

        full_content = ""
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                # 只显示最后5行
                lines = full_content.split('\n')
                display_lines = lines[-5:] if len(lines) > 5 else lines
                display_content = '\n'.join(display_lines)
                progress_placeholder.text(f"正在提取文字...\n{display_content}")
                time.sleep(0.05)

        self.extracted_text = full_content
        return full_content

    def generate_json_structure(self, extracted_text, custom_prompt="", progress_placeholder=None):
        """步骤2: 将提取的文字整理成JSON格式（支持流式输出）"""
        if not self.openai_client:
            raise ValueError("OpenAI客户端未初始化，请检查通义千问API密钥配置")

        # 构建系统消息，如果有自定义prompt则添加到系统消息中
        system_content = """你是一个专业的数据整理专家，擅长将非结构化文本转换为结构化JSON数据。
你需要仔细分析文本，识别出所有地点、商家信息，并正确分类各种信息类型。"""

        if custom_prompt.strip():
            system_content += f"\n\n**用户额外要求：**\n{custom_prompt.strip()}"

        completion = self.openai_client.chat.completions.create(
            model="qwen-max-latest",
            messages=[
                {
                    "role": "system",
                    "content": system_content
                },
                {
                    "role": "user",
                    "content": f"""
请将以下提取的文字信息整理成JSON格式，要求：

1. 仔细识别出所有地点、商家或机构信息
2. 正确分类各种信息（名称、地址、电话、网站等）
3. 只有确实存在的信息才填入对应字段，不存在的属性请不要包含该键值对
4. 电话号码请保持原格式
5. 如果有多个地点，请分别列出
6. 若 custom_prompt 未指定标签，则输出 tags 为空列表
7. 确保输出有效的JSON格式

提取的文字内容：
{extracted_text}

请按照以下格式输出：
{{
  "data": [
    {{
      "name": "地点或商家名称",
      "address": "具体地址信息", 
      "phone": "电话号码",
      "webName": "网站/视频/公众号",
      "webLink": "网站链接或相关URL",
      "intro": "相关描述或简介信息",
      "tags": ["相关标签", "类别"],
      "center": {{"lat": 0, "lng": 0}}
    }}
  ]
}}

注意：只输出JSON，不要包含其他解释文字。如果无法识别任何有效信息，请输出空的data数组。
"""
                }
            ],
            stream=True,
        )

        full_content = ""
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                if progress_placeholder:
                    # 只显示最后5行
                    lines = full_content.split('\n')
                    display_lines = lines[-5:] if len(lines) > 5 else lines
                    display_content = '\n'.join(display_lines)
                    progress_placeholder.text(f"正在生成JSON结构...\n{display_content}")
                    time.sleep(0.05)

        try:
            # 尝试解析JSON
            self.json_data = json.loads(full_content)

            # 清理JSON数据中的文本
            if self.json_data and 'data' in self.json_data:
                for item in self.json_data['data']:
                    if 'name' in item:
                        item['name'] = clean_text(item['name'])
                    if 'address' in item:
                        item['address'] = clean_text(item['address'])
                    if 'phone' in item:
                        item['phone'] = clean_text(item['phone'])
                    if 'webName' in item:
                        item['webName'] = clean_text(item['webName'])
                    if 'webLink' in item:
                        item['webLink'] = clean_url(item['webLink'])
                    if 'intro' in item:
                        item['intro'] = clean_text(item['intro'])
                    if 'tags' in item:
                        item['tags'] = clean_tags(item['tags'])

            return self.json_data
        except json.JSONDecodeError:
            # 如果解析失败，尝试提取JSON部分
            json_match = re.search(r'\{.*\}', full_content, re.DOTALL)
            if json_match:
                try:
                    self.json_data = json.loads(json_match.group())
                    return self.json_data
                except:
                    pass
            return None

    def get_coordinates_with_progress(self, progress_callback=None):
        """步骤4: 获取地址的经纬度信息（带进度显示）"""
        # 注意：这个方法已经被弃用，现在由tab直接处理批量坐标获取
        # 保留此方法仅为兼容性
        if progress_callback:
            progress_callback("批量坐标获取功能已移至坐标管理页面")

    def ai_edit_json_data(self, user_instruction: str, progress_placeholder=None):
        """使用AI根据用户指令编辑JSON数据（支持流式输出）"""
        if not self.openai_client:
            raise ValueError("OpenAI客户端未初始化，请检查通义千问API密钥配置")
        
        if not self.json_data:
            raise ValueError("暂无数据可编辑")

        current_data = json.dumps(self.json_data, ensure_ascii=False, indent=2)
        
        completion = self.openai_client.chat.completions.create(
            model="qwen-max-latest",
            messages=[
                {
                    "role": "system",
                    "content": """你是一个专业的JSON数据编辑助手。用户会给你当前的JSON数据和编辑指令，你需要根据指令修改数据并返回完整的JSON。

要求：
1. 严格按照指令修改数据
2. 保持JSON的结构完整性
3. 只输出修改后的完整JSON，不要添加任何解释
4. 确保所有字段的数据类型正确
5. 如果需要清理文本，请去除多余空格和特殊字符
6. 坐标信息格式为 {"lat": 纬度, "lng": 经度}
"""
                },
                {
                    "role": "user", 
                    "content": f"""当前JSON数据：
{current_data}

用户指令：{user_instruction}

请根据指令修改数据并返回完整的JSON。"""
                }
            ],
            stream=True,
        )

        full_content = ""
        for chunk in completion:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                if progress_placeholder:
                    # 只显示最后5行
                    lines = full_content.split('\n')
                    display_lines = lines[-5:] if len(lines) > 5 else lines
                    display_content = '\n'.join(display_lines)
                    progress_placeholder.text(f"正在编辑JSON数据...\n{display_content}")
                    time.sleep(0.05)

        try:
            # 尝试解析JSON
            edited_data = json.loads(full_content)
            
            # 验证数据结构
            if "data" not in edited_data:
                raise ValueError("返回的JSON缺少data字段")
            
            # 清理编辑后的数据
            if edited_data and 'data' in edited_data:
                for item in edited_data['data']:
                    if 'name' in item:
                        item['name'] = clean_text(item['name'])
                    if 'address' in item:
                        item['address'] = clean_text(item['address'])
                    if 'phone' in item:
                        item['phone'] = clean_text(item['phone'])
                    if 'webName' in item:
                        item['webName'] = clean_text(item['webName'])
                    if 'webLink' in item:
                        item['webLink'] = clean_url(item['webLink'])
                    if 'intro' in item:
                        item['intro'] = clean_text(item['intro'])
                    if 'tags' in item:
                        item['tags'] = clean_tags(item['tags'])
                        
            self.json_data = edited_data
            return edited_data
            
        except json.JSONDecodeError:
            # 如果解析失败，尝试提取JSON部分
            json_match = re.search(r'\{.*\}', full_content, re.DOTALL)
            if json_match:
                try:
                    edited_data = json.loads(json_match.group())
                    self.json_data = edited_data
                    return edited_data
                except:
                    pass
            raise ValueError("AI返回的内容不是有效的JSON格式")

    def ai_filter_tags(self, instruction: str, all_tags: list, progress_placeholder=None):
        """使用AI根据指令智能筛选标签"""
        if not self.openai_client:
            # 如果没有AI客户端，回退到简单的关键词匹配
            return self._fallback_filter_tags(instruction, all_tags)
        
        if not all_tags:
            return []
        
        try:
            # 构建提示词
            tags_text = ", ".join(all_tags)
            
            completion = self.openai_client.chat.completions.create(
                model="qwen-max-latest",
                messages=[
                    {
                        "role": "system",
                        "content": """你是一个专业的标签分类助手。用户会给你一个指令和一些标签，你需要根据指令筛选出相关的标签。

要求：
1. 仔细理解用户的筛选指令
2. 从给定的标签列表中找出符合条件的标签
3. 返回结果应该是一个JSON数组，包含筛选出的标签
4. 如果没有找到符合条件的标签，返回空数组
5. 只返回JSON数组，不要添加任何解释

示例：
- 指令："餐厅相关的标签" -> ["中餐", "西餐", "火锅", "快餐"]
- 指令："购物相关的标签" -> ["商场", "超市", "便利店"]
"""
                    },
                    {
                        "role": "user",
                        "content": f"""筛选指令：{instruction}

可选标签列表：{tags_text}

请从上述标签中筛选出符合指令的标签，以JSON数组格式返回。"""
                    }
                ],
                stream=True,
            )

            full_content = ""
            for chunk in completion:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_content += content
                    if progress_placeholder:
                        progress_placeholder.text(f"AI正在筛选标签...")
                        time.sleep(0.01)

            try:
                # 尝试解析JSON
                filtered_tags = json.loads(full_content)
                
                # 验证返回的是列表
                if isinstance(filtered_tags, list):
                    # 确保返回的标签都在原始列表中
                    valid_tags = [tag for tag in filtered_tags if tag in all_tags]
                    return valid_tags
                else:
                    # 如果不是列表，尝试从文本中提取
                    return self._extract_tags_from_text(full_content, all_tags)
                    
            except json.JSONDecodeError:
                # 如果解析失败，尝试从文本中提取标签
                return self._extract_tags_from_text(full_content, all_tags)
                
        except Exception as e:
            # AI调用失败时，回退到简单匹配
            if progress_placeholder:
                progress_placeholder.text(f"AI调用失败，使用关键词匹配...")
            return self._fallback_filter_tags(instruction, all_tags)

    def _extract_tags_from_text(self, text: str, all_tags: list):
        """从AI返回的文本中提取标签"""
        extracted_tags = []
        text_lower = text.lower()
        
        for tag in all_tags:
            if tag.lower() in text_lower:
                extracted_tags.append(tag)
        
        return extracted_tags

    def _fallback_filter_tags(self, instruction: str, all_tags: list):
        """关键词匹配回退方案"""
        filtered_tags = []
        instruction_lower = instruction.lower()
        
        # 定义关键词映射
        keyword_mappings = {
            "餐厅": ["餐", "食", "饭", "厅", "菜", "料理"],
            "餐饮": ["餐", "食", "饭", "厅", "菜", "料理", "茶", "咖啡", "酒"],
            "咖啡": ["咖啡", "cafe", "coffee"],
            "购物": ["购", "商", "店", "市场", "超市", "商场", "商店"],
            "娱乐": ["娱乐", "游戏", "影院", "KTV", "酒吧", "娱", "乐"],
            "医疗": ["医", "院", "诊所", "药店", "健康"],
            "教育": ["学", "校", "教育", "培训", "大学"],
            "交通": ["地铁", "公交", "车站", "机场", "交通"],
            "酒店": ["酒店", "旅馆", "宾馆", "住宿"],
            "银行": ["银行", "ATM", "金融"],
            "服务": ["服务", "维修", "理发", "美容"]
        }
        
        # 根据指令中的关键词筛选标签
        for category, keywords in keyword_mappings.items():
            if category in instruction_lower:
                for tag in all_tags:
                    if any(keyword in tag for keyword in keywords):
                        if tag not in filtered_tags:
                            filtered_tags.append(tag)
        
        # 如果没有匹配到预定义类别，尝试直接关键词匹配
        if not filtered_tags:
            # 提取指令中的可能关键词
            words = instruction_lower.replace("筛选", "").replace("找出", "").replace("显示", "").replace("相关", "").replace("的", "").replace("标签", "").strip()
            potential_keywords = [word.strip() for word in words.split() if len(word.strip()) > 1]
            
            for tag in all_tags:
                for keyword in potential_keywords:
                    if keyword in tag.lower():
                        if tag not in filtered_tags:
                            filtered_tags.append(tag)
        
        return filtered_tags 