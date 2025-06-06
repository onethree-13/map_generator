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
import time
from typing import Dict, Any, Optional, Tuple
from utils.data_manager import DataManager, validate_url


class TabManager:
    """Tab 管理器，负责处理 Tab 切换时的数据验证和保存"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self._init_session_state()
    
    def _init_session_state(self):
        """初始化 session state"""
        if 'current_tab' not in st.session_state:
            st.session_state.current_tab = "数据提取"
        
        if 'previous_tab' not in st.session_state:
            st.session_state.previous_tab = "数据提取"
        
        if 'tab_switch_pending' not in st.session_state:
            st.session_state.tab_switch_pending = False
        
        if 'last_validation_result' not in st.session_state:
            st.session_state.last_validation_result = {"valid": True, "message": ""}
        
        if 'tab_access_count' not in st.session_state:
            st.session_state.tab_access_count = {}
        
        if 'auto_save_enabled' not in st.session_state:
            st.session_state.auto_save_enabled = True
        
        if 'button_counter' not in st.session_state:
            st.session_state.button_counter = 0
    
    def _get_unique_key(self, base_key: str) -> str:
        """生成唯一的按钮 key"""
        st.session_state.button_counter += 1
        timestamp = int(time.time() * 1000)  # 毫秒级时间戳
        return f"{base_key}_{st.session_state.button_counter}_{timestamp}"
    
    def detect_tab_switch(self, accessing_tab: str) -> bool:
        """
        检测是否发生了 Tab 切换
        
        Args:
            accessing_tab: 当前正在访问的 Tab
            
        Returns:
            bool: 是否发生了切换
        """
        current_tab = st.session_state.current_tab
        
        # 增加访问计数（仅对当前活跃的 tab）
        if accessing_tab == current_tab:
            if accessing_tab not in st.session_state.tab_access_count:
                st.session_state.tab_access_count[accessing_tab] = 0
            st.session_state.tab_access_count[accessing_tab] += 1
        
        # 如果访问的 Tab 与当前 Tab 不同，说明发生了切换
        if accessing_tab != current_tab:
            return True
        
        return False
    

    
    def handle_tab_switch(self, new_tab: str, force_switch: bool = False) -> bool:
        """
        处理 Tab 切换
        
        Args:
            new_tab: 新的 Tab 名称
            force_switch: 是否强制切换（跳过验证）
            
        Returns:
            bool: 是否成功切换
        """
        current_tab = st.session_state.current_tab
        
        # 如果是同一个 Tab，直接返回
        if current_tab == new_tab:
            return True
        
        # 记录切换信息
        st.session_state.previous_tab = current_tab
        
        # 如果启用了自动保存且不是强制切换，先进行数据验证
        if st.session_state.auto_save_enabled and not force_switch:
            validation_result = self._validate_current_tab_data(current_tab)
            st.session_state.last_validation_result = validation_result
            
            if not validation_result["valid"]:
                # 验证失败，显示错误信息
                st.error(f"❌ {validation_result['message']}")
                st.warning("⚠️ 请修复数据问题后再切换 Tab，或使用强制切换")
                
                # 提供强制切换选项
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔧 修复数据", key=self._get_unique_key(f"fix_data_{current_tab}")):
                        st.info("💡 请在当前 Tab 中修复数据问题")
                        return False
                
                with col2:
                    if st.button("⚡ 强制切换", key=self._get_unique_key(f"force_switch_{new_tab}"), type="secondary"):
                        return self.handle_tab_switch(new_tab, force_switch=True)
                
                return False
        
        # 保存当前 Tab 的数据
        if st.session_state.auto_save_enabled:
            save_result = self._save_current_tab_data(current_tab)
            
            if not save_result["success"]:
                st.error(f"❌ 保存失败：{save_result['message']}")
                
                # 提供选择：重试保存或强制切换
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔄 重试保存", key=self._get_unique_key(f"retry_save_{current_tab}")):
                        return self.handle_tab_switch(new_tab)
                
                with col2:
                    if st.button("⚡ 跳过保存", key=self._get_unique_key(f"skip_save_{new_tab}"), type="secondary"):
                        return self.handle_tab_switch(new_tab, force_switch=True)
                
                return False
        
        # 更新当前 Tab
        st.session_state.current_tab = new_tab
        
        # 重新加载新 Tab 的数据
        self._reload_tab_data(new_tab)
        
        # 显示成功信息
        if not force_switch and st.session_state.auto_save_enabled:
            st.success(f"✅ 已从 {current_tab} 切换到 {new_tab}")
        
        return True
    
    def _validate_current_tab_data(self, tab_name: str) -> Dict[str, Any]:
        """
        验证当前 Tab 的数据格式
        
        Args:
            tab_name: Tab 名称
            
        Returns:
            Dict: 验证结果 {"valid": bool, "message": str}
        """
        try:
            if tab_name == "数据提取":
                return self._validate_extraction_data()
            elif tab_name == "地图信息":
                return self._validate_map_info_data()
            elif tab_name == "数据编辑":
                return self._validate_editing_data()
            elif tab_name == "标签管理":
                return self._validate_tag_data()
            elif tab_name == "坐标管理":
                return self._validate_coordinate_data()
            elif tab_name == "数据导出":
                return self._validate_export_data()
            elif tab_name == "JSON编辑器":
                return self._validate_json_editor_data()
            else:
                return {"valid": True, "message": ""}
                
        except Exception as e:
            return {"valid": False, "message": f"数据验证时发生错误：{str(e)}"}
    
    def _validate_extraction_data(self) -> Dict[str, Any]:
        """验证数据提取 Tab 的数据"""
        extracted_text = self.data_manager.get_extracted_text()
        
        if extracted_text and len(extracted_text.strip()) > 0:
            # 检查文本是否包含有效内容
            if len(extracted_text.strip()) < 10:
                return {"valid": False, "message": "提取的文本内容过短，可能无效"}
            
            # 检查文本中是否包含可能的网站链接格式（http/https或www开头）
            import re
            url_patterns = [
                r'https?://[^\s]+',  # http或https开头的URL
                r'www\.[^\s]+',      # www开头的URL
                r'[^\s]+\.(com|cn|org|net|edu|gov)[^\s]*'  # 常见域名后缀
            ]
            
            found_urls = []
            for pattern in url_patterns:
                urls = re.findall(pattern, extracted_text, re.IGNORECASE)
                found_urls.extend(urls)
            
            if found_urls:
                # 如果发现URL，提供提示
                unique_urls = list(set(found_urls))[:3]  # 最多显示3个
                url_info = ", ".join(unique_urls)
                if len(found_urls) > 3:
                    url_info += f" 等{len(found_urls)}个"
                return {"valid": True, "message": f"数据提取验证通过，发现网站链接：{url_info}"}
        
        return {"valid": True, "message": "数据提取验证通过"}
    
    def _validate_map_info_data(self) -> Dict[str, Any]:
        """验证地图信息 Tab 的数据"""
        saved_json = self.data_manager.get_saved_json()
        
        # 检查基本信息
        if not saved_json.get("name", "").strip():
            return {"valid": False, "message": "地图名称不能为空"}
        
        # 检查过滤器格式
        filter_data = saved_json.get("filter", {})
        if not isinstance(filter_data, dict):
            return {"valid": False, "message": "过滤器数据格式错误"}
        
        if "inclusive" not in filter_data or "exclusive" not in filter_data:
            return {"valid": False, "message": "过滤器缺少必要字段"}
        
        return {"valid": True, "message": "地图信息验证通过"}
    
    def _validate_editing_data(self) -> Dict[str, Any]:
        """验证数据编辑 Tab 的数据"""
        # 检查是否有待保存的编辑
        if self.data_manager.has_pending_edits():
            return {"valid": False, "message": "有待保存的编辑，请先应用或撤销编辑"}
        
        # 验证saved_json的结构
        saved_json = self.data_manager.get_saved_json()
        is_valid, error_msg = self.data_manager.validate_json_structure(saved_json)
        
        if not is_valid:
            return {"valid": False, "message": f"数据格式错误：{error_msg}"}
        
        # 验证webLink字段
        data_items = saved_json.get("data", [])
        weblink_errors = []
        
        for i, item in enumerate(data_items):
            web_link = item.get("webLink", "")
            if web_link:
                is_valid_url, url_error = validate_url(web_link)
                if not is_valid_url:
                    weblink_errors.append(f"第{i+1}项的webLink格式错误：{url_error}")
        
        if weblink_errors:
            return {"valid": False, "message": f"发现webLink格式问题：{'; '.join(weblink_errors[:3])}{'...' if len(weblink_errors) > 3 else ''}"}
        
        return {"valid": True, "message": "数据编辑验证通过"}
    
    def _validate_tag_data(self) -> Dict[str, Any]:
        """验证标签管理 Tab 的数据"""
        # 检查是否有待保存的编辑
        if self.data_manager.has_pending_edits():
            return {"valid": False, "message": "有待保存的标签编辑，请先应用或撤销编辑"}
        
        # 检查标签数据的一致性（从saved_json读取）
        all_tags = self.data_manager.get_all_tags(use_editing=False)
        
        # 检查是否有重复标签
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        return {"valid": True, "message": "标签管理验证通过"}
    
    def _validate_coordinate_data(self) -> Dict[str, Any]:
        """验证坐标管理 Tab 的数据"""
        # 从saved_json读取数据进行验证
        saved_json = self.data_manager.get_saved_json()
        data_items = saved_json.get("data", [])
        
        # 检查坐标格式
        for i, item in enumerate(data_items):
            center = item.get("center", {})
            if "lat" in center or "lng" in center:
                try:
                    lat = float(center.get("lat", 0))
                    lng = float(center.get("lng", 0))
                    
                    # 检查坐标范围
                    if not (-90 <= lat <= 90):
                        return {"valid": False, "message": f"第{i+1}项的纬度超出有效范围"}
                    if not (-180 <= lng <= 180):
                        return {"valid": False, "message": f"第{i+1}项的经度超出有效范围"}
                        
                except (ValueError, TypeError):
                    return {"valid": False, "message": f"第{i+1}项的坐标格式错误"}
            
            # 验证webLink字段
            web_link = item.get("webLink", "")
            if web_link:
                is_valid_url, url_error = validate_url(web_link)
                if not is_valid_url:
                    return {"valid": False, "message": f"第{i+1}项的webLink格式错误：{url_error}"}
        
        return {"valid": True, "message": "坐标管理验证通过"}
    
    def _validate_export_data(self) -> Dict[str, Any]:
        """验证数据导出 Tab 的数据"""
        saved_json = self.data_manager.get_saved_json()
        
        if not saved_json.get("data"):
            return {"valid": False, "message": "没有可导出的数据"}
        
        return {"valid": True, "message": "数据导出验证通过"}
    
    def _validate_json_editor_data(self) -> Dict[str, Any]:
        """验证 JSON 编辑器 Tab 的数据"""
        # JSON 编辑器的验证在其内部处理
        return {"valid": True, "message": "JSON编辑器验证通过"}
    
    def _save_current_tab_data(self, tab_name: str) -> Dict[str, Any]:
        """
        保存当前 Tab 的数据
        
        Args:
            tab_name: Tab 名称
            
        Returns:
            Dict: 保存结果 {"success": bool, "message": str}
        """
        try:
            if tab_name == "数据提取":
                return self._save_extraction_data()
            elif tab_name == "地图信息":
                return self._save_map_info_data()
            elif tab_name == "数据编辑":
                return self._save_editing_data()
            elif tab_name == "标签管理":
                return self._save_tag_data()
            elif tab_name == "坐标管理":
                return self._save_coordinate_data()
            elif tab_name == "数据导出":
                return self._save_export_data()
            elif tab_name == "JSON编辑器":
                return self._save_json_editor_data()
            else:
                return {"success": True, "message": "无需保存"}
                
        except Exception as e:
            return {"success": False, "message": f"保存时发生错误：{str(e)}"}
    
    def _save_extraction_data(self) -> Dict[str, Any]:
        """保存数据提取的数据"""
        # 数据提取的数据已经自动保存到 extracted_text
        return {"success": True, "message": "数据提取已保存"}
    
    def _save_map_info_data(self) -> Dict[str, Any]:
        """保存地图信息的数据"""
        # 地图信息的数据已经直接保存到 saved_json
        return {"success": True, "message": "地图信息已保存"}
    
    def _save_editing_data(self) -> Dict[str, Any]:
        """保存数据编辑的数据"""
        # 如果有待保存的编辑，应用它们
        if self.data_manager.has_pending_edits():
            self.data_manager.apply_edits()
            return {"success": True, "message": "编辑数据已应用并保存"}
        else:
            return {"success": True, "message": "无待保存的编辑数据"}
    
    def _save_tag_data(self) -> Dict[str, Any]:
        """保存标签管理的数据"""
        # 如果有待保存的编辑，应用它们
        if self.data_manager.has_pending_edits():
            self.data_manager.apply_edits()
            return {"success": True, "message": "标签编辑已应用并保存"}
        else:
            return {"success": True, "message": "无待保存的标签编辑"}
    
    def _save_coordinate_data(self) -> Dict[str, Any]:
        """保存坐标管理的数据"""
        # 坐标管理的数据已经直接保存到 saved_json
        return {"success": True, "message": "坐标数据已保存"}
    
    def _save_export_data(self) -> Dict[str, Any]:
        """保存数据导出的数据"""
        # 数据导出不需要保存状态
        return {"success": True, "message": "导出设置已保存"}
    
    def _save_json_editor_data(self) -> Dict[str, Any]:
        """保存 JSON 编辑器的数据"""
        # JSON 编辑器的保存在其内部处理
        return {"success": True, "message": "JSON编辑器数据已保存"}
    
    def _reload_tab_data(self, tab_name: str):
        """
        重新加载新 Tab 的数据
        
        Args:
            tab_name: Tab 名称
        """
        try:
            # 在新的逻辑下，大部分Tab都直接从saved_json读取数据
            # 只有在明确需要编辑时才会使用editing_json
            # 因此这里不需要特殊的重新加载逻辑
            
            # 如果有待保存的编辑，给出提示
            if self.data_manager.has_pending_edits():
                st.warning(f"⚠️ 切换到 {tab_name} 时发现有待保存的编辑，请注意及时保存或撤销")
            
        except Exception as e:
            st.warning(f"⚠️ 重新加载 {tab_name} 数据时发生错误：{str(e)}")
    
    def get_current_tab(self) -> str:
        """获取当前 Tab"""
        return st.session_state.current_tab
    
    def get_previous_tab(self) -> str:
        """获取上一个 Tab"""
        return st.session_state.previous_tab
    
    def get_last_validation_result(self) -> Dict[str, Any]:
        """获取最后一次验证结果"""
        return st.session_state.last_validation_result
    
    def force_switch_tab(self, new_tab: str) -> bool:
        """强制切换 Tab（跳过验证）"""
        return self.handle_tab_switch(new_tab, force_switch=True)
    

    
    def toggle_auto_save(self, enabled: bool = None) -> bool:
        """切换自动保存功能"""
        if enabled is not None:
            st.session_state.auto_save_enabled = enabled
        else:
            st.session_state.auto_save_enabled = not st.session_state.auto_save_enabled
        
        return st.session_state.auto_save_enabled
    
    def is_auto_save_enabled(self) -> bool:
        """检查自动保存是否启用"""
        return st.session_state.auto_save_enabled
    
    def show_tab_status(self):
        """显示 Tab 状态信息"""
        current_tab = self.get_current_tab()
        previous_tab = self.get_previous_tab()
        last_result = self.get_last_validation_result()
        
        with st.expander("📊 Tab 管理状态", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**当前 Tab：** {current_tab}")
                st.write(f"**上一个 Tab：** {previous_tab}")
                
                # 自动保存开关
                auto_save = st.checkbox(
                    "启用自动保存", 
                    value=self.is_auto_save_enabled(),
                    key="auto_save_checkbox",
                    help="在切换 Tab 时自动验证和保存数据"
                )
                if auto_save != self.is_auto_save_enabled():
                    self.toggle_auto_save(auto_save)
                    st.rerun()
                
                # 显示数据状态
                has_extracted = self.data_manager.has_extracted_text()
                has_saved = self.data_manager.has_saved_json()
                has_pending = self.data_manager.has_pending_edits()
                
                st.write("**数据状态：**")
                st.write(f"- 提取文本: {'✅' if has_extracted else '❌'}")
                st.write(f"- 保存数据: {'✅' if has_saved else '❌'}")
                st.write(f"- 待保存编辑: {'⚠️' if has_pending else '✅'}")
                
                if has_pending:
                    st.warning("有待保存的编辑，请及时处理")
            
            with col2:
                st.write("**最后验证结果：**")
                if last_result["valid"]:
                    st.success(f"✅ {last_result['message']}")
                else:
                    st.error(f"❌ {last_result['message']}")
                
                # 显示数据统计
                stats = self.data_manager.get_data_statistics(use_editing=False)
                st.write("**数据统计：**")
                st.write(f"- 总地点数: {stats['total_locations']}")
                st.write(f"- 有坐标: {stats['has_coordinates']}")
                st.write(f"- 有地址: {stats['has_address']}")
                st.write(f"- 有电话: {stats['has_phone']}")
                st.write(f"- 有网站链接: {stats['has_weblink']}")
                
                # 显示webLink字段的详细统计
                if stats['total_locations'] > 0:
                    weblink_percentage = (stats['has_weblink'] / stats['total_locations']) * 100
                    if weblink_percentage > 0:
                        st.write(f"  🔗 网站链接完整度: {weblink_percentage:.1f}%")
                
                # Tab 访问统计
                if st.session_state.tab_access_count:
                    st.write("**Tab 访问次数：**")
                    for tab, count in st.session_state.tab_access_count.items():
                        st.write(f"- {tab}: {count}")
    
    def show_quick_actions(self):
        """显示快速操作按钮"""
        st.subheader("🚀 快速操作")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 保存当前数据", key="save_current_data_btn", help="保存当前 Tab 的数据"):
                current_tab = self.get_current_tab()
                result = self._save_current_tab_data(current_tab)
                if result["success"]:
                    st.success(f"✅ {result['message']}")
                else:
                    st.error(f"❌ {result['message']}")
        
        with col2:
            if st.button("✅ 应用编辑", key="apply_edits_btn", 
                        disabled=not self.data_manager.has_pending_edits(),
                        help="应用待保存的编辑到保存版本"):
                self.data_manager.apply_edits()
                st.success("✅ 编辑已应用")
        
        with col3:
            if st.button("🧹 验证数据", key="validate_data_btn", help="验证当前 Tab 的数据格式"):
                current_tab = self.get_current_tab()
                result = self._validate_current_tab_data(current_tab)
                if result["valid"]:
                    st.success(f"✅ {result['message']}")
                else:
                    st.error(f"❌ {result['message']}")
        
        # webLink相关操作
        st.subheader("🔗 网站链接操作")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔍 检查网站链接", key="check_weblinks_btn", help="检查所有webLink字段的有效性"):
                self._check_all_weblinks()
        
        with col2:
            if st.button("🧹 清理空链接", key="clean_empty_weblinks_btn", help="移除所有空的webLink字段"):
                self._clean_empty_weblinks()
        
        with col3:
            if st.button("📊 网站链接统计", key="weblink_stats_btn", help="显示webLink字段的详细统计"):
                self._show_weblink_statistics()
        
        # Tab 切换按钮
        st.subheader("📋 Tab 切换")
        tab_cols = st.columns(4)
        
        tab_buttons = [
            ("📁", "数据提取"),
            ("🗺️", "地图信息"), 
            ("📝", "数据编辑"),
            ("🏷️", "标签管理")
        ]
        
        for i, (icon, tab_name) in enumerate(tab_buttons):
            with tab_cols[i % 4]:
                if st.button(f"{icon} {tab_name}", key=f"switch_to_{tab_name}", 
                           disabled=(self.get_current_tab() == tab_name)):
                    self.manual_switch_tab(tab_name)
        
        tab_cols2 = st.columns(3)
        tab_buttons2 = [
            ("📍", "坐标管理"),
            ("📊", "数据导出"),
            ("📝", "JSON编辑器")
        ]
        
        for i, (icon, tab_name) in enumerate(tab_buttons2):
            with tab_cols2[i]:
                if st.button(f"{icon} {tab_name}", key=f"switch_to_{tab_name}", 
                           disabled=(self.get_current_tab() == tab_name)):
                    self.manual_switch_tab(tab_name)
    
    def manual_switch_tab(self, new_tab: str):
        """手动切换 Tab"""
        current_tab = self.get_current_tab()
        
        if current_tab == new_tab:
            return
        
        # 如果启用了自动保存，先验证和保存当前数据
        if self.is_auto_save_enabled():
            # 验证当前 Tab 数据
            validation_result = self._validate_current_tab_data(current_tab)
            if not validation_result["valid"]:
                st.error(f"❌ {validation_result['message']}")
                if st.button("⚡ 强制切换", key=self._get_unique_key(f"force_manual_switch_{new_tab}")):
                    self._do_switch_tab(new_tab)
                return
            
            # 保存当前 Tab 数据
            save_result = self._save_current_tab_data(current_tab)
            if not save_result["success"]:
                st.error(f"❌ 保存失败：{save_result['message']}")
                if st.button("⚡ 跳过保存并切换", key=self._get_unique_key(f"skip_save_manual_switch_{new_tab}")):
                    self._do_switch_tab(new_tab)
                return
        
        # 执行切换
        self._do_switch_tab(new_tab)
    
    def _do_switch_tab(self, new_tab: str):
        """执行 Tab 切换"""
        st.session_state.previous_tab = st.session_state.current_tab
        st.session_state.current_tab = new_tab
        
        # 重新加载新 Tab 的数据
        self._reload_tab_data(new_tab)
        
        st.success(f"✅ 已切换到 {new_tab}")
        st.rerun()
    
    def _check_all_weblinks(self):
        """检查所有webLink字段的有效性"""
        saved_json = self.data_manager.get_saved_json()
        data_items = saved_json.get("data", [])
        
        if not data_items:
            st.info("📝 暂无数据可检查")
            return
        
        valid_links = []
        invalid_links = []
        empty_links = 0
        
        for i, item in enumerate(data_items):
            web_link = item.get("webLink", "")
            if not web_link:
                empty_links += 1
            else:
                is_valid, error_msg = validate_url(web_link)
                if is_valid:
                    valid_links.append({"index": i+1, "name": item.get("name", "未知"), "url": web_link})
                else:
                    invalid_links.append({"index": i+1, "name": item.get("name", "未知"), "url": web_link, "error": error_msg})
        
        # 显示检查结果
        st.write("🔍 **网站链接检查结果：**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ 有效链接", len(valid_links))
        with col2:
            st.metric("❌ 无效链接", len(invalid_links))
        with col3:
            st.metric("⭕ 空链接", empty_links)
        
        if invalid_links:
            st.error("❌ **发现无效链接：**")
            for link in invalid_links[:5]:  # 最多显示5个
                st.write(f"• 第{link['index']}项 ({link['name']}): {link['url']} - {link['error']}")
            if len(invalid_links) > 5:
                st.write(f"... 还有 {len(invalid_links) - 5} 个无效链接")
        
        if valid_links:
            st.success(f"✅ 发现 {len(valid_links)} 个有效链接")
    
    def _clean_empty_weblinks(self):
        """清理空的webLink字段"""
        saved_json = self.data_manager.get_saved_json()
        data_items = saved_json.get("data", [])
        
        cleaned_count = 0
        for item in data_items:
            if "webLink" in item and not item["webLink"].strip():
                del item["webLink"]
                cleaned_count += 1
        
        if cleaned_count > 0:
            self.data_manager.set_saved_json(saved_json)
            st.success(f"🧹 已清理 {cleaned_count} 个空的网站链接字段")
        else:
            st.info("✨ 没有发现空的网站链接字段需要清理")
    
    def _show_weblink_statistics(self):
        """显示webLink字段的详细统计"""
        saved_json = self.data_manager.get_saved_json()
        data_items = saved_json.get("data", [])
        
        if not data_items:
            st.info("📝 暂无数据可统计")
            return
        
        total_items = len(data_items)
        has_weblink_field = sum(1 for item in data_items if "webLink" in item)
        has_weblink_value = sum(1 for item in data_items if item.get("webLink", "").strip())
        
        # 按域名统计
        domain_stats = {}
        for item in data_items:
            web_link = item.get("webLink", "").strip()
            if web_link:
                try:
                    # 简单的域名提取
                    if "://" in web_link:
                        domain = web_link.split("://")[1].split("/")[0]
                    else:
                        domain = web_link.split("/")[0]
                    domain_stats[domain] = domain_stats.get(domain, 0) + 1
                except:
                    domain_stats["其他"] = domain_stats.get("其他", 0) + 1
        
        st.write("📊 **网站链接详细统计：**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**基本统计：**")
            st.write(f"• 总地点数: {total_items}")
            st.write(f"• 有webLink字段: {has_weblink_field}")
            st.write(f"• 有webLink值: {has_weblink_value}")
            
            if total_items > 0:
                completion_rate = (has_weblink_value / total_items) * 100
                st.write(f"• 完整度: {completion_rate:.1f}%")
        
        with col2:
            if domain_stats:
                st.write("**域名分布：**")
                for domain, count in sorted(domain_stats.items(), key=lambda x: x[1], reverse=True)[:5]:
                    st.write(f"• {domain}: {count} 个")
                if len(domain_stats) > 5:
                    st.write(f"• ... 还有 {len(domain_stats) - 5} 个域名")
            else:
                st.write("**域名分布：** 暂无数据") 