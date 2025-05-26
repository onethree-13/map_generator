import streamlit as st
from utils.data_manager import DataManager


class MapInfoTab:
    """地图信息标签页"""

    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager

    def render(self):
        """渲染地图信息标签页"""
        st.info("步骤2：地图基本信息设置")

        # 基本信息部分
        self._render_basic_info()

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
