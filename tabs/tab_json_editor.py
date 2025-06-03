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

import streamlit as st
import json
from typing import Dict, Any, Optional
from utils.data_manager import DataManager


class JSONEditorTab:
    """JSON编辑器标签页"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def render(self):
        """渲染JSON编辑器标签页"""
        st.info("步骤7: JSON数据编辑器")
        
        if not self.data_manager.has_saved_json():
            st.warning("⚠️ 暂无JSON数据可编辑，请先完成数据提取步骤。")
            st.info("💡 请在'数据提取'标签页中提取或导入数据，然后返回此页面进行编辑。")
            return
        
        # 获取当前JSON数据
        current_json = self.data_manager.get_saved_json()
        
        # JSON编辑区域
        self._render_json_editor(current_json)
    
    def _render_json_editor(self, current_json: Dict[str, Any]):
        """渲染JSON编辑器"""
        st.subheader("📝 JSON数据编辑器")
        
        # 显示数据统计信息
        self._show_data_statistics(current_json)
        
        # 创建两列布局
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # 将JSON转换为格式化字符串
            json_str = json.dumps(current_json, ensure_ascii=False, indent=2)
            
            # 文本编辑器
            edited_json_str = st.text_area(
                "编辑JSON数据",
                value=json_str,
                height=500,
                help="直接编辑JSON数据，保存时会验证格式",
                key="json_editor_textarea"
            )
        
        with col2:
            st.markdown("### 🛠️ 操作工具")
            
            # 格式化按钮
            if st.button("🎨 格式化JSON", use_container_width=True):
                # 使用统一的语法验证
                is_valid, error_msg = self.data_manager.validate_json_syntax(edited_json_str)
                if not is_valid:
                    st.error(f"❌ {error_msg}")
                else:
                    try:
                        parsed = json.loads(edited_json_str)
                        formatted = json.dumps(parsed, ensure_ascii=False, indent=2)
                        st.session_state.json_editor_textarea = formatted
                        st.success("✅ JSON格式化完成")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 格式化失败: {str(e)}")
            
            # 验证按钮
            if st.button("✅ 验证格式", use_container_width=True):
                is_valid, error_msg = self._validate_json(edited_json_str)
                if is_valid:
                    st.success("✅ JSON格式正确")
                    # 显示验证后的统计
                    try:
                        parsed_data = json.loads(edited_json_str)
                        self._show_validation_statistics(parsed_data)
                    except:
                        pass
                else:
                    st.error(f"❌ {error_msg}")
            
            # 重置按钮
            if st.button("🔄 重置到原始", use_container_width=True):
                original_json = json.dumps(current_json, ensure_ascii=False, indent=2)
                st.session_state.json_editor_textarea = original_json
                st.info("🔄 已重置到原始数据")
                st.rerun()
            
            # 保存按钮
            if st.button("💾 保存修改", type="primary", use_container_width=True):
                self._save_json(edited_json_str)

    def _show_data_statistics(self, json_data: Dict[str, Any]):
        """显示数据统计信息"""
        data_items = json_data.get("data", [])
        if not data_items:
            return
        
        st.info("📊 **当前数据统计**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total = len(data_items)
            has_name = sum(1 for item in data_items if item.get("name", "").strip())
            st.metric("📍 总地点", total)
            st.metric("📝 有名称", has_name)
        
        with col2:
            has_address = sum(1 for item in data_items if item.get("address", "").strip())
            has_phone = sum(1 for item in data_items if item.get("phone", "").strip())
            st.metric("🏠 有地址", has_address)
            st.metric("📞 有电话", has_phone)
        
        with col3:
            has_webname = sum(1 for item in data_items if item.get("webName", "").strip())
            has_weblink = sum(1 for item in data_items if item.get("webLink", "").strip())
            st.metric("🌐 有网站名", has_webname)
            st.metric("🔗 有网站链接", has_weblink)
        
        with col4:
            has_intro = sum(1 for item in data_items if item.get("intro", "").strip())
            has_coords = sum(1 for item in data_items 
                           if item.get("center", {}).get("lat", 0) != 0 and 
                              item.get("center", {}).get("lng", 0) != 0)
            st.metric("📖 有简介", has_intro)
            st.metric("📍 有坐标", has_coords)

    def _show_validation_statistics(self, json_data: Dict[str, Any]):
        """显示验证后的统计信息"""
        st.success("🔍 **验证统计：**")
        data_items = json_data.get("data", [])
        
        # 检查webLink字段的完整性
        weblink_stats = []
        for i, item in enumerate(data_items):
            has_weblink_field = "webLink" in item
            weblink_value = item.get("webLink", "")
            weblink_stats.append({
                "序号": i + 1,
                "有webLink字段": "✅" if has_weblink_field else "❌",
                "webLink值": weblink_value if weblink_value else "(空)"
            })
        
        if len(weblink_stats) <= 5:
            st.write("**webLink字段检查：**")
            for stat in weblink_stats:
                st.write(f"地点{stat['序号']}: {stat['有webLink字段']} | 值: {stat['webLink值']}")
        else:
            missing_weblink = sum(1 for item in data_items if "webLink" not in item)
            empty_weblink = sum(1 for item in data_items if "webLink" in item and not item["webLink"].strip())
            valid_weblink = sum(1 for item in data_items if item.get("webLink", "").strip())
            
            st.write(f"**webLink字段统计：** 缺失 {missing_weblink} | 空值 {empty_weblink} | 有效 {valid_weblink}")

    def _validate_json(self, json_str: str) -> tuple[bool, Optional[str]]:
        """验证JSON格式和数据结构"""
        # 首先验证JSON语法
        is_valid_syntax, syntax_error = self.data_manager.validate_json_syntax(json_str)
        if not is_valid_syntax:
            return False, syntax_error
        
        try:
            # 解析JSON
            parsed_data = json.loads(json_str)
            
            # 使用data_manager的结构验证
            is_valid_structure, structure_error = self.data_manager.validate_json_structure(parsed_data)
            if not is_valid_structure:
                return False, structure_error
            
            return True, None
            
        except Exception as e:
            return False, f"验证错误: {str(e)}"
    
    def _save_json(self, json_str: str):
        """保存JSON数据"""
        is_valid, error_msg = self._validate_json(json_str)
        
        if not is_valid:
            st.error(f"❌ 保存失败: {error_msg}")
            return
        
        try:
            # 获取保存前的数据统计
            old_data = self.data_manager.get_saved_json()
            old_weblink_count = sum(1 for item in old_data.get("data", []) 
                                  if item.get("webLink", "").strip())
            
            # 解析JSON
            parsed_data = json.loads(json_str)
            
            # 获取保存后的数据统计
            new_weblink_count = sum(1 for item in parsed_data.get("data", []) 
                                  if item.get("webLink", "").strip())
            
            # 保存数据
            self.data_manager.set_saved_json(parsed_data)
            
            st.success("✅ JSON数据已保存成功！")
            st.info("💡 数据已更新，其他标签页中的数据也会同步更新。")
            
            # 显示保存的数据统计
            data_count = len(parsed_data.get("data", []))
            
            # 显示webLink字段的变化
            if new_weblink_count != old_weblink_count:
                if new_weblink_count > old_weblink_count:
                    st.success(f"🔗 webLink字段: {old_weblink_count} → {new_weblink_count} (+{new_weblink_count - old_weblink_count})")
                elif new_weblink_count < old_weblink_count:
                    st.warning(f"🔗 webLink字段: {old_weblink_count} → {new_weblink_count} (-{old_weblink_count - new_weblink_count})")
            else:
                st.info(f"🔗 webLink字段数量保持不变: {new_weblink_count}")
            
            st.balloons()  # 添加庆祝动画
            st.success(f"🎉 成功保存 {data_count} 个地点的数据！")
            
        except Exception as e:
            st.error(f"❌ 保存失败: {str(e)}") 