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

"""
JSON编辑器组件
提供统一的JSON预览和编辑功能
"""

import streamlit as st
import json
from typing import Dict, Any, Optional
from .data_manager import DataManager


class JSONEditor:
    """JSON编辑器类"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def render_editor_modal(self):
        """渲染JSON编辑器模态框"""
        if not st.session_state.get('show_json_editor', False):
            return
        
        # 创建模态框效果
        with st.container():
            st.markdown("---")
            st.markdown("## 📝 JSON数据编辑器")
            
            # 获取当前JSON数据
            current_json = self.data_manager.get_saved_json()
            
            # 显示当前数据统计
            self._render_json_stats(current_json)
            
            # JSON编辑区域
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # 将JSON转换为格式化字符串
                json_str = json.dumps(current_json, ensure_ascii=False, indent=2)
                
                # 文本编辑器
                edited_json_str = st.text_area(
                    "编辑JSON数据",
                    value=json_str,
                    height=400,
                    help="直接编辑JSON数据，保存时会验证格式"
                )
            
            with col2:
                st.markdown("### 🛠️ 操作")
                
                # 格式化按钮
                if st.button("🎨 格式化", use_container_width=True):
                    try:
                        parsed = json.loads(edited_json_str)
                        formatted = json.dumps(parsed, ensure_ascii=False, indent=2)
                        st.success("✅ JSON格式化完成")
                        # 直接显示格式化后的内容，不使用session_state
                        edited_json_str = formatted
                    except json.JSONDecodeError as e:
                        st.error(f"JSON格式错误: {str(e)}")
                
                # 验证按钮
                if st.button("✅ 验证格式", use_container_width=True):
                    is_valid, error_msg = self._validate_json(edited_json_str)
                    if is_valid:
                        st.success("✅ JSON格式正确")
                    else:
                        st.error(f"❌ {error_msg}")
                
                # 重置按钮
                if st.button("🔄 重置", use_container_width=True):
                    st.rerun()
                
                st.markdown("---")
                
                # 保存和取消按钮
                col_save, col_cancel = st.columns(2)
                
                with col_save:
                    if st.button("💾 保存", type="primary", use_container_width=True):
                        self._save_json(edited_json_str)
                
                with col_cancel:
                    if st.button("❌ 取消", use_container_width=True):
                        st.session_state['show_json_editor'] = False
                        st.rerun()
            
            # 提示信息
            st.markdown("**💡 使用提示:**")
            st.markdown("- 点击'格式化'美化JSON格式")
            st.markdown("- 点击'验证格式'检查数据正确性")
            st.markdown("- 保存前会自动验证数据结构")
            
            st.markdown("---")
    
    def _render_json_stats(self, json_data: Dict[str, Any]):
        """渲染JSON数据统计信息"""
        st.markdown("### 📊 数据概览")
        
        data_items = json_data.get("data", [])
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📍 地点总数", len(data_items))
        
        with col2:
            has_coords = sum(1 for item in data_items 
                           if item.get("center", {}).get("lat", 0) != 0)
            st.metric("🌐 有坐标", has_coords)
        
        with col3:
            has_phone = sum(1 for item in data_items 
                          if item.get("phone", "").strip())
            st.metric("📞 有电话", has_phone)
        
        with col4:
            has_address = sum(1 for item in data_items 
                            if item.get("address", "").strip())
            st.metric("📍 有地址", has_address)
        
        # 显示地图信息（如果有）
        if json_data.get("name") or json_data.get("description"):
            st.info(f"🗺️ 地图名称: {json_data.get('name', '未设置')} | "
                   f"描述: {json_data.get('description', '未设置')}")
    
    def _validate_json(self, json_str: str) -> tuple[bool, Optional[str]]:
        """验证JSON格式和数据结构"""
        try:
            # 基本JSON格式验证
            parsed_data = json.loads(json_str)
            
            # 数据结构验证
            if not isinstance(parsed_data, dict):
                return False, "根对象必须是字典类型"
            
            # 检查必要字段
            if "data" not in parsed_data:
                return False, "缺少必要的 'data' 字段"
            
            if not isinstance(parsed_data["data"], list):
                return False, "'data' 字段必须是数组类型"
            
            # 验证数据项结构
            for i, item in enumerate(parsed_data["data"]):
                if not isinstance(item, dict):
                    return False, f"数据项 {i+1} 必须是字典类型"
                
                # 检查坐标格式（如果存在）
                if "center" in item:
                    center = item["center"]
                    if not isinstance(center, dict):
                        return False, f"数据项 {i+1} 的 'center' 必须是字典类型"
                    
                    if "lat" in center or "lng" in center:
                        lat = center.get("lat", 0)
                        lng = center.get("lng", 0)
                        
                        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
                            return False, f"数据项 {i+1} 的坐标必须是数字类型"
                        
                        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                            return False, f"数据项 {i+1} 的坐标超出有效范围"
            
            return True, None
            
        except json.JSONDecodeError as e:
            return False, f"JSON格式错误: {str(e)}"
        except Exception as e:
            return False, f"验证错误: {str(e)}"
    
    def _save_json(self, json_str: str):
        """保存JSON数据"""
        is_valid, error_msg = self._validate_json(json_str)
        
        if not is_valid:
            st.error(f"❌ 保存失败: {error_msg}")
            return
        
        try:
            # 解析JSON
            parsed_data = json.loads(json_str)
            
            # 保存数据
            self.data_manager.set_saved_json(parsed_data)
            
            # 关闭编辑器
            st.session_state['show_json_editor'] = False
            
            st.success("✅ JSON数据已保存成功！")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ 保存失败: {str(e)}")
    
    @staticmethod
    def show_editor():
        """显示JSON编辑器"""
        st.session_state['show_json_editor'] = True
    
    @staticmethod
    def hide_editor():
        """隐藏JSON编辑器"""
        st.session_state['show_json_editor'] = False
    
    @staticmethod
    def is_editor_visible() -> bool:
        """检查编辑器是否可见"""
        return st.session_state.get('show_json_editor', False) 