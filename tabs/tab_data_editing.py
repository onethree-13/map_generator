import streamlit as st
import pandas as pd
from utils.data_manager import DataManager, clean_text


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

        # 确保editing_json存在
        if not self.data_manager.has_editing_json():
            self.data_manager.copy_saved_to_editing()

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
            placeholder="例如：\n• 删除所有没有电话号码的地点\n• 将所有地址中的'街道'替换为'路'\n• 为星巴克添加简介：知名国际咖啡连锁品牌\n• 删除第2个地点\n• 添加一个新地点：名称为'测试咖啡厅'，地址为'上海市长宁区测试路123号'",
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
                        disabled=not self.data_manager.has_editing_json(),
                        help="将编辑版本应用到保存版本"):
                self._apply_editing()

        with col3:
            if st.button("↩️ 撤销编辑", use_container_width=True,
                        disabled=not self.data_manager.has_editing_json(),
                        help="撤销编辑，恢复到保存版本"):
                self._undo_editing()

    def _execute_ai_edit(self, user_instruction):
        """执行AI编辑"""
        try:
            with st.spinner("AI正在处理您的编辑指令..."):
                edited_data = self.processor.ai_edit_json_data(user_instruction)

            # 更新数据到editing_json
            self.data_manager.set_editing_json(edited_data)
            
            st.success(f"✅ 编辑成功！数据已更新为 {len(edited_data['data'])} 个地点")
            st.rerun()

        except ValueError as e:
            st.error(f"❌ 编辑失败: {str(e)}")
            if "API密钥" in str(e):
                st.info("💡 请在侧边栏中配置正确的通义千问API密钥")
        except Exception as e:
            st.error(f"❌ 编辑出错: {str(e)}")

    def _apply_editing(self):
        """应用编辑到保存版本"""
        self.data_manager.save_editing_to_saved()
        st.success("✅ 编辑已应用到保存版本！")
        st.rerun()

    def _undo_editing(self):
        """撤销编辑，恢复到保存版本"""
        self.data_manager.copy_saved_to_editing()
        st.success("✅ 已撤销编辑，恢复到保存版本")
        st.rerun()

    def _render_manual_editing(self):
        """渲染手动编辑表格"""
        st.subheader("📊 手动编辑表格")
        st.info("💡 表格支持直接编辑，修改后点击保存按钮将数据同步到保存版本")

        data_items = self.data_manager.get_editing_data_items()

        # 准备表格数据
        editable_data = []
        for i, item in enumerate(data_items):
            row = {
                "名称": item.get('name', ''),
                "地址": item.get('address', ''),
                "电话": item.get('phone', ''),
                "网站/公众号": item.get('webName', ''),
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
                    help="网站链接或微信公众号",
                    max_chars=100,
                    width="medium"
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
                    help="将表格修改保存到编辑版本和保存版本"):
            if edited_df is not None:
                self._save_table_changes(edited_df)

    def _save_table_changes(self, edited_df):
        """保存表格修改"""
        # 获取当前的数据项
        data_items = self.data_manager.get_editing_data_items()
        updated_data = []

        for i, row in enumerate(edited_df):
            # 清理和验证数据
            name = clean_text(str(row.get('名称', '')))
            address = clean_text(str(row.get('地址', '')))
            phone = clean_text(str(row.get('电话', '')))
            web_name = clean_text(str(row.get('网站/公众号', '')))
            intro = clean_text(str(row.get('简介', '')))

            # 构建数据项，保留原有坐标
            original_item = data_items[i] if i < len(data_items) else {}
            original_center = original_item.get('center', {"lat": 0.0, "lng": 0.0})

            item = {
                "name": name,
                "address": address,
                "phone": phone,
                "webName": web_name,
                "intro": intro,
                "tags": original_item.get('tags', []),
                "center": original_center
            }

            # 只保留有效的项目（至少有名称或地址）
            if item["name"].strip() or item["address"].strip():
                updated_data.append(item)

        # 更新editing_json和saved_json
        current_editing = self.data_manager.get_editing_json()
        current_editing["data"] = updated_data
        self.data_manager.set_editing_json(current_editing)
        self.data_manager.save_editing_to_saved()

        st.success(f"✅ 修改已保存！共保存 {len(updated_data)} 个地点")
        st.rerun()
