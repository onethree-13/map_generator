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
import streamlit as st
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
import re


def clean_text(text):
    """清理文本中的多余空格和换行符"""
    if not text or not isinstance(text, str):
        return ""

    # 去除首尾空格
    text = text.strip()

    # 将多个连续空格替换为单个空格
    text = re.sub(r' +', ' ', text)

    # 清理制表符和其他空白字符
    text = re.sub(r'[\t\r\f\v]+', ' ', text)

    # 规范化换行符，保留段落结构
    text = re.sub(r'\n +', '\n', text)  # 去除行首空格
    text = re.sub(r' +\n', '\n', text)  # 去除行尾空格
    text = re.sub(r'\n{3,}', '\n\n', text)  # 最多保留两个连续换行符

    return text


def clean_url(url):
    """清理和标准化URL"""
    if not url or not isinstance(url, str):
        return ""
    
    url = url.strip()
    if not url:
        return ""
    
    # 移除多余的空格和换行符
    url = re.sub(r'\s+', '', url)
    
    # 如果不是以http://或https://开头，尝试添加https://
    if url and not re.match(r'^https?://', url):
        # 检查是否是有效的域名格式
        if re.match(r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]\.[a-zA-Z]{2,}', url):
            url = 'https://' + url
        # 检查是否是www开头的域名
        elif url.startswith('www.'):
            url = 'https://' + url
    
    return url


def validate_url(url):
    """验证URL是否有效"""
    if not url:
        return True, ""  # 空URL是有效的
    
    # 基本URL格式验证
    url_pattern = r'^https?://[a-zA-Z0-9]([a-zA-Z0-9\-\.]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}([/?].*)?$'
    
    if not re.match(url_pattern, url):
        return False, "URL格式不正确，请确保包含有效的协议(http://或https://)和域名"
    
    return True, ""


def clean_tags(tags):
    """清理标签列表"""
    if not tags or not isinstance(tags, list):
        return []

    cleaned_tags = []
    for tag in tags:
        if isinstance(tag, str):
            clean_tag = clean_text(tag)
            if clean_tag:  # 只添加非空标签
                cleaned_tags.append(clean_tag)

    return cleaned_tags


