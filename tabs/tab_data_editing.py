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
import pandas as pd
from utils.data_manager import DataManager, clean_text, clean_url, validate_url


class DataEditingTab:
    """数据编辑标签页"""

    def __init__(self, data_manager: DataManager, processor):
        self.data_manager = data_manager
        self.processor = processor

    def render(self):
        """渲染数据编辑标签页"""
        st.info("步骤3：数据确认与编辑")

        if not self.data_manager.has_saved_json():
            st.warning("暂无数据可编辑，请先完成数据提取步骤。")
            return

        # AI智能编辑区域
        self._render_ai_editing()

        st.markdown("---")

        # 手动编辑表格
        self._render_manual_editing()

    def _render_ai_editing(self):
        """渲染AI智能编辑区域"""
        st.subheader("🤖 AI智能编辑")

        # AI编辑输入框
        user_instruction = st.text_area(
            "请输入编辑指令：",
            placeholder="例如：\n• 删除所有没有电话号码的地点\n• 将所有地址中的'街道'替换为'路'\n• 为星巴克添加简介：知名国际咖啡连锁品牌\n• 为所有餐厅类地点添加标签：餐饮\n• 删除第2个地点\n• 添加一个新地点：名称为'测试咖啡厅'，地址为'上海市长宁区测试路123号'，标签为'咖啡,饮品'",
            height=120,
            help="用自然语言描述您想要对数据进行的修改"
        )

        # AI编辑按钮组
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 执行编辑", type="primary", use_container_width=True, 
                        disabled=not user_instruction.strip(),
                        help="执行AI编辑并保存到编辑版本"):
                if user_instruction.strip():
                    self._execute_ai_edit(user_instruction)

        with col2:
            if st.button("✅ 应用编辑", use_container_width=True,
                        disabled=not self.data_manager.has_pending_edits(),
                        help="将编辑版本应用到保存版本"):
                self._apply_editing()

        with col3:
            if st.button("↩️ 撤销编辑", use_container_width=True,
                        disabled=not self.data_manager.has_pending_edits(),
                        help="撤销编辑，恢复到保存版本"):
                self._undo_editing()

        # 显示编辑状态
        if self.data_manager.has_pending_edits():
            st.info("💡 有AI编辑结果待确认，请点击'应用编辑'保存，或点击'撤销编辑'取消")
            
            # 显示编辑前后对比
            with st.expander("📊 查看编辑前后对比", expanded=False):
                col_before, col_after = st.columns(2)
                
                with col_before:
                    st.write("**编辑前（保存版本）：**")
                    saved_stats = self.data_manager.get_data_statistics(use_editing=False)
                    st.write(f"• 总地点数: {saved_stats['total_locations']}")
                    st.write(f"• 有地址: {saved_stats['has_address']}")
                    st.write(f"• 有电话: {saved_stats['has_phone']}")
                    st.write(f"• 有标签: {saved_stats['has_tags']}")
                    
                with col_after:
                    st.write("**编辑后（待确认版本）：**")
                    editing_stats = self.data_manager.get_data_statistics(use_editing=True)
                    st.write(f"• 总地点数: {editing_stats['total_locations']}")
                    st.write(f"• 有地址: {editing_stats['has_address']}")
                    st.write(f"• 有电话: {editing_stats['has_phone']}")
                    st.write(f"• 有标签: {editing_stats['has_tags']}")
                    
                    # 显示变化
                    location_diff = editing_stats['total_locations'] - saved_stats['total_locations']
                    if location_diff > 0:
                        st.success(f"📈 增加了 {location_diff} 个地点")
                    elif location_diff < 0:
                        st.warning(f"📉 减少了 {abs(location_diff)} 个地点")
                    else:
                        st.info("📊 地点数量无变化")
                    
                    # 显示标签变化
                    tag_diff = editing_stats['has_tags'] - saved_stats['has_tags']
                    if tag_diff > 0:
                        st.success(f"🏷️ 增加了 {tag_diff} 个有标签的地点")
                    elif tag_diff < 0:
                        st.warning(f"🏷️ 减少了 {abs(tag_diff)} 个有标签的地点")
                    else:
                        st.info("🏷️ 标签地点数量无变化")

    def _execute_ai_edit(self, user_instruction):
        """执行AI编辑"""
        progress_placeholder = st.empty()
        
        try:
            with st.spinner("AI正在处理您的编辑指令..."):
                # 开始编辑：将saved_json复制到editing_json
                self.data_manager.start_editing()
                
                edited_data = self.processor.ai_edit_json_data(user_instruction, progress_placeholder)

            progress_placeholder.empty()
            # 更新数据到editing_json
            self.data_manager.set_editing_json(edited_data)
            
            st.success(f"✅ 编辑成功！数据已更新为 {len(edited_data['data'])} 个地点，请确认后应用")
            st.rerun()

        except ValueError as e:
            progress_placeholder.empty()
            st.error(f"❌ 编辑失败: {str(e)}")
            if "API密钥" in str(e):
                st.info("💡 请在侧边栏中配置正确的通义千问API密钥")
        except Exception as e:
            progress_placeholder.empty()
            st.error(f"❌ 编辑出错: {str(e)}")

    def _apply_editing(self):
        """应用编辑到保存版本"""
        self.data_manager.apply_edits()
        st.success("✅ 编辑已应用到保存版本！")
        st.rerun()

    def _undo_editing(self):
        """撤销编辑，恢复到保存版本"""
        self.data_manager.discard_edits()
        st.success("✅ 已撤销编辑，恢复到保存版本")
        st.rerun()

    def _render_manual_editing(self):
        """渲染手动编辑表格"""
        st.subheader("📊 手动编辑表格")
        st.info("💡 表格支持直接编辑，修改后点击保存按钮将数据直接保存到保存版本")

        # 从saved_json读取数据进行显示和编辑
        data_items = self.data_manager.get_data_items(use_editing=False)

        # 准备表格数据
        editable_data = []
        for i, item in enumerate(data_items):
            # 处理标签：将标签数组转换为逗号分割的字符串
            tags = item.get('tags', [])
            tags_str = ", ".join(tags) if tags else ""
            
            row = {
                "名称": item.get('name', ''),
                "地址": item.get('address', ''),
                "电话": item.get('phone', ''),
                "网站/公众号": item.get('webName', ''),
                "网站链接": item.get('webLink', ''),
                "标签": tags_str,
                "简介": item.get('intro', '')
            }
            editable_data.append(row)

        # 确保至少有一行数据用于编辑
        if not editable_data:
            editable_data = [{
                "名称": "",
                "地址": "",
                "电话": "",
                "网站/公众号": "",
                "网站链接": "",
                "标签": "",
                "简介": ""
            }]

        # 可编辑数据表格
        edited_df = st.data_editor(
            editable_data,
            use_container_width=True,
            height=400,
            num_rows="dynamic",
            column_config={
                "名称": st.column_config.TextColumn(
                    "名称",
                    help="地点或商家的名称",
                    max_chars=100,
                    width="medium"
                ),
                "地址": st.column_config.TextColumn(
                    "地址",
                    help="详细地址信息",
                    max_chars=200,
                    width="large"
                ),
                "电话": st.column_config.TextColumn(
                    "电话",
                    help="联系电话",
                    max_chars=25,
                    width="small"
                ),
                "网站/公众号": st.column_config.TextColumn(
                    "网站/公众号",
                    help="网站名称或微信公众号",
                    max_chars=100,
                    width="medium"
                ),
                "网站链接": st.column_config.TextColumn(
                    "网站链接",
                    help="网站URL或相关链接",
                    max_chars=200,
                    width="medium"
                ),
                "标签": st.column_config.TextColumn(
                    "标签",
                    help="多个标签用逗号分隔，如：餐厅, 川菜, 网红店",
                    max_chars=300,
                    width="large"
                ),
                "简介": st.column_config.TextColumn(
                    "简介",
                    help="地点描述或简介",
                    max_chars=500,
                    width="large"
                )
            },
            key="manual_data_editor"
        )

        # 保存修改按钮
        if st.button("💾 保存修改", type="primary", use_container_width=True,
                    help="将表格修改直接保存到保存版本"):
            if edited_df is not None:
                self._save_table_changes(edited_df)

    def _save_table_changes(self, edited_df):
        """保存表格修改"""
        # 获取当前的saved_json数据项
        saved_json = self.data_manager.get_saved_json()
        data_items = saved_json.get("data", [])
        updated_data = []
        validation_errors = []

        for i, row in enumerate(edited_df):
            # 清理和验证数据
            name = clean_text(str(row.get('名称', '')))
            address = clean_text(str(row.get('地址', '')))
            phone = clean_text(str(row.get('电话', '')))
            web_name = clean_text(str(row.get('网站/公众号', '')))
            web_link = clean_url(str(row.get('网站链接', '')))
            intro = clean_text(str(row.get('简介', '')))
            
            # 处理标签：将逗号分割的字符串转换为标签数组
            tags_str = str(row.get('标签', '')).strip()
            if tags_str:
                # 分割标签并清理每个标签
                tags = [clean_text(tag) for tag in tags_str.split(",") if clean_text(tag)]
            else:
                tags = []

            # 验证webLink
            if web_link:
                is_valid_url, url_error = validate_url(web_link)
                if not is_valid_url:
                    validation_errors.append(f"第{i+1}行网站链接格式错误：{url_error}")

            # 构建数据项，保留原有坐标
            original_item = data_items[i] if i < len(data_items) else {}
            original_center = original_item.get('center', {"lat": 0.0, "lng": 0.0})

            item = {
                "name": name,
                "address": address,
                "phone": phone,
                "webName": web_name,
                "webLink": web_link,
                "intro": intro,
                "tags": tags,
                "center": original_center
            }

            # 只保留有效的项目（至少有名称或地址）
            if item["name"].strip() or item["address"].strip():
                updated_data.append(item)

        # 如果有验证错误，显示警告但仍然保存
        if validation_errors:
            st.warning("⚠️ 发现以下格式问题，已自动修正：")
            for error in validation_errors:
                st.write(f"• {error}")

        # 直接更新saved_json
        saved_json["data"] = updated_data
        self.data_manager.set_saved_json(saved_json)

        # 计算标签相关的统计信息
        tag_count = sum(1 for item in updated_data if item.get("tags"))
        total_tags = sum(len(item.get("tags", [])) for item in updated_data)

        success_msg = f"✅ 修改已保存！共保存 {len(updated_data)} 个地点"
        if tag_count > 0:
            success_msg += f"，其中 {tag_count} 个地点有标签（共 {total_tags} 个标签）"
        if validation_errors:
            success_msg += f"，{len(validation_errors)} 个网址已自动修正格式"
        
        st.success(success_msg)
        st.rerun()
