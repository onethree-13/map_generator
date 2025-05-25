import streamlit as st
import pandas as pd
from collections import Counter

# 导入配置
from config import get_config

# 导入数据管理器
from utils.data_manager import DataManager

# 导入侧边栏组件
from utils.sidebar_components import SidebarComponents

# 导入地图数据处理器
from utils.map_data_processor import MapDataProcessor

# 导入所有标签页
from tabs import (
    DataExtractionTab,
    MapInfoTab, 
    DataEditingTab,
    TagManagementTab,
    CoordinateManagementTab,
    DataExportTab
)


def main():
    st.set_page_config(
        page_title="地图数据智能生成器",
        page_icon="🗺️",
        layout="wide"
    )

    st.title("🗺️ AI地图数据提取工具")
    st.markdown("智能地图数据提取与整理工具")

    # 初始化数据管理器
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = DataManager()
    
    data_manager = st.session_state.data_manager

    # 初始化侧边栏组件
    if 'sidebar_components' not in st.session_state:
        st.session_state.sidebar_components = SidebarComponents(data_manager)
    
    sidebar_components = st.session_state.sidebar_components

    # 初始化处理器
    if 'processor' not in st.session_state:
        st.session_state.processor = MapDataProcessor()

    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置选项")

        # API配置
        st.subheader("API配置")

        # 从配置获取默认值
        default_openai_key = get_config("OPENAI_API_KEY", "")
        default_tencent_key = get_config("TENCENT_API_KEY", "")

        qwen_api_key = st.text_input(
            "通义千问API密钥", value=default_openai_key, type="password", help="用于图像识别和文本处理")
        api_key = st.text_input(
            "腾讯地图API密钥", value=default_tencent_key, type="password", help="用于获取经纬度坐标")

        # 配置状态检查
        if not default_openai_key or not default_tencent_key:
            st.warning("⚠️ 检测到API密钥未配置！")
            st.markdown("""
            **请配置API密钥：**
            1. 复制 `env.example` 为 `.env`
            2. 填入真实的API密钥
            3. 重启应用程序
            
            或在上方输入框中直接填入密钥。
            """)

        # 更新配置
        if st.button("更新配置"):
            st.session_state.processor.initialize_geo_service(api_key)
            st.session_state.processor.initialize_openai_client(qwen_api_key)
            st.success("配置已更新！")

        # 初始化服务
        if st.session_state.processor.geo_service is None:
            st.session_state.processor.initialize_geo_service(api_key)

        if st.session_state.processor.openai_client is None:
            st.session_state.processor.initialize_openai_client(qwen_api_key)

        # 重置功能
        sidebar_components.render_reset_operations()
        
        # 检查是否需要重置处理器
        if sidebar_components.check_processor_reset_needed():
            st.session_state.processor.json_data = None
            st.session_state.processor.extracted_text = ""

        # 数据状态展示
        sidebar_components.render_data_status()

    # 主界面布局 - 创建标签页
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["📁 数据提取", "🗺️ 地图信息", "📝 数据编辑", "🏷️ 标签管理", "📍 坐标管理", "📊 数据导出"])

    # 创建标签页实例
    data_extraction_tab = DataExtractionTab(data_manager, st.session_state.processor)
    map_info_tab = MapInfoTab(data_manager)
    data_editing_tab = DataEditingTab(data_manager, st.session_state.processor)
    tag_management_tab = TagManagementTab(data_manager, st.session_state.processor)
    coordinate_management_tab = CoordinateManagementTab(data_manager, st.session_state.processor)
    data_export_tab = DataExportTab(data_manager)

    # 渲染各个标签页
    with tab1:
        data_extraction_tab.render()

    with tab2:
        map_info_tab.render()

    with tab3:
        data_editing_tab.render()

    with tab4:
        tag_management_tab.render()

    with tab5:
        coordinate_management_tab.render()

    with tab6:
        data_export_tab.render()

    # 页脚
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #888; padding: 20px;'>"
        "🗺️ AI地图数据提取工具 | 由 AI 驱动的智能数据处理"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main() 