class DataManager:
    """数据管理器，负责管理三个核心数据：extracted_text、saved_json、editing_json
    
    数据流向：
    1. extracted_text: 原始提取的文本
    2. saved_json: 确认过的数据（AI生成或人工编辑的最终版本）
    3. editing_json: AI编辑中的临时数据（可撤销、可保存到saved_json）
    
    核心原则：
    - saved_json 是数据的权威版本，所有读取操作默认从这里获取
    - editing_json 仅用于AI编辑过程中的临时存储
    - 只有明确的编辑操作才会使用 editing_json
    """
    
    def __init__(self):
        self.init_session_state()
    
    def init_session_state(self):
        """初始化session state中的数据结构"""
        # 核心数据1：提取的原始文本
        if 'extracted_text' not in st.session_state:
            st.session_state.extracted_text = ""
        
        # 核心数据2：已确认的JSON数据（权威版本）
        if 'saved_json' not in st.session_state:
            st.session_state.saved_json = self._create_empty_json()
        
        # 核心数据3：AI编辑中的临时JSON数据
        if 'editing_json' not in st.session_state:
            st.session_state.editing_json = self._create_empty_json()
        
        # 编辑状态标记
        if 'has_pending_edits' not in st.session_state:
            st.session_state.has_pending_edits = False
    
    def _create_empty_json(self) -> Dict[str, Any]:
        """创建空的JSON结构"""
        return {
            "name": "",
            "description": "",
            "origin": "",
            "filter": {
                "inclusive": {},
                "exclusive": {}
            },
            "data": []
        }
    
    def _create_empty_data_item(self) -> Dict[str, Any]:
        """创建空的数据项结构"""
        return {
            "name": "",
            "address": "",
            "phone": "",
            "webName": "",
            "webLink": "",
            "intro": "",
            "tags": [],
            "center": {
                "lat": 0,
                "lng": 0
            }
        }
    
    def _clean_data_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """清理单个数据项，确保符合规范"""
        cleaned_item = {"name": ""}  # name是必需的
        
        # 处理字符串字段 - 确保所有字段都存在，即使为空
        for field in ["name", "address", "phone", "webName", "intro"]:
            if field in item and item[field]:
                cleaned_item[field] = clean_text(str(item[field]))
            else:
                cleaned_item[field] = ""  # 确保字段存在
        
        # 特殊处理webLink字段 - 确保字段存在
        if "webLink" in item and item["webLink"]:
            cleaned_item["webLink"] = clean_url(str(item["webLink"]))
        else:
            cleaned_item["webLink"] = ""  # 确保字段存在，即使为空
        
        # 处理标签
        if "tags" in item:
            cleaned_item["tags"] = clean_tags(item["tags"])
        else:
            cleaned_item["tags"] = []
        
        # 处理坐标
        if "center" in item and isinstance(item["center"], dict):
            center = item["center"]
            cleaned_item["center"] = {
                "lat": float(center.get("lat", 0)),
                "lng": float(center.get("lng", 0))
            }
        else:
            cleaned_item["center"] = {"lat": 0, "lng": 0}
        
        return cleaned_item
    
    def _clean_json_structure(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """清理JSON结构，确保符合规范"""
        cleaned = self._create_empty_json()
        
        # 清理基本信息
        for field in ["name", "description", "origin"]:
            if field in json_data and json_data[field]:
                cleaned[field] = clean_text(str(json_data[field]))
        
        # 清理过滤器
        if "filter" in json_data and isinstance(json_data["filter"], dict):
            filter_data = json_data["filter"]
            if "inclusive" in filter_data and isinstance(filter_data["inclusive"], dict):
                cleaned["filter"]["inclusive"] = filter_data["inclusive"]
            if "exclusive" in filter_data and isinstance(filter_data["exclusive"], dict):
                cleaned["filter"]["exclusive"] = filter_data["exclusive"]
        
        # 清理数据项
        if "data" in json_data and isinstance(json_data["data"], list):
            cleaned["data"] = [self._clean_data_item(item) for item in json_data["data"]]
        
        return cleaned
    
    # ===== 提取文本管理 =====
    def set_extracted_text(self, text: str):
        """设置提取的文本"""
        st.session_state.extracted_text = clean_text(text)
    
    def get_extracted_text(self) -> str:
        """获取提取的文本"""
        return st.session_state.extracted_text
    
    def has_extracted_text(self) -> bool:
        """检查是否有提取的文本"""
        return bool(st.session_state.extracted_text.strip())
    
    def clear_extracted_text(self):
        """清空提取的文本"""
        st.session_state.extracted_text = ""
    
    # ===== 已确认JSON管理（权威数据源）=====
    def set_saved_json(self, json_data: Dict[str, Any]):
        """设置已确认的JSON数据"""
        st.session_state.saved_json = self._clean_json_structure(json_data)
        # 清除编辑状态
        st.session_state.has_pending_edits = False
    
    def get_saved_json(self) -> Dict[str, Any]:
        """获取已确认的JSON数据"""
        return st.session_state.saved_json
    
    def has_saved_json(self) -> bool:
        """检查是否有已确认的JSON数据"""
        return bool(st.session_state.saved_json.get("data"))
    
    def clear_saved_json(self):
        """清空已确认的JSON数据"""
        st.session_state.saved_json = self._create_empty_json()
        st.session_state.has_pending_edits = False
    
    # ===== AI编辑中JSON管理（临时数据）=====
    def set_editing_json(self, json_data: Dict[str, Any]):
        """设置AI编辑中的JSON数据"""
        st.session_state.editing_json = self._clean_json_structure(json_data)
        st.session_state.has_pending_edits = True
    
    def get_editing_json(self) -> Dict[str, Any]:
        """获取AI编辑中的JSON数据"""
        return st.session_state.editing_json
    
    def has_editing_json(self) -> bool:
        """检查是否有AI编辑中的JSON数据"""
        return bool(st.session_state.editing_json.get("data"))
    
    def clear_editing_json(self):
        """清空AI编辑中的JSON数据"""
        st.session_state.editing_json = self._create_empty_json()
        st.session_state.has_pending_edits = False
    
    def has_pending_edits(self) -> bool:
        """检查是否有待保存的编辑"""
        return st.session_state.get('has_pending_edits', False)
    
    def start_editing(self):
        """开始编辑：将saved_json复制到editing_json"""
        st.session_state.editing_json = json.loads(json.dumps(st.session_state.saved_json))
        st.session_state.has_pending_edits = False  # 刚开始编辑时没有变更
    
    def apply_edits(self):
        """应用编辑：将editing_json保存到saved_json"""
        st.session_state.saved_json = json.loads(json.dumps(st.session_state.editing_json))
        st.session_state.has_pending_edits = False
    
    def discard_edits(self):
        """丢弃编辑：清除editing_json并重置编辑状态"""
        st.session_state.editing_json = json.loads(json.dumps(st.session_state.saved_json))
        st.session_state.has_pending_edits = False
    
    # ===== 兼容性方法（保持向后兼容）=====
    def copy_saved_to_editing(self):
        """将已保存的JSON复制到编辑中的JSON（兼容性方法）"""
        self.start_editing()
    
    def save_editing_to_saved(self):
        """将编辑中的JSON覆盖到已保存的JSON（兼容性方法）"""
        self.apply_edits()
    
    # ===== JSON语法检查 =====
    def validate_json_syntax(self, json_str: str) -> Tuple[bool, str]:
        """检查JSON语法是否正确
        
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            json.loads(json_str)
            return True, ""
        except json.JSONDecodeError as e:
            return False, f"JSON语法错误：{str(e)}"
        except Exception as e:
            return False, f"未知错误：{str(e)}"
    
    def validate_json_structure(self, json_data: Dict[str, Any]) -> Tuple[bool, str]:
        """检查JSON结构是否符合规范
        
        Returns:
            Tuple[bool, str]: (是否有效, 错误信息)
        """
        try:
            # 检查顶级结构
            required_fields = ["name", "description", "origin", "filter", "data"]
            for field in required_fields:
                if field not in json_data:
                    return False, f"缺少必需字段：{field}"
            
            # 检查filter结构
            filter_data = json_data["filter"]
            if not isinstance(filter_data, dict):
                return False, "filter字段必须是对象"
            
            if "inclusive" not in filter_data or "exclusive" not in filter_data:
                return False, "filter必须包含inclusive和exclusive字段"
            
            if not isinstance(filter_data["inclusive"], dict) or not isinstance(filter_data["exclusive"], dict):
                return False, "inclusive和exclusive必须是对象"
            
            # 检查data结构
            data = json_data["data"]
            if not isinstance(data, list):
                return False, "data字段必须是数组"
            
            # 检查每个数据项
            for i, item in enumerate(data):
                if not isinstance(item, dict):
                    return False, f"数据项{i+1}必须是对象"
                
                if "name" not in item:
                    return False, f"数据项{i+1}缺少必需的name字段"
                
                # 检查center结构（如果存在）
                if "center" in item:
                    center = item["center"]
                    if not isinstance(center, dict):
                        return False, f"数据项{i+1}的center必须是对象"
                    
                    if "lat" in center and not isinstance(center["lat"], (int, float)):
                        return False, f"数据项{i+1}的center.lat必须是数字"
                    
                    if "lng" in center and not isinstance(center["lng"], (int, float)):
                        return False, f"数据项{i+1}的center.lng必须是数字"
                
                # 检查tags结构（如果存在）
                if "tags" in item and not isinstance(item["tags"], list):
                    return False, f"数据项{i+1}的tags必须是数组"
                
                # 验证webLink字段（如果存在）
                if "webLink" in item and item["webLink"]:
                    is_valid_url, url_error = validate_url(str(item["webLink"]))
                    if not is_valid_url:
                        return False, f"数据项{i+1}的webLink无效：{url_error}"
            
            return True, ""
        
        except Exception as e:
            return False, f"结构验证错误：{str(e)}"
    
    def validate_data_item(self, item: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """验证单个数据项的有效性
        
        Args:
            item: 要验证的数据项
            
        Returns:
            Tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []
        
        # 检查必需字段
        if not item.get("name", "").strip():
            errors.append("名称不能为空")
        
        # 验证webLink字段
        web_link = item.get("webLink", "")
        if web_link:
            is_valid_url, url_error = validate_url(web_link)
            if not is_valid_url:
                errors.append(f"网站链接格式错误：{url_error}")
        
        # 验证坐标
        center = item.get("center", {})
        if center:
            try:
                lat = float(center.get("lat", 0))
                lng = float(center.get("lng", 0))
                
                # 检查坐标范围
                if not (-90 <= lat <= 90):
                    errors.append("纬度必须在-90到90之间")
                if not (-180 <= lng <= 180):
                    errors.append("经度必须在-180到180之间")
            except (ValueError, TypeError):
                errors.append("坐标必须是有效的数字")
        
        return len(errors) == 0, errors
    
    # ===== 数据访问接口（默认从saved_json读取）=====
    def get_data_items(self, use_editing: bool = False) -> List[Dict[str, Any]]:
        """获取数据项列表
        
        Args:
            use_editing: 是否使用编辑中的数据，默认False（从saved_json读取）
        """
        json_data = st.session_state.editing_json if use_editing else st.session_state.saved_json
        return json_data.get("data", [])
    
    def get_map_info(self, use_editing: bool = False) -> Dict[str, Any]:
        """获取地图基本信息
        
        Args:
            use_editing: 是否使用编辑中的数据，默认False（从saved_json读取）
        """
        json_data = st.session_state.editing_json if use_editing else st.session_state.saved_json
        return {
            "name": json_data.get("name", ""),
            "description": json_data.get("description", ""),
            "origin": json_data.get("origin", ""),
            "filter": json_data.get("filter", {"inclusive": {}, "exclusive": {}})
        }
    
    # ===== 编辑中JSON的操作接口 =====
    def update_editing_basic_info(self, name: str = None, description: str = None, origin: str = None):
        """更新编辑中JSON的基本信息"""
        if name is not None:
            st.session_state.editing_json["name"] = clean_text(name)
            st.session_state.has_pending_edits = True
        if description is not None:
            st.session_state.editing_json["description"] = clean_text(description)
            st.session_state.has_pending_edits = True
        if origin is not None:
            st.session_state.editing_json["origin"] = clean_text(origin)
            st.session_state.has_pending_edits = True
    
    def get_editing_data_items(self) -> List[Dict[str, Any]]:
        """获取编辑中JSON的数据项列表"""
        return st.session_state.editing_json.get("data", [])
    
    def add_editing_data_item(self, item: Dict[str, Any]):
        """向编辑中JSON添加数据项"""
        cleaned_item = self._clean_data_item(item)
        st.session_state.editing_json["data"].append(cleaned_item)
        st.session_state.has_pending_edits = True
    
    def update_editing_data_item(self, index: int, item: Dict[str, Any]):
        """更新编辑中JSON的指定数据项"""
        data_items = st.session_state.editing_json["data"]
        if 0 <= index < len(data_items):
            data_items[index] = self._clean_data_item(item)
            st.session_state.has_pending_edits = True
    
    def remove_editing_data_item(self, index: int):
        """删除编辑中JSON的指定数据项"""
        data_items = st.session_state.editing_json["data"]
        if 0 <= index < len(data_items):
            data_items.pop(index)
            st.session_state.has_pending_edits = True
    
    def update_editing_filters(self, inclusive: Dict[str, List[str]] = None, exclusive: Dict[str, List[str]] = None):
        """更新编辑中JSON的过滤器"""
        if inclusive is not None:
            st.session_state.editing_json["filter"]["inclusive"] = inclusive
            st.session_state.has_pending_edits = True
        if exclusive is not None:
            st.session_state.editing_json["filter"]["exclusive"] = exclusive
            st.session_state.has_pending_edits = True
    
    # ===== 导出功能（从saved_json导出）=====
    def export_from_saved_json(self, remove_empty: bool = True, remove_zero_coords: bool = False) -> Dict[str, Any]:
        """直接从saved_json导出结果"""
        return self._prepare_export_data(st.session_state.saved_json, remove_empty, remove_zero_coords)
    
    def export_data_only_from_saved(self, remove_empty: bool = True, remove_zero_coords: bool = False) -> List[Dict[str, Any]]:
        """从saved_json导出仅数据部分"""
        exported = self._prepare_export_data(st.session_state.saved_json, remove_empty, remove_zero_coords)
        return exported.get("data", [])
    
    def _prepare_export_data(self, json_data: Dict[str, Any], remove_empty: bool, remove_zero_coords: bool) -> Dict[str, Any]:
        """准备导出数据"""
        result = json.loads(json.dumps(json_data))  # 深拷贝
        
        cleaned_data = []
        for item in result.get("data", []):
            cleaned_item = {}
            
            for key, value in item.items():
                # 清理数据
                if isinstance(value, str):
                    value = clean_text(value)
                elif isinstance(value, list):
                    value = clean_tags(value) if key == 'tags' else [
                        clean_text(v) if isinstance(v, str) else v for v in value]
                    # 过滤空值
                    value = [v for v in value if v]
                
                # 跳过空值（如果设置了移除空字段）
                if remove_empty and (not value or value == "" or value == []):
                    continue
                
                cleaned_item[key] = value
            
            # 跳过无效坐标的项目
            if remove_zero_coords:
                center = cleaned_item.get("center", {})
                if center.get("lat", 0) == 0 and center.get("lng", 0) == 0:
                    continue
            
            if cleaned_item:
                cleaned_data.append(cleaned_item)
        
        result["data"] = cleaned_data
        return result
    
    # ===== 数据统计和分析（默认从saved_json读取）=====
    def get_data_statistics(self, use_editing: bool = False) -> Dict[str, int]:
        """获取数据统计信息
        
        Args:
            use_editing: 是否使用编辑中的数据，默认False（从saved_json读取）
        """
        json_data = st.session_state.editing_json if use_editing else st.session_state.saved_json
        data_items = json_data.get("data", [])
        
        if not data_items:
            return {
                "total_locations": 0,
                "has_address": 0,
                "has_coordinates": 0,
                "has_phone": 0,
                "has_intro": 0,
                "has_name": 0,
                "has_tags": 0,
                "has_weblink": 0
            }
        
        total_locations = len(data_items)
        
        # 统计各种字段的有效数据数量
        has_name = sum(1 for item in data_items if item.get("name", "").strip())
        has_address = sum(1 for item in data_items if item.get("address", "").strip())
        has_coordinates = sum(1 for item in data_items
                              if item.get("center", {}).get("lat", 0) != 0 and
                              item.get("center", {}).get("lng", 0) != 0)
        has_phone = sum(1 for item in data_items if item.get("phone", "").strip())
        has_intro = sum(1 for item in data_items if item.get("intro", "").strip())
        has_tags = sum(1 for item in data_items if item.get("tags", []))
        has_weblink = sum(1 for item in data_items if item.get("webLink", "").strip())
        
        return {
            "total_locations": total_locations,
            "has_name": has_name,
            "has_address": has_address,
            "has_coordinates": has_coordinates,
            "has_phone": has_phone,
            "has_intro": has_intro,
            "has_tags": has_tags,
            "has_weblink": has_weblink
        }
    
    def get_all_tags(self, use_editing: bool = False) -> List[str]:
        """获取所有标签
        
        Args:
            use_editing: 是否使用编辑中的数据，默认False（从saved_json读取）
        """
        json_data = st.session_state.editing_json if use_editing else st.session_state.saved_json
        all_tags = set()
        
        # 从过滤器中获取标签
        for filter_type in ["inclusive", "exclusive"]:
            filter_data = json_data.get("filter", {}).get(filter_type, {})
            for category, tags in filter_data.items():
                if isinstance(tags, list):
                    all_tags.update(tags)
        
        # 从数据项中获取标签
        for item in json_data.get("data", []):
            tags = item.get("tags", [])
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, str) and tag.strip():
                        all_tags.add(tag.strip())
        
        return sorted(list(all_tags))
    
    # ===== 坐标管理（默认操作saved_json）=====
    def update_coordinates(self, index: int, lat: float, lng: float, use_editing: bool = False):
        """更新坐标
        
        Args:
            index: 数据项索引
            lat: 纬度
            lng: 经度
            use_editing: 是否更新编辑中的数据，默认False（更新saved_json）
        """
        json_data = st.session_state.editing_json if use_editing else st.session_state.saved_json
        data_items = json_data.get("data", [])
        
        if 0 <= index < len(data_items):
            data_items[index]["center"] = {"lat": lat, "lng": lng}
            if use_editing:
                st.session_state.has_pending_edits = True
    
    def get_coordinates_status(self, use_editing: bool = False) -> List[Dict[str, Any]]:
        """获取坐标状态信息
        
        Args:
            use_editing: 是否使用编辑中的数据，默认False（从saved_json读取）
        """
        json_data = st.session_state.editing_json if use_editing else st.session_state.saved_json
        coord_stats = []
        
        for i, item in enumerate(json_data.get("data", [])):
            name = clean_text(item.get('name', '未知地点'))
            address = clean_text(item.get('address', '无地址'))
            has_address = bool(address and address != '无地址')
            has_coords = bool(item.get('center', {}).get('lat', 0) != 0)
            
            coord_stats.append({
                "序号": i + 1,
                "名称": name if name else '未知地点',
                "地址": address if address else '无地址',
                "坐标状态": "✅ 已获取" if has_coords else ("⏳ 待获取" if has_address else "❌ 无地址")
            })
        
        return coord_stats
    
    # ===== 重置功能 =====
    def reset_all_data(self):
        """重置所有数据"""
        st.session_state.extracted_text = ""
        st.session_state.saved_json = self._create_empty_json()
        st.session_state.editing_json = self._create_empty_json()
        st.session_state.has_pending_edits = False
    
    def reset_saved_json(self):
        """重置已保存的JSON"""
        st.session_state.saved_json = self._create_empty_json()
        st.session_state.has_pending_edits = False
    
    def reset_editing_json(self):
        """重置编辑中的JSON"""
        st.session_state.editing_json = self._create_empty_json()
        st.session_state.has_pending_edits = False
    
    # ===== 智能建议功能（默认从saved_json读取）=====
    def generate_smart_suggestions(self, use_editing: bool = False) -> Dict[str, str]:
        """基于数据生成智能建议
        
        Args:
            use_editing: 是否使用编辑中的数据，默认False（从saved_json读取）
        """
        json_data = st.session_state.editing_json if use_editing else st.session_state.saved_json
        data_items = json_data.get("data", [])
        
        suggestions = {
            "name": "新地图",
            "description": "精选地点推荐地图",
            "origin": "用户收集"
        }
        
        if not data_items:
            return suggestions
        
        total_count = len(data_items)
        
        # 提取标签信息
        all_tags = []
        for item in data_items:
            tags = item.get("tags", [])
            if isinstance(tags, list):
                all_tags.extend([tag.strip() for tag in tags if tag.strip()])
        
        # 统计最常见的标签
        tag_counter = Counter(all_tags)
        common_tags = [tag for tag, count in tag_counter.most_common(3)]
        
        # 提取地址信息以推断区域
        addresses = []
        for item in data_items:
            address = item.get("address", "").strip()
            if address:
                addresses.append(address)
        
        # 尝试提取共同的地理区域
        region = ""
        if addresses:
            # 简单的区域提取逻辑
            for addr in addresses:
                if "区" in addr:
                    parts = addr.split("区")
                    if len(parts) > 1:
                        region_part = parts[0]
                        if len(region_part) >= 2:
                            region = region_part[-2:] + "区"
                            break
            
            # 如果没有找到区，尝试找街道
            if not region:
                for addr in addresses:
                    if "街道" in addr:
                        parts = addr.split("街道")
                        if len(parts) > 1:
                            street_part = parts[0]
                            if len(street_part) >= 4:
                                region = street_part[-4:] + "街道"
                                break
        
        # 生成地图名称
        if common_tags and region:
            tag_str = "、".join(common_tags[:2])
            suggestions["name"] = f"{region}{tag_str}地图"
        elif common_tags:
            tag_str = "、".join(common_tags[:2])
            suggestions["name"] = f"{tag_str}推荐地图"
        elif region:
            suggestions["name"] = f"{region}生活服务地图"
        else:
            suggestions["name"] = f"精选{total_count}个地点推荐地图"
        
        # 生成地图描述
        desc_parts = []
        if region:
            desc_parts.append(f"位于{region}")
        
        if common_tags:
            if len(common_tags) == 1:
                desc_parts.append(f"主要包含{common_tags[0]}类场所")
            else:
                tag_str = "、".join(common_tags)
                desc_parts.append(f"涵盖{tag_str}等多种类型场所")
        
        desc_parts.append(f"共收录{total_count}个精选地点")
        
        suggestions["description"] = "，".join(desc_parts) + "。"
        
        # 尝试推断数据来源
        web_names = [item.get("webName", "").strip()
                     for item in data_items if item.get("webName", "").strip()]
        if web_names:
            common_web = Counter(web_names).most_common(1)
            if common_web:
                suggestions["origin"] = common_web[0][0]
        
        return suggestions 