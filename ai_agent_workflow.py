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
    DataExportTab,
    JSONEditorTab,
    TabManager
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

    # 初始化 Tab 管理器
    if 'tab_manager' not in st.session_state:
        st.session_state.tab_manager = TabManager(data_manager)
    
    tab_manager = st.session_state.tab_manager

    # 侧边栏配置
    with st.sidebar:
        st.header("⚙️ 配置选项")

        # API配置
        st.subheader("API配置")

        # 从配置获取默认值
        default_openai_key = get_config("OPENAI_API_KEY", "")
        default_amap_key = get_config("AMAP_API_KEY", "")
        default_tencent_key = get_config("TENCENT_API_KEY", "")

        qwen_api_key = st.text_input(
            "通义千问API密钥", value=default_openai_key, type="password", help="用于图像识别和文本处理")

        # 地图服务选择
        st.subheader("地图服务配置")
        
        # 获取可用的地图服务
        available_services = get_config("MAP_SERVICES", {})
        service_options = {key: config["name"] for key, config in available_services.items()}
        
        # 地图服务选择
        selected_service = st.selectbox(
            "选择地图服务",
            options=list(service_options.keys()),
            format_func=lambda x: service_options[x],
            index=0 if get_config("DEFAULT_MAP_SERVICE", "amap") == "amap" else 1,
            help="选择用于地理编码的地图服务"
        )

        # 根据选择的服务显示对应的API密钥输入框
        if selected_service == "amap":
            map_api_key = st.text_input(
                "高德地图API密钥", 
                value=default_amap_key, 
                type="password", 
                help="用于获取经纬度坐标（高德地图Web服务API）"
            )
        elif selected_service == "tencent":
            map_api_key = st.text_input(
                "腾讯地图API密钥", 
                value=default_tencent_key, 
                type="password", 
                help="用于获取经纬度坐标（腾讯位置服务API）"
            )

        # 配置状态检查
        missing_keys = []
        if not default_openai_key:
            missing_keys.append("通义千问API密钥")
        if selected_service == "amap" and not default_amap_key:
            missing_keys.append("高德地图API密钥")
        elif selected_service == "tencent" and not default_tencent_key:
            missing_keys.append("腾讯地图API密钥")

        if missing_keys:
            st.warning(f"⚠️ 检测到以下API密钥未配置：{', '.join(missing_keys)}")
            st.markdown("""
            **请配置API密钥：**
            1. 复制 `env.example` 为 `.env`
            2. 填入真实的API密钥
            3. 重启应用程序
            
            或在上方输入框中直接填入密钥。
            """)

        # 更新配置按钮
        if st.button("更新配置", type="primary"):
            # 初始化地理编码服务
            if map_api_key:
                st.session_state.processor.initialize_geo_service(
                    map_api_key, 
                    selected_service
                )
                st.success(f"✅ {service_options[selected_service]}服务已初始化！")
            
            # 初始化OpenAI客户端
            if qwen_api_key:
                st.session_state.processor.initialize_openai_client(qwen_api_key)
                st.success("✅ 通义千问服务已初始化！")

        # 显示当前地图服务状态
        if st.session_state.processor.geo_service:
            service_info = st.session_state.processor.get_current_map_service_info()
            st.success(f"🗺️ 当前使用：{service_info['service_name']}")
        else:
            st.info("🔧 请配置并更新地图服务")

        # 自动初始化服务（如果有默认密钥）
        if st.session_state.processor.geo_service is None and map_api_key:
            st.session_state.processor.initialize_geo_service(
                map_api_key, 
                selected_service
            )

        if st.session_state.processor.openai_client is None and qwen_api_key:
            st.session_state.processor.initialize_openai_client(qwen_api_key)

        # 重置功能
        sidebar_components.render_reset_operations()
        
        # 检查是否需要重置处理器
        if sidebar_components.check_processor_reset_needed():
            st.session_state.processor.json_data = None
            st.session_state.processor.extracted_text = ""

        # 数据状态展示
        sidebar_components.render_data_status()
        
        # Tab 状态信息
        tab_manager.show_tab_status()
        
        # 快速操作
        tab_manager.show_quick_actions()

    # 主界面布局 - 创建标签页
    tab_names = ["📁 数据提取", "🗺️ 地图信息", "📝 数据编辑", "🏷️ 标签管理", "📍 坐标管理", "📊 数据导出", "📝 JSON编辑器"]
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(tab_names)
    
    # 检测当前活跃的 Tab（通过 URL 参数或其他方式）
    # 注意：Streamlit 的 tabs 不直接支持切换检测，这里我们使用一个变通方法
    current_tab_index = 0  # 默认第一个 Tab
    
    # 根据 session state 确定当前 Tab
    current_tab_name = tab_manager.get_current_tab()
    tab_name_mapping = {
        "数据提取": 0,
        "地图信息": 1, 
        "数据编辑": 2,
        "标签管理": 3,
        "坐标管理": 4,
        "数据导出": 5,
        "JSON编辑器": 6
    }
    
    # 创建标签页实例
    data_extraction_tab = DataExtractionTab(data_manager, st.session_state.processor)
    map_info_tab = MapInfoTab(data_manager)
    data_editing_tab = DataEditingTab(data_manager, st.session_state.processor)
    tag_management_tab = TagManagementTab(data_manager, st.session_state.processor)
    coordinate_management_tab = CoordinateManagementTab(data_manager, st.session_state.processor)
    data_export_tab = DataExportTab(data_manager)
    json_editor_tab = JSONEditorTab(data_manager)

    # 简化的 Tab 渲染逻辑
    # 只渲染内容，不进行自动切换检测
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

    with tab7:
        json_editor_tab.render()

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