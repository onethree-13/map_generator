import streamlit as st
from utils.data_manager import DataManager


class TagManagementTab:
    """标签管理标签页"""

    def __init__(self, data_manager: DataManager, processor):
        self.data_manager = data_manager
        self.processor = processor

    def render(self):
        """渲染标签管理标签页"""
        st.info("步骤4：标签管理")

        if not self.data_manager.has_saved_json():
            st.warning("暂无数据可管理，请先完成数据提取步骤。")
            return

        # 确保editing_json存在
        if not self.data_manager.has_editing_json():
            self.data_manager.copy_saved_to_editing()

        data_items = self.data_manager.get_editing_json().get("data", [])

        # 数据验证和初始化
        if not self._validate_and_initialize_data(data_items):
            return

        # 收集所有可用标签
        all_tags = self.data_manager.get_all_tags(use_editing=True)

        # 强制刷新标签列表
        self._handle_tag_refresh(all_tags)

        # 初始化选择状态
        if 'selected_locations' not in st.session_state:
            st.session_state.selected_locations = set()
        if 'selected_tags' not in st.session_state:
            st.session_state.selected_tags = set()

        st.subheader("🏷️ 批量标签管理")
        st.info("💡 选择地点和标签，然后使用下方按钮进行批量操作")

        # 主要操作区域
        self._render_selection_interface(data_items, all_tags)

        # 选择状态显示
        self._render_selection_status(data_items)

        # 批量操作按钮
        self._render_batch_operations()

        # AI标签编辑
        self._render_ai_tag_editing()

        # 标签编辑表格
        self._render_tag_editing_table()

    def _validate_and_initialize_data(self, data_items):
        """验证和初始化数据"""
        if not isinstance(data_items, list):
            st.error("❌ 数据格式错误：data字段必须是列表")
            return False

        if len(data_items) == 0:
            st.info("📭 数据列表为空，请先添加一些地点数据")
            return False

        # 确保每个数据项都有tags字段且为列表
        for i, item in enumerate(data_items):
            if not isinstance(item, dict):
                st.error(f"❌ 数据项 {i+1} 格式错误：必须是字典对象")
                return False

            if "tags" not in item:
                item["tags"] = []
            elif not isinstance(item["tags"], list):
                if isinstance(item["tags"], str):
                    item["tags"] = [item["tags"]] if item["tags"].strip() else [
                    ]
                else:
                    item["tags"] = []

        return True

    def _handle_tag_refresh(self, all_tags):
        """处理标签刷新"""
        if 'last_tag_count' not in st.session_state:
            st.session_state.last_tag_count = len(all_tags)
        elif st.session_state.last_tag_count != len(all_tags):
            st.session_state.last_tag_count = len(all_tags)
            # 标签数量改变时，清除选择状态避免错误
            if 'selected_tags' in st.session_state:
                # 只保留仍然存在的标签
                st.session_state.selected_tags = st.session_state.selected_tags.intersection(
                    set(all_tags))

    def _render_selection_interface(self, data_items, all_tags):
        """渲染选择界面"""
        left_col, right_col = st.columns([1, 1])

        with left_col:
            self._render_location_selection(data_items)

        with right_col:
            self._render_tag_selection(all_tags)

    def _render_location_selection(self, data_items):
        """渲染地点选择界面"""
        st.markdown("### 📍 选择地点")

        # 地点选择操作
        location_action_col1, location_action_col2 = st.columns(2)
        with location_action_col1:
            if st.button("✅ 全选地点", key="select_all_locations"):
                st.session_state.selected_locations = set(
                    range(len(data_items)))
        with location_action_col2:
            if st.button("❌ 取消全选", key="deselect_all_locations"):
                st.session_state.selected_locations = set()

        # 地点pill按钮
        location_cols = st.columns(3)  # 3列布局
        for i, item in enumerate(data_items):
            name = item.get("name", f"地点 {i+1}")
            with location_cols[i % 3]:
                is_selected = i in st.session_state.selected_locations
                button_type = "primary" if is_selected else "secondary"
                button_label = f"✅ {name}" if is_selected else f"⚪ {name}"

                if st.button(
                    button_label,
                    key=f"location_pill_{i}",
                    type=button_type,
                    use_container_width=True,
                    help=f"点击{'取消选择' if is_selected else '选择'} {name}"
                ):
                    if is_selected:
                        st.session_state.selected_locations.discard(i)
                    else:
                        st.session_state.selected_locations.add(i)
                    st.rerun()

    def _render_tag_selection(self, all_tags):
        """渲染标签选择界面"""
        st.markdown("### 🏷️ 选择标签")

        # 标签选择操作
        tag_action_col1, tag_action_col2, tag_action_col3 = st.columns(3)
        with tag_action_col1:
            if st.button("✅ 全选标签", key="select_all_tags"):
                st.session_state.selected_tags = set(all_tags)
        with tag_action_col2:
            if st.button("❌ 取消全选", key="deselect_all_tags"):
                st.session_state.selected_tags = set()
        with tag_action_col3:
            # 添加新标签
            new_tag = st.text_input(
                "新标签", placeholder="输入新标签", key="new_tag_input", label_visibility="collapsed")
            if st.button("➕", key="add_new_tag", disabled=not new_tag.strip()):
                if new_tag.strip() and new_tag.strip() not in all_tags:
                    all_tags.append(new_tag.strip())
                    all_tags.sort()
                    st.session_state.selected_tags.add(new_tag.strip())
                    st.rerun()

        # 标签pill按钮
        if all_tags:
            tag_cols = st.columns(3)  # 3列布局
            for i, tag in enumerate(all_tags):
                with tag_cols[i % 3]:
                    is_selected = tag in st.session_state.selected_tags
                    button_type = "primary" if is_selected else "secondary"
                    button_label = f"✅ {tag}" if is_selected else f"⚪ {tag}"

                    if st.button(
                        button_label,
                        key=f"tag_pill_{i}",
                        type=button_type,
                        use_container_width=True,
                        help=f"点击{'取消选择' if is_selected else '选择'} {tag}"
                    ):
                        if is_selected:
                            st.session_state.selected_tags.discard(tag)
                        else:
                            st.session_state.selected_tags.add(tag)
                        st.rerun()
        else:
            st.info("暂无可用标签，请在上方输入框添加新标签")

    def _render_selection_status(self, data_items):
        """渲染选择状态"""
        status_col1, status_col2 = st.columns(2)
        with status_col1:
            selected_location_names = [data_items[i].get(
                "name", f"地点 {i+1}") for i in st.session_state.selected_locations]
            st.info(
                f"已选择 {len(st.session_state.selected_locations)} 个地点: {', '.join(selected_location_names) if selected_location_names else '无'}")
        with status_col2:
            st.info(
                f"已选择 {len(st.session_state.selected_tags)} 个标签: {', '.join(st.session_state.selected_tags) if st.session_state.selected_tags else '无'}")

    def _render_batch_operations(self):
        """渲染批量操作"""
        st.markdown("### ⚡ 批量操作")
        action_col1, action_col2, action_col3 = st.columns(3)

        with action_col1:
            if st.button(
                "➕ 添加标签",
                type="primary",
                use_container_width=True,
                disabled=not st.session_state.selected_locations or not st.session_state.selected_tags,
                help="将选中的标签添加到选中的地点",
                key="batch_add_tags"
            ):
                self._execute_add_tags()

        with action_col2:
            if st.button(
                "🔄 覆写标签",
                type="secondary",
                use_container_width=True,
                disabled=not st.session_state.selected_locations,
                help="用选中的标签完全替换选中地点的所有标签",
                key="batch_overwrite_tags"
            ):
                self._execute_overwrite_tags()

        with action_col3:
            if st.button(
                "🗑️ 重置标签",
                type="secondary",
                use_container_width=True,
                disabled=not st.session_state.selected_locations,
                help="清空选中地点的所有标签",
                key="batch_clear_tags"
            ):
                self._execute_clear_tags()

    def _execute_add_tags(self):
        """执行添加标签操作"""
        editing_json = self.data_manager.get_editing_json()
        data_items = editing_json.get("data", [])

        # 为指定项目添加标签
        for index in st.session_state.selected_locations:
            if 0 <= index < len(data_items):
                current_tags = set(data_items[index].get("tags", []))
                current_tags.update(st.session_state.selected_tags)
                data_items[index]["tags"] = list(current_tags)

        self.data_manager.set_editing_json(editing_json)

        # 增加表格刷新计数器
        st.session_state.table_refresh_counter = getattr(
            st.session_state, 'table_refresh_counter', 0) + 1

        # 显示成功消息
        st.success(
            f"✅ 已为 {len(st.session_state.selected_locations)} 个地点添加 {len(st.session_state.selected_tags)} 个标签")

        # 清除选择状态
        st.session_state.selected_locations = set()
        st.session_state.selected_tags = set()

        st.rerun()

    def _execute_overwrite_tags(self):
        """执行覆写标签操作"""
        editing_json = self.data_manager.get_editing_json()
        data_items = editing_json.get("data", [])

        # 为指定项目设置标签（覆写）
        for index in st.session_state.selected_locations:
            if 0 <= index < len(data_items):
                data_items[index]["tags"] = list(
                    st.session_state.selected_tags)

        self.data_manager.set_editing_json(editing_json)

        # 增加表格刷新计数器
        st.session_state.table_refresh_counter = getattr(
            st.session_state, 'table_refresh_counter', 0) + 1

        # 显示成功消息
        st.success(f"✅ 已覆写 {len(st.session_state.selected_locations)} 个地点的标签")

        # 清除选择状态
        st.session_state.selected_locations = set()
        st.session_state.selected_tags = set()

        st.rerun()

    def _execute_clear_tags(self):
        """执行清空标签操作"""
        editing_json = self.data_manager.get_editing_json()
        data_items = editing_json.get("data", [])

        # 清空指定项目的标签
        for index in st.session_state.selected_locations:
            if 0 <= index < len(data_items):
                data_items[index]["tags"] = []

        self.data_manager.set_editing_json(editing_json)

        # 增加表格刷新计数器
        st.session_state.table_refresh_counter = getattr(
            st.session_state, 'table_refresh_counter', 0) + 1

        # 显示成功消息
        st.success(f"✅ 已重置 {len(st.session_state.selected_locations)} 个地点的标签")

        # 清除选择状态
        st.session_state.selected_locations = set()

        st.rerun()

    def _render_ai_tag_editing(self):
        """渲染AI标签编辑"""
        st.markdown("---")
        st.markdown("### 🤖 AI智能标签编辑")

        ai_instruction = st.text_area(
            "输入AI编辑指令",
            placeholder="例如：\n• 为所有餐厅类地点添加'美食'标签\n• 删除所有地点的'临时'标签\n• 将标签'咖啡店'替换为'咖啡厅'\n• 为包含'购物'标签的地点添加'商业'标签",
            height=100,
            help="使用自然语言描述您想要对标签进行的修改"
        )

        # AI编辑按钮组
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🚀 执行编辑", type="primary", use_container_width=True,
                         disabled=not ai_instruction.strip(),
                         help="执行AI标签编辑并保存到编辑版本",
                         key="ai_tag_execute_edit"):
                if ai_instruction.strip():
                    self._execute_ai_tag_editing(ai_instruction)

        with col2:
            if st.button("✅ 应用编辑", use_container_width=True,
                         disabled=not self.data_manager.has_editing_json(),
                         help="将编辑版本应用到保存版本",
                         key="ai_tag_apply_edit"):
                self._apply_tag_editing()

        with col3:
            if st.button("↩️ 撤销编辑", use_container_width=True,
                         disabled=not self.data_manager.has_editing_json(),
                         help="撤销编辑，恢复到保存版本",
                         key="ai_tag_undo_edit"):
                self._undo_tag_editing()

    def _execute_ai_tag_editing(self, ai_instruction):
        """执行AI标签编辑"""
        try:
            with st.spinner("AI正在处理标签编辑指令..."):
                # 确保editing_json存在
                if not self.data_manager.has_editing_json():
                    self.data_manager.copy_saved_to_editing()

                # 构建专门的标签编辑prompt
                current_data = self.data_manager.get_editing_json()

                tag_edit_prompt = f"""请根据用户指令修改JSON数据中的tags字段。

用户指令：{ai_instruction}

要求：
1. 只修改tags字段，不要改动其他数据
2. 确保所有tags都是字符串列表格式
3. 返回完整的JSON数据结构
4. 不要添加任何解释，只返回JSON"""

                edited_data = self.processor.ai_edit_json_data(tag_edit_prompt)

                # 更新数据到editing_json
                self.data_manager.set_editing_json(edited_data)

                st.success("✅ AI标签编辑完成！已保存到编辑版本")
                st.rerun()

        except Exception as e:
            st.error(f"❌ AI编辑失败: {str(e)}")

    def _apply_tag_editing(self):
        """应用标签编辑到保存版本"""
        self.data_manager.save_editing_to_saved()

        # 增加表格刷新计数器
        st.session_state.table_refresh_counter = getattr(
            st.session_state, 'table_refresh_counter', 0) + 1

        # 清除选择状态
        st.session_state.selected_locations = set()
        st.session_state.selected_tags = set()

        st.success("✅ 标签编辑已应用到保存版本！")
        st.rerun()

    def _undo_tag_editing(self):
        """撤销标签编辑，恢复到保存版本"""
        self.data_manager.copy_saved_to_editing()

        # 增加表格刷新计数器
        st.session_state.table_refresh_counter = getattr(
            st.session_state, 'table_refresh_counter', 0) + 1

        # 清除选择状态
        st.session_state.selected_locations = set()
        st.session_state.selected_tags = set()

        st.success("✅ 已撤销标签编辑，恢复到保存版本")
        st.rerun()

    def _render_tag_editing_table(self):
        """渲染标签编辑表格"""
        st.markdown("---")
        st.markdown("### 📊 标签编辑表格")

        # 重新获取最新的数据项，确保表格显示最新数据
        current_data_items = self.data_manager.get_editing_json().get("data", [])

        # 准备表格数据 - 始终使用最新数据
        table_data = []
        for i, item in enumerate(current_data_items):
            name = item.get("name", f"地点 {i+1}")
            tags = item.get("tags", [])
            tags_str = ", ".join(tags) if tags else ""
            table_data.append({
                "地点名称": name,
                "标签": tags_str
            })

        # 生成基于数据内容的唯一key，确保数据变化时表格能刷新
        if 'table_refresh_counter' not in st.session_state:
            st.session_state.table_refresh_counter = 0

        table_content_hash = hash(str([(item.get("name", ""), ",".join(item.get(
            "tags", []))) for item in current_data_items]) + str(st.session_state.table_refresh_counter))

        # 可编辑表格
        edited_table = st.data_editor(
            table_data,
            use_container_width=True,
            height=400,
            column_config={
                "地点名称": st.column_config.TextColumn(
                    "地点名称",
                    disabled=True,
                    width="medium"
                ),
                "标签": st.column_config.TextColumn(
                    "标签",
                    help="多个标签用逗号分隔",
                    width="large"
                )
            },
            key=f"tags_table_editor_{table_content_hash}"
        )

        # 应用表格修改
        if st.button("💾 应用表格修改", type="primary", use_container_width=True,
                        key="apply_table_modifications"):
            self._apply_table_modifications(edited_table)
            self.data_manager.save_editing_to_saved()

    def _apply_table_modifications(self, edited_table):
        """应用表格修改"""
        try:
            # 使用最新的data_items进行修改
            editing_json = self.data_manager.get_editing_json()
            latest_data_items = editing_json.get("data", [])

            for i, row in enumerate(edited_table):
                if i < len(latest_data_items):
                    tags_str = row.get("标签", "")
                    if tags_str.strip():
                        # 分割标签并清理
                        tags = [tag.strip()
                                for tag in tags_str.split(",") if tag.strip()]
                    else:
                        tags = []
                    latest_data_items[i]["tags"] = tags

            # 更新editing_json数据
            self.data_manager.set_editing_json(editing_json)

            # 增加表格刷新计数器
            st.session_state.table_refresh_counter = getattr(
                st.session_state, 'table_refresh_counter', 0) + 1

            # 清除选择状态
            st.session_state.selected_locations = set()
            st.session_state.selected_tags = set()

            st.success("✅ 表格修改已应用到JSON数据")
            st.rerun()

        except Exception as e:
            st.error(f"❌ 应用修改失败: {str(e)}")
