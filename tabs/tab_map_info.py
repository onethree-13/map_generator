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
from utils.data_manager import DataManager
import json


class MapInfoTab:
    """地图信息标签页"""

    def __init__(self, data_manager: DataManager, processor=None):
        self.data_manager = data_manager
        self.processor = processor

    def render(self):
        """渲染地图信息标签页"""
        st.info("步骤2：地图基本信息设置")

        # 基本信息部分
        self._render_basic_info()
        
        # 分隔线
        st.divider()
        
        # Filter 编辑部分
        self._render_filter_editor()

    def _apply_ai_suggestions(self):
        """应用AI智能建议"""
        smart_placeholders = self.data_manager.generate_smart_suggestions(
            use_editing=False)
        saved_json = self.data_manager.get_saved_json()

        # 如果当前字段为空，则自动填入建议
        if not saved_json.get("name", "").strip():
            saved_json["name"] = smart_placeholders["name"]
        if not saved_json.get("description", "").strip():
            saved_json["description"] = smart_placeholders["description"]
        if not saved_json.get("origin", "").strip():
            saved_json["origin"] = smart_placeholders["origin"]

        self.data_manager.set_saved_json(saved_json)
        st.success("✅ AI建议已应用到空白字段！")
        st.rerun()

    def _render_basic_info(self):
        """渲染基本信息部分"""
        st.subheader("📋 基本信息")

        col1, col2 = st.columns([2, 1])

        # 生成智能placeholder
        smart_placeholders = self.data_manager.generate_smart_suggestions(
            use_editing=False)
        saved_json = self.data_manager.get_saved_json()

        with col1:
            map_name = st.text_input(
                "地图名称",
                value=saved_json.get("name", ""),
                placeholder=smart_placeholders["name"],
                help="为您的地图设置一个描述性的名称"
            )
            saved_json["name"] = map_name

            map_description = st.text_area(
                "地图描述",
                value=saved_json.get("description", ""),
                placeholder=smart_placeholders["description"],
                height=100,
                help="简要描述地图的用途和内容"
            )
            saved_json["description"] = map_description

            map_origin = st.text_input(
                "数据来源",
                value=saved_json.get("origin", ""),
                placeholder=smart_placeholders["origin"],
                help="标注数据的来源或提供方"
            )
            saved_json["origin"] = map_origin

            # 更新saved_json
            self.data_manager.set_saved_json(saved_json)

        with col2:
            self._render_info_preview(
                map_name, map_description, map_origin, smart_placeholders)

    def _render_filter_editor(self):
        """渲染过滤器编辑部分"""
        st.subheader("🔍 过滤器设置")
        
        saved_json = self.data_manager.get_saved_json()
        filter_data = saved_json.get("filter", {"inclusive": {}, "exclusive": {}})
        
        # AI标签筛选功能
        self._render_ai_filter_generation()
        
        st.markdown("---")
        
        # 显示现有过滤器
        self._render_existing_filters(filter_data)
        
        # 添加新过滤器
        self._render_add_filter_form()

    def _render_ai_filter_generation(self):
        """渲染AI标签筛选功能"""
        st.subheader("🤖 AI智能标签筛选")
        
        # 获取可用的标签数据
        all_tags = self.data_manager.get_all_tags(use_editing=False)
        
        if not all_tags:
            st.warning("⚠️ 暂无标签数据，无法使用AI筛选标签。请先在数据编辑或标签管理中添加标签。")
            return
        
        # AI指令输入
        ai_instruction = st.text_area(
            "请输入标签筛选指令：",
            placeholder="例如：\n• 筛选所有与餐厅相关的标签\n• 找出购物相关的标签\n• 显示娱乐类标签\n• 筛选包含'咖啡'的标签",
            height=120,
            help="用自然语言描述您想要筛选的标签类型",
            key="ai_filter_instruction"
        )
        
        # 显示可用标签信息
        with st.expander("📋 查看所有可用标签", expanded=False):
            st.write(f"**共有 {len(all_tags)} 个标签：**")
            st.write(", ".join(all_tags))
        
        # AI筛选按钮
        if st.button("🔍 AI筛选标签", type="primary", use_container_width=True,
                    disabled=not ai_instruction.strip(),
                    help="使用AI根据指令筛选相关标签"):
            if ai_instruction.strip():
                with st.spinner("AI正在分析标签..."):
                    # 创建进度显示占位符
                    progress_placeholder = st.empty()
                    
                    try:
                        # 检查是否有processor和AI客户端
                        if self.processor and hasattr(self.processor, 'openai_client') and self.processor.openai_client:
                            filtered_tags = self._filter_tags_by_ai_instruction(ai_instruction, all_tags, progress_placeholder)
                        else:
                            progress_placeholder.info("💡 未配置AI接口，使用智能关键词匹配...")
                            filtered_tags = self._fallback_filter_tags(ai_instruction, all_tags)
                        
                        progress_placeholder.empty()
                        
                        if filtered_tags:
                            st.success(f"✅ 筛选出 {len(filtered_tags)} 个相关标签：")
                            st.info(", ".join(filtered_tags))
                            
                            # 提供一键添加到过滤器的选项
                            if st.button("📋 添加到包含过滤器", key="add_to_filter"):
                                self._add_filter_from_tags("AI筛选结果", "inclusive", filtered_tags)
                        else:
                            st.warning("⚠️ 未找到符合条件的标签，请尝试其他筛选条件")
                            
                    except Exception as e:
                        progress_placeholder.empty()
                        st.error(f"❌ AI筛选失败: {str(e)}")
                        st.info("💡 正在使用关键词匹配作为备选方案...")
                        fallback_tags = self._fallback_filter_tags(ai_instruction, all_tags)
                        if fallback_tags:
                            st.info(f"🔍 关键词匹配结果: {', '.join(fallback_tags)}")
    
    def _filter_tags_by_ai_instruction(self, instruction, all_tags, progress_placeholder=None):
        """根据AI指令筛选标签"""
        if self.processor:
            # 使用真正的AI筛选
            return self.processor.ai_filter_tags(instruction, all_tags, progress_placeholder)
        else:
            # 回退到简单的关键词匹配
            return self._fallback_filter_tags(instruction, all_tags)
    
    def _fallback_filter_tags(self, instruction, all_tags):
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

    def _render_existing_filters(self, filter_data):
        """渲染现有过滤器列表"""
        st.write("**现有过滤器：**")
        
        has_filters = False
        
        # 显示 inclusive 过滤器
        for filter_name, filter_options in filter_data.get("inclusive", {}).items():
            has_filters = True
            self._render_filter_item(filter_name, "inclusive", filter_options)
        
        # 显示 exclusive 过滤器
        for filter_name, filter_options in filter_data.get("exclusive", {}).items():
            has_filters = True
            self._render_filter_item(filter_name, "exclusive", filter_options)
        
        if not has_filters:
            st.info("暂无过滤器，请添加新的过滤器。")

    def _render_filter_item(self, filter_name, filter_type, filter_options):
        """渲染单个过滤器项"""
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1, 3, 1])
            
            with col1:
                st.write(f"**{filter_name}**")
            
            with col2:
                type_color = "🟢" if filter_type == "inclusive" else "🔴"
                type_text = "包含" if filter_type == "inclusive" else "排除"
                st.write(f"{type_color} {type_text}")
            
            with col3:
                options_text = ", ".join(filter_options) if isinstance(filter_options, list) else str(filter_options)
                st.write(f"选项: {options_text}")
            
            with col4:
                if st.button("🗑️", key=f"delete_{filter_type}_{filter_name}", 
                           help="删除此过滤器"):
                    self._delete_filter(filter_name, filter_type)
                    st.rerun()

    def _render_add_filter_form(self):
        """渲染添加过滤器表单"""
        st.write("**添加新过滤器：**")
        
        with st.form("add_filter_form"):
            col1, col2 = st.columns([1, 1])
            
            with col1:
                filter_name = st.text_input(
                    "过滤器名称",
                    placeholder="例如：类型、区域、价格等",
                    help="为过滤器设置一个描述性的名称"
                )
                
                filter_type = st.selectbox(
                    "过滤器类型",
                    options=["inclusive", "exclusive"],
                    format_func=lambda x: "包含 (inclusive)" if x == "inclusive" else "排除 (exclusive)",
                    help="包含：显示匹配的项目；排除：隐藏匹配的项目"
                )
            
            with col2:
                filter_options = st.text_area(
                    "过滤器选项",
                    placeholder="请用逗号分隔多个选项，例如：餐厅,咖啡厅,酒吧",
                    height=100,
                    help="输入过滤器的选项值，多个选项用逗号分隔"
                )
            
            # 表单按钮
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
            
            with col_btn1:
                add_button = st.form_submit_button("➕ 新增", type="primary")
            
            with col_btn2:
                save_button = st.form_submit_button("💾 保存", type="secondary")
            
            # 处理表单提交
            if add_button:
                self._add_filter(filter_name, filter_type, filter_options)
            
            if save_button:
                self._save_filters()

    def _add_filter(self, filter_name, filter_type, filter_options):
        """添加新过滤器"""
        if not filter_name.strip():
            st.error("❌ 请输入过滤器名称")
            return
        
        if not filter_options.strip():
            st.error("❌ 请输入过滤器选项")
            return
        
        # 解析选项
        options_list = [option.strip() for option in filter_options.split(",") if option.strip()]
        
        if not options_list:
            st.error("❌ 请输入有效的过滤器选项")
            return
        
        # 获取当前数据
        saved_json = self.data_manager.get_saved_json()
        filter_data = saved_json.get("filter", {"inclusive": {}, "exclusive": {}})
        
        # 检查是否已存在同名过滤器
        if (filter_name in filter_data.get("inclusive", {}) or 
            filter_name in filter_data.get("exclusive", {})):
            st.error(f"❌ 过滤器 '{filter_name}' 已存在")
            return
        
        # 添加新过滤器
        if filter_type not in filter_data:
            filter_data[filter_type] = {}
        
        filter_data[filter_type][filter_name] = options_list
        
        # 更新数据
        saved_json["filter"] = filter_data
        self.data_manager.set_saved_json(saved_json)
        
        st.success(f"✅ 成功添加过滤器 '{filter_name}'")
        st.rerun()

    def _delete_filter(self, filter_name, filter_type):
        """删除过滤器"""
        saved_json = self.data_manager.get_saved_json()
        filter_data = saved_json.get("filter", {"inclusive": {}, "exclusive": {}})
        
        if filter_type in filter_data and filter_name in filter_data[filter_type]:
            del filter_data[filter_type][filter_name]
            saved_json["filter"] = filter_data
            self.data_manager.set_saved_json(saved_json)
            st.success(f"✅ 成功删除过滤器 '{filter_name}'")
        else:
            st.error(f"❌ 过滤器 '{filter_name}' 不存在")

    def _save_filters(self):
        """保存过滤器设置"""
        st.success("✅ 过滤器设置已保存")
        st.info("💡 过滤器设置会自动保存到地图数据中")

    def _render_info_preview(self, map_name, map_description, map_origin, smart_placeholders):
        """渲染信息预览"""
        # AI智能建议功能
        if self.data_manager.has_saved_json():
            if st.button("🤖 AI智能建议", type="secondary",
                            help="基于当前数据智能生成地图信息建议"):
                self._apply_ai_suggestions()

        if map_name:
            st.success(f"✅ 地图名称: {map_name}")
        else:
            st.warning("⚠️ 请设置地图名称")
            if smart_placeholders["name"] != "新地图":
                st.info(f"💡 AI建议: {smart_placeholders['name']}")

        if map_description:
            st.info(f"📝 描述字数: {len(map_description)} 字符")
        else:
            if smart_placeholders["description"] != "精选地点推荐地图":
                with st.expander("💡 查看AI建议描述", expanded=False):
                    st.write(smart_placeholders["description"])

        if map_origin:
            st.info(f"📍 数据来源: {map_origin}")
        else:
            if smart_placeholders["origin"] != "用户收集":
                st.info(f"💡 AI建议来源: {smart_placeholders['origin']}")

    def _add_filter_from_tags(self, filter_name, filter_type, tag_list):
        """从标签列表添加过滤器"""
        if not tag_list:
            st.error("❌ 没有标签可添加")
            return
        
        # 获取当前数据
        saved_json = self.data_manager.get_saved_json()
        filter_data = saved_json.get("filter", {"inclusive": {}, "exclusive": {}})
        
        # 生成唯一的过滤器名称
        base_name = filter_name
        counter = 1
        while (filter_name in filter_data.get("inclusive", {}) or 
               filter_name in filter_data.get("exclusive", {})):
            filter_name = f"{base_name}_{counter}"
            counter += 1
        
        # 添加新过滤器
        if filter_type not in filter_data:
            filter_data[filter_type] = {}
        
        filter_data[filter_type][filter_name] = tag_list
        
        # 更新数据
        saved_json["filter"] = filter_data
        self.data_manager.set_saved_json(saved_json)
        
        st.success(f"✅ 已将 {len(tag_list)} 个标签添加到过滤器 '{filter_name}'")
        st.rerun()
