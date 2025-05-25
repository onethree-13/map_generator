import streamlit as st
import time
from utils.data_manager import DataManager


class CoordinateManagementTab:
    """坐标管理标签页"""
    
    def __init__(self, data_manager: DataManager, processor):
        self.data_manager = data_manager
        self.processor = processor
    
    def render(self):
        """渲染坐标管理标签页"""
        st.info("步骤4：获取地理坐标")

        if not self.data_manager.has_saved_json():
            st.warning("暂无数据，请先完成数据提取步骤。")
            return

        # 坐标获取状态
        self._render_coordinate_status()
        
        # 批量获取坐标操作
        self._render_batch_coordinate_operations()
    
    def _render_coordinate_status(self):
        """渲染坐标获取状态"""
        st.subheader("📍 坐标获取状态")

        coord_stats = self.data_manager.get_coordinates_status(use_editing=False)
        st.dataframe(coord_stats, use_container_width=True)
    
    def _render_batch_coordinate_operations(self):
        """渲染批量坐标操作"""
        col1, col2 = st.columns([1, 1])

        with col1:
            if st.button("🗺️ 获取所有地点坐标", type="primary", use_container_width=True):
                self._get_all_coordinates()

        with col2:
            if st.button("🔄 重置所有坐标", type="secondary", use_container_width=True):
                self._reset_all_coordinates()
    
    def _get_all_coordinates(self):
        """获取所有地点坐标"""
        if self.processor.geo_service:
            progress_bar = st.progress(0)
            status_text = st.empty()

            def progress_callback(message):
                status_text.text(message)

            try:
                self.processor.get_coordinates_with_progress(progress_callback)
                progress_bar.progress(100)
                status_text.text("✅ 坐标获取完成！")
                st.success("所有地点的坐标已获取完成！")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"获取坐标时出错: {e}")
        else:
            st.error("地理编码服务未初始化，请检查API配置。")
    
    def _reset_all_coordinates(self):
        """重置所有坐标"""
        saved_json = self.data_manager.get_saved_json()
        for item in saved_json.get("data", []):
            item["center"] = {"lat": 0, "lng": 0}
        self.data_manager.set_saved_json(saved_json)
        st.success("所有坐标已重置！")
        st.rerun() 