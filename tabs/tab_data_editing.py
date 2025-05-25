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

        # 将saved_json复制到editing_json进行编辑
        if not self.data_manager.has_editing_json():
            self.data_manager.copy_saved_to_editing()

        # 验证和清理数据
        self._validate_and_clean_data()

        data_items = self.data_manager.get_editing_data_items()

        if not data_items:
            st.warning("暂无数据可编辑，请先完成数据提取步骤。")
            return

        # AI对话编辑区域
        self._render_ai_editing()

        st.markdown("---")

        # 表格形式显示数据
        self._render_data_table()

        # 手动编辑区域（保留作为备选）
        self._render_manual_editing()

        # 添加新地点（保留）
        self._render_add_new_item()
        
        # 保存编辑结果
        self._render_save_editing()
    
    def _validate_and_clean_data(self):
        """验证和清理编辑数据"""
        editing_json = self.data_manager.get_editing_json()
        data_items = editing_json.get("data", [])
        
        cleaned_items = []
        issues_found = []
        
        for i, item in enumerate(data_items):
            # 确保item是字典
            if not isinstance(item, dict):
                issues_found.append(f"地点 {i+1}: 数据格式错误，已跳过")
                continue
            
            # 清理和标准化数据项
            cleaned_item = self._clean_data_item(item, i+1)
            if cleaned_item:
                cleaned_items.append(cleaned_item)
            else:
                issues_found.append(f"地点 {i+1}: 数据无效，已跳过")
        
        # 更新清理后的数据
        editing_json["data"] = cleaned_items
        self.data_manager.set_editing_json(editing_json)
        
        # 显示清理结果
        if issues_found:
            with st.expander("⚠️ 数据清理报告", expanded=False):
                st.warning(f"发现 {len(issues_found)} 个数据问题：")
                for issue in issues_found:
                    st.write(f"• {issue}")
                st.info(f"✅ 成功清理 {len(cleaned_items)} 个有效地点数据")
    
    def _clean_data_item(self, item: dict, index: int) -> dict:
        """清理单个数据项"""
        try:
            # 基础字段清理
            cleaned_item = {
                "name": self._clean_text_field(item.get("name", ""), f"地点 {index}"),
                "address": self._clean_text_field(item.get("address", ""), ""),
                "phone": self._clean_text_field(item.get("phone", ""), ""),
                "webName": self._clean_text_field(item.get("webName", ""), ""),
                "intro": self._clean_text_field(item.get("intro", ""), ""),
                "tags": self._clean_tags_field(item.get("tags", [])),
                "center": self._clean_center_field(item.get("center", {}))
            }
            
            # 验证必要字段：至少需要名称或地址
            if not cleaned_item["name"].strip() and not cleaned_item["address"].strip():
                return None
            
            return cleaned_item
            
        except Exception as e:
            st.warning(f"清理地点 {index} 数据时出错: {str(e)}")
            return None
    
    def _clean_text_field(self, value, default: str = "") -> str:
        """清理文本字段"""
        if value is None:
            return default
        if not isinstance(value, str):
            return str(value).strip() if value else default
        return clean_text(value) if value.strip() else default
    
    def _clean_tags_field(self, tags) -> list:
        """清理标签字段"""
        if not tags:
            return []
        
        if isinstance(tags, str):
            # 如果是字符串，尝试分割
            if tags.strip():
                return [tag.strip() for tag in tags.split(",") if tag.strip()]
            return []
        
        if isinstance(tags, list):
            # 清理列表中的标签
            cleaned_tags = []
            for tag in tags:
                if isinstance(tag, str) and tag.strip():
                    cleaned_tags.append(tag.strip())
                elif tag and not isinstance(tag, str):
                    cleaned_tags.append(str(tag).strip())
            return cleaned_tags
        
        return []
    
    def _clean_center_field(self, center) -> dict:
        """清理坐标字段"""
        if not isinstance(center, dict):
            return {"lat": 0.0, "lng": 0.0}
        
        try:
            lat = float(center.get("lat", 0.0)) if center.get("lat") not in [None, "", "null"] else 0.0
            lng = float(center.get("lng", 0.0)) if center.get("lng") not in [None, "", "null"] else 0.0
            
            # 验证坐标范围
            if not (-90 <= lat <= 90):
                lat = 0.0
            if not (-180 <= lng <= 180):
                lng = 0.0
                
            return {"lat": lat, "lng": lng}
        except (ValueError, TypeError):
            return {"lat": 0.0, "lng": 0.0}
    
    def _safe_get_text(self, item: dict, key: str, default: str = "") -> str:
        """安全获取文本字段"""
        value = item.get(key)
        if value is None:
            return default
        if not isinstance(value, str):
            return str(value).strip() if value else default
        return value.strip() if value.strip() else default
    
    def _safe_get_number(self, item: dict, key: str, default: float = 0.0) -> float:
        """安全获取数字字段"""
        value = item.get(key)
        if value is None or value == "":
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _safe_clean_text(self, value) -> str:
        """安全清理文本值"""
        if value is None:
            return ""
        if not isinstance(value, str):
            value = str(value)
        return clean_text(value) if value.strip() else ""
    
    def _safe_parse_coordinate(self, value, min_val: float, max_val: float) -> float:
        """安全解析坐标值"""
        if value is None or value == "":
            return 0.0
        try:
            coord = float(value)
            # 验证坐标范围
            if min_val <= coord <= max_val:
                return coord
            else:
                return 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def _render_ai_editing(self):
        """渲染AI智能编辑区域"""
        st.subheader("🤖 AI智能编辑")
        
        # 创建对话历史
        if 'edit_chat_history' not in st.session_state:
            st.session_state.edit_chat_history = []
        
        # 显示对话历史
        if st.session_state.edit_chat_history:
            with st.expander("💬 编辑历史", expanded=False):
                for i, (instruction, result) in enumerate(st.session_state.edit_chat_history):
                    st.markdown(f"**指令 {i+1}:** {instruction}")
                    if result.startswith("✅"):
                        st.success(result)
                    else:
                        st.error(result)
                    st.markdown("---")
        
        # AI编辑输入框
        col1, col2 = st.columns([3, 1])
        
        with col1:
            user_instruction = st.text_area(
                "请输入编辑指令：",
                placeholder="例如：\n• 删除所有没有电话号码的地点\n• 将所有地址中的'街道'替换为'路'\n• 为星巴克添加简介：知名国际咖啡连锁品牌\n• 删除第2个地点\n• 添加一个新地点：名称为'测试咖啡厅'，地址为'上海市长宁区测试路123号'",
                height=120,
                help="用自然语言描述您想要对数据进行的修改"
            )
        
        with col2:
            st.markdown("**💡 编辑示例:**")
            if st.button("🗑️ 删除空数据", use_container_width=True, help="删除名称和地址都为空的地点"):
                user_instruction = "删除所有名称和地址都为空的地点"
                st.session_state.temp_instruction = user_instruction
                
            if st.button("📞 补充信息", use_container_width=True, help="为缺少信息的地点添加提示"):
                user_instruction = "为所有没有电话号码的地点在简介中添加'联系方式待补充'"
                st.session_state.temp_instruction = user_instruction
                
            if st.button("🏷️ 规范地址", use_container_width=True, help="规范地址格式"):
                user_instruction = "统一地址格式，确保所有地址都以'上海市'开头"
                st.session_state.temp_instruction = user_instruction
                
            # 如果有临时指令，自动填入
            if hasattr(st.session_state, 'temp_instruction'):
                user_instruction = st.session_state.temp_instruction
                del st.session_state.temp_instruction
                st.rerun()
        
        # 执行AI编辑
        if st.button("🚀 执行AI编辑", type="primary", disabled=not user_instruction.strip()):
            if user_instruction.strip():
                self._execute_ai_edit(user_instruction)
    
    def _execute_ai_edit(self, user_instruction):
        """执行AI编辑"""
        try:
            with st.spinner("AI正在处理您的编辑指令..."):
                edited_data = self.processor.ai_edit_json_data(user_instruction)
            
            # 更新数据到editing_json
            self.data_manager.set_editing_json(edited_data)
            
            # 记录编辑历史
            success_msg = f"✅ 编辑成功！数据已更新为 {len(edited_data['data'])} 个地点"
            st.session_state.edit_chat_history.append((user_instruction, success_msg))
            
            st.success(success_msg)
            st.rerun()
            
        except ValueError as e:
            error_msg = f"❌ 编辑失败: {str(e)}"
            st.session_state.edit_chat_history.append((user_instruction, error_msg))
            st.error(error_msg)
            if "API密钥" in str(e):
                st.info("💡 请在侧边栏中配置正确的通义千问API密钥")
        except Exception as e:
            error_msg = f"❌ 编辑出错: {str(e)}"
            st.session_state.edit_chat_history.append((user_instruction, error_msg))
            st.error(error_msg)
    
    def _render_data_table(self):
        """渲染数据管理表格"""
        st.subheader("📊 数据管理表格")
        st.info("💡 表格支持直接编辑，修改后数据将实时更新到JSON中。点击表格底部的➕按钮添加新行。")
        
        data_items = self.data_manager.get_editing_data_items()
        
        # 准备可编辑的表格数据，增强缺省值处理
        editable_data = []
        for i, item in enumerate(data_items):
            # 安全获取各字段值，处理各种缺省情况
            name = self._safe_get_text(item, 'name', f'地点 {i+1}')
            address = self._safe_get_text(item, 'address', '')
            phone = self._safe_get_text(item, 'phone', '')
            web_name = self._safe_get_text(item, 'webName', '')
            intro = self._safe_get_text(item, 'intro', '')
            
            # 安全获取坐标
            center = item.get('center', {}) if isinstance(item.get('center'), dict) else {}
            lat = self._safe_get_number(center, 'lat', 0.0)
            lng = self._safe_get_number(center, 'lng', 0.0)
            
            row = {
                "名称": name,
                "地址": address,
                "电话": phone,
                "网站/公众号": web_name,
                "简介": intro,
                "纬度": lat,
                "经度": lng
            }
            editable_data.append(row)
        
        # 使用可编辑的数据表格
        if editable_data or st.button("📝 开始编辑数据表格", type="secondary"):
            # 确保至少有一行空数据用于编辑
            if not editable_data:
                editable_data = [{
                    "名称": "",
                    "地址": "",
                    "电话": "",
                    "网站/公众号": "",
                    "简介": "",
                    "纬度": 0.0,
                    "经度": 0.0
                }]
            
            edited_df = st.data_editor(
                editable_data,
                use_container_width=True,
                height=400,
                num_rows="dynamic",  # 允许添加/删除行
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
                        max_chars=50,
                        width="medium"
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
                    ),
                    "纬度": st.column_config.NumberColumn(
                        "纬度",
                        help="地理坐标纬度 (留空或0表示未获取)",
                        min_value=-90.0,
                        max_value=90.0,
                        step=0.000001,
                        format="%.6f",
                        width="small"
                    ),
                    "经度": st.column_config.NumberColumn(
                        "经度", 
                        help="地理坐标经度 (留空或0表示未获取)",
                        min_value=-180.0,
                        max_value=180.0,
                        step=0.000001,
                        format="%.6f",
                        width="small"
                    )
                },
                key="data_editor"
            )
            
            # 实时更新JSON数据
            if edited_df is not None:
                self._update_data_from_table(edited_df)
                self._render_table_status()
        
        # 批量操作按钮
        self._render_batch_operations()
    
    def _update_data_from_table(self, edited_df):
        """从表格更新数据，增强缺省值处理"""
        updated_data = []
        
        # 处理编辑后的数据 - edited_df是list类型，不是DataFrame
        for i, row in enumerate(edited_df):
            # 安全获取和清理各字段
            name = self._safe_clean_text(row.get('名称', ''))
            address = self._safe_clean_text(row.get('地址', ''))
            phone = self._safe_clean_text(row.get('电话', ''))
            web_name = self._safe_clean_text(row.get('网站/公众号', ''))
            intro = self._safe_clean_text(row.get('简介', ''))
            
            # 安全处理坐标
            lat = self._safe_parse_coordinate(row.get('纬度', 0.0), -90, 90)
            lng = self._safe_parse_coordinate(row.get('经度', 0.0), -180, 180)
            
            # 构建数据项，确保所有必要字段都存在
            item = {
                "name": name if name else f"地点 {i+1}",  # 如果名称为空，提供默认名称
                "address": address,
                "phone": phone,
                "webName": web_name,
                "intro": intro,
                "tags": [],  # 确保tags字段存在
                "center": {
                    "lat": lat,
                    "lng": lng
                }
            }
            
            # 只保留有效的项目（至少有名称或地址）
            if item["name"].strip() or item["address"].strip():
                updated_data.append(item)
        
        # 更新editing_json数据
        current_editing = self.data_manager.get_editing_json()
        current_editing["data"] = updated_data
        self.data_manager.set_editing_json(current_editing)
    
    def _render_table_status(self):
        """渲染表格状态，增强数据完整性显示"""
        data_items = self.data_manager.get_editing_data_items()
        
        if not data_items:
            st.info("📭 暂无数据")
            return
        
        # 计算数据完整性统计
        total_count = len(data_items)
        has_names = sum(1 for item in data_items if self._safe_get_text(item, "name", "").strip())
        has_addresses = sum(1 for item in data_items if self._safe_get_text(item, "address", "").strip())
        has_phones = sum(1 for item in data_items if self._safe_get_text(item, "phone", "").strip())
        has_coords = sum(1 for item in data_items 
                        if self._safe_get_number(item.get("center", {}), "lat", 0.0) != 0 
                        and self._safe_get_number(item.get("center", {}), "lng", 0.0) != 0)
        has_intros = sum(1 for item in data_items if self._safe_get_text(item, "intro", "").strip())
        has_webs = sum(1 for item in data_items if self._safe_get_text(item, "webName", "").strip())
        
        # 显示统计信息
        st.markdown("### 📊 数据完整性统计")
        
        col_status1, col_status2, col_status3, col_status4 = st.columns(4)
        with col_status1:
            st.metric("📍 总地点数", total_count)
            completion_rate = (has_names / total_count * 100) if total_count > 0 else 0
            st.metric("🏷️ 有名称", f"{has_names} ({completion_rate:.0f}%)")
        
        with col_status2:
            completion_rate = (has_addresses / total_count * 100) if total_count > 0 else 0
            st.metric("📍 有地址", f"{has_addresses} ({completion_rate:.0f}%)")
            completion_rate = (has_phones / total_count * 100) if total_count > 0 else 0
            st.metric("📞 有电话", f"{has_phones} ({completion_rate:.0f}%)")
        
        with col_status3:
            completion_rate = (has_coords / total_count * 100) if total_count > 0 else 0
            st.metric("🌐 有坐标", f"{has_coords} ({completion_rate:.0f}%)")
            completion_rate = (has_intros / total_count * 100) if total_count > 0 else 0
            st.metric("📝 有简介", f"{has_intros} ({completion_rate:.0f}%)")
        
        with col_status4:
            completion_rate = (has_webs / total_count * 100) if total_count > 0 else 0
            st.metric("🌐 有网站", f"{has_webs} ({completion_rate:.0f}%)")
            
            # 整体完整度
            overall_completion = ((has_names + has_addresses + has_coords) / (total_count * 3) * 100) if total_count > 0 else 0
            st.metric("✅ 整体完整度", f"{overall_completion:.0f}%")
        
        # 数据质量提示
        if total_count > 0:
            issues = []
            if has_names < total_count:
                issues.append(f"{total_count - has_names} 个地点缺少名称")
            if has_addresses < total_count:
                issues.append(f"{total_count - has_addresses} 个地点缺少地址")
            if has_coords < total_count:
                issues.append(f"{total_count - has_coords} 个地点缺少坐标")
            
            if issues:
                with st.expander("⚠️ 数据质量提示", expanded=False):
                    for issue in issues:
                        st.write(f"• {issue}")
                    st.info("💡 建议使用AI编辑功能或手动编辑来完善数据")
    
    def _render_batch_operations(self):
        """渲染批量操作"""
        st.markdown("---")
        st.subheader("🔧 批量操作")
        
        col_batch1, col_batch2, col_batch3, col_batch4 = st.columns(4)
        
        with col_batch1:
            if st.button("🗑️ 清空坐标", use_container_width=True, help="清空所有地点的坐标信息"):
                data_items = self.data_manager.get_editing_data_items()
                for item in data_items:
                    item["center"] = {"lat": 0, "lng": 0}
                st.success("✅ 已清空所有坐标")
                st.rerun()
        
        with col_batch2:
            if st.button("📞 清空电话", use_container_width=True, help="清空所有地点的电话信息"):
                data_items = self.data_manager.get_editing_data_items()
                for item in data_items:
                    item["phone"] = ""
                st.success("✅ 已清空所有电话")
                st.rerun()
        
        with col_batch3:
            if st.button("🔄 重新获取坐标", use_container_width=True, help="重新获取所有地点的坐标"):
                if self.processor.geo_service:
                    try:
                        with st.spinner("正在批量获取坐标..."):
                            self.processor.get_coordinates_with_progress()
                        st.success("✅ 坐标获取完成")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 坐标获取失败: {str(e)}")
                else:
                    st.error("❌ 地理编码服务未初始化")
        
        with col_batch4:
            if st.button("🔧 修复缺省数据", use_container_width=True, help="自动修复和补全缺省的数据字段"):
                self._fix_missing_data()
    
    def _fix_missing_data(self):
        """修复和补全缺省的数据字段"""
        editing_json = self.data_manager.get_editing_json()
        data_items = editing_json.get("data", [])
        
        fixed_count = 0
        
        for i, item in enumerate(data_items):
            item_fixed = False
            
            # 确保所有必要字段存在
            if "name" not in item or not self._safe_get_text(item, "name", "").strip():
                item["name"] = f"地点 {i+1}"
                item_fixed = True
            
            if "address" not in item:
                item["address"] = ""
                item_fixed = True
            
            if "phone" not in item:
                item["phone"] = ""
                item_fixed = True
            
            if "webName" not in item:
                item["webName"] = ""
                item_fixed = True
            
            if "intro" not in item:
                item["intro"] = ""
                item_fixed = True
            
            if "tags" not in item:
                item["tags"] = []
                item_fixed = True
            elif not isinstance(item["tags"], list):
                # 修复非列表类型的tags
                if isinstance(item["tags"], str):
                    item["tags"] = [tag.strip() for tag in item["tags"].split(",") if tag.strip()]
                else:
                    item["tags"] = []
                item_fixed = True
            
            if "center" not in item or not isinstance(item["center"], dict):
                item["center"] = {"lat": 0.0, "lng": 0.0}
                item_fixed = True
            else:
                center = item["center"]
                if "lat" not in center:
                    center["lat"] = 0.0
                    item_fixed = True
                if "lng" not in center:
                    center["lng"] = 0.0
                    item_fixed = True
                
                # 验证坐标值
                try:
                    lat = float(center["lat"])
                    if not (-90 <= lat <= 90):
                        center["lat"] = 0.0
                        item_fixed = True
                except (ValueError, TypeError):
                    center["lat"] = 0.0
                    item_fixed = True
                
                try:
                    lng = float(center["lng"])
                    if not (-180 <= lng <= 180):
                        center["lng"] = 0.0
                        item_fixed = True
                except (ValueError, TypeError):
                    center["lng"] = 0.0
                    item_fixed = True
            
            if item_fixed:
                fixed_count += 1
        
        # 更新数据
        self.data_manager.set_editing_json(editing_json)
        
        if fixed_count > 0:
            st.success(f"✅ 已修复 {fixed_count} 个地点的缺省数据字段")
        else:
            st.info("✅ 所有数据字段都完整，无需修复")
        
        st.rerun()
    
    def _render_manual_editing(self):
        """渲染手动编辑区域"""
        with st.expander("✏️ 单项详细编辑 (备选方式)", expanded=False):
            data_items = self.data_manager.get_editing_data_items()
            
            # 选择要编辑的项目
            if data_items:
                item_options = [f"地点 {i+1}: {item.get('name', '未知地点')}" for i, item in enumerate(data_items)]
                selected_index = st.selectbox(
                    "选择要编辑的地点：",
                    range(len(item_options)),
                    format_func=lambda x: item_options[x],
                    help="选择一个地点进行详细编辑"
                )
                
                if selected_index is not None:
                    item = data_items[selected_index]
                    
                    # 创建编辑表单
                    with st.form(f"edit_form_{selected_index}", clear_on_submit=False):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            new_name = st.text_input("名称", value=item.get('name', ''))
                            new_address = st.text_input("地址", value=item.get('address', ''))
                            new_phone = st.text_input("电话", value=item.get('phone', ''))
                            new_web = st.text_input("网站/公众号", value=item.get('webName', ''))
                            new_intro = st.text_area("简介", value=item.get('intro', ''), height=100)
                        
                        with col2:
                            st.subheader("🗺️ 坐标信息")
                            center = item.get('center', {})
                            lat = center.get('lat', 0)
                            lng = center.get('lng', 0)
                            
                            if lat != 0 and lng != 0:
                                st.success("✅ 已有坐标")
                                st.write(f"纬度: {lat:.6f}")
                                st.write(f"经度: {lng:.6f}")
                            else:
                                st.warning("❌ 暂无坐标")
                        
                        # 提交按钮
                        col_save, col_delete = st.columns([1, 1])
                        
                        with col_save:
                            if st.form_submit_button("💾 保存修改", type="primary", use_container_width=True):
                                # 更新数据
                                updated_item = {
                                    'name': clean_text(new_name),
                                    'address': clean_text(new_address),
                                    'phone': clean_text(new_phone),
                                    'webName': clean_text(new_web),
                                    'intro': clean_text(new_intro),
                                    'center': item.get('center', {"lat": 0, "lng": 0})
                                }
                                self.data_manager.update_editing_data_item(selected_index, updated_item)
                                st.success("✅ 修改已保存！")
                                st.rerun()
                        
                        with col_delete:
                            if st.form_submit_button("🗑️ 删除地点", type="secondary", use_container_width=True):
                                self.data_manager.remove_editing_data_item(selected_index)
                                st.success("✅ 地点已删除！")
                                st.rerun()
    
    def _render_add_new_item(self):
        """渲染添加新地点区域"""
        with st.expander("➕ 快速添加新地点", expanded=False):
            with st.form("add_new_item", clear_on_submit=True):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    add_name = st.text_input("名称", placeholder="请输入地点名称")
                    add_address = st.text_input("地址", placeholder="请输入详细地址")
                    add_phone = st.text_input("电话", placeholder="请输入联系电话")
                    add_web = st.text_input("网站/公众号", placeholder="请输入网站或公众号")
                    add_intro = st.text_area("简介", placeholder="请输入简介描述", height=80)
                
                with col2:
                    st.info("💡 也可以直接在上方表格底部点击➕按钮添加新行")
                    
                    if st.form_submit_button("➕ 添加地点", type="primary", use_container_width=True):
                        if add_name.strip() or add_address.strip():
                            new_item = {
                                "name": clean_text(add_name),
                                "address": clean_text(add_address),
                                "phone": clean_text(add_phone),
                                "webName": clean_text(add_web),
                                "intro": clean_text(add_intro),
                                "center": {"lat": 0, "lng": 0}
                            }
                            self.data_manager.add_editing_data_item(new_item)
                            st.success("✅ 新地点已添加！")
                            st.rerun()
                        else:
                            st.error("❌ 请至少填写名称或地址")
    
    def _render_save_editing(self):
        """渲染保存编辑结果区域"""
        st.markdown("---")
        st.subheader("💾 保存编辑结果")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("💾 保存所有修改", type="primary", use_container_width=True, help="将当前编辑的数据保存为最终版本"):
                self.data_manager.save_editing_to_saved()
                st.success("✅ 所有修改已保存！")
                st.info("💡 您可以继续在其他标签页中使用这些数据")
                st.rerun()
        
        with col2:
            if st.button("🔄 重置编辑", use_container_width=True, help="放弃当前修改，恢复到保存的版本"):
                self.data_manager.copy_saved_to_editing()
                st.success("✅ 已重置到保存的版本")
                st.rerun()
        
        with col3:
            if st.button("📊 对比版本", use_container_width=True, help="查看编辑版本与保存版本的差异"):
                self._show_version_comparison()
    
    def _show_version_comparison(self):
        """显示版本对比"""
        saved_stats = self.data_manager.get_data_statistics(use_editing=False)
        editing_stats = self.data_manager.get_data_statistics(use_editing=True)
        
        st.info("**版本对比:**")
        
        col_saved, col_editing = st.columns(2)
        
        with col_saved:
            st.markdown("**📁 保存版本:**")
            st.write(f"- 总地点数: {saved_stats['total_locations']}")
            st.write(f"- 有名称: {saved_stats['has_name']}")
            st.write(f"- 有地址: {saved_stats['has_address']}")
            st.write(f"- 有坐标: {saved_stats['has_coordinates']}")
        
        with col_editing:
            st.markdown("**✏️ 编辑版本:**")
            st.write(f"- 总地点数: {editing_stats['total_locations']}")
            st.write(f"- 有名称: {editing_stats['has_name']}")
            st.write(f"- 有地址: {editing_stats['has_address']}")
            st.write(f"- 有坐标: {editing_stats['has_coordinates']}")
        
        # 显示差异
        diff_count = editing_stats['total_locations'] - saved_stats['total_locations']
        if diff_count > 0:
            st.success(f"✅ 编辑版本比保存版本多 {diff_count} 个地点")
        elif diff_count < 0:
            st.warning(f"⚠️ 编辑版本比保存版本少 {abs(diff_count)} 个地点")
        else:
            st.info("📊 两个版本的地点数量相同") 