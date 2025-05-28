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
            # 解析JSON
            parsed_data = json.loads(json_str)
            
            # 保存数据
            self.data_manager.set_saved_json(parsed_data)
            
            st.success("✅ JSON数据已保存成功！")
            st.info("💡 数据已更新，其他标签页中的数据也会同步更新。")
            
            # 显示保存的数据统计
            data_count = len(parsed_data.get("data", []))
            st.balloons()  # 添加庆祝动画
            st.success(f"🎉 成功保存 {data_count} 个地点的数据！")
            
        except Exception as e:
            st.error(f"❌ 保存失败: {str(e)}") 