import streamlit as st
from .data_manager import DataManager


class SidebarResetOperations:
    """侧边栏重置操作组件"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def render(self):
        """渲染重置操作区域"""
        st.subheader("🔄 重置操作")
        col_reset1, col_reset2 = st.columns(2)

        with col_reset1:
            if st.button("🗑️ 清除数据", type="secondary", use_container_width=True):
                self.data_manager.reset_saved_json()
                st.success("✅ 地图信息已清除")
                st.rerun()

        with col_reset2:
            if st.button("🔄 完全重置", type="secondary", use_container_width=True):
                self.data_manager.reset_all_data()
                # 注意：这里需要外部处理器重置，我们返回一个标志
                st.session_state._need_processor_reset = True
                st.success("✅ 所有数据已重置")
                st.rerun()


class SidebarDataStatus:
    """侧边栏数据状态显示组件"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def render(self):
        """渲染数据状态区域"""
        st.subheader("📊 数据状态")

        # 计算数据统计
        stats = self.data_manager.get_data_statistics(use_editing=False)

        if stats["total_locations"] > 0:
            # 显示总体统计
            st.metric("📍 总地点数", stats["total_locations"])

            # 创建两列显示详细统计
            col_stat1, col_stat2 = st.columns(2)

            with col_stat1:
                st.metric("🏷️ 有名称", f"{stats['has_name']}")
                st.metric("📍 有地址", f"{stats['has_address']}")
                st.metric("🌐 有坐标", f"{stats['has_coordinates']}")

            with col_stat2:
                st.metric("📞 有电话", f"{stats['has_phone']}")
                st.metric("📝 有简介", f"{stats['has_intro']}")
                st.metric("🏷️ 有标签", f"{stats['has_tags']}")
                # 计算完整度百分比
                completion_rate = (
                    stats['has_coordinates'] / stats['total_locations'] * 100) if stats['total_locations'] > 0 else 0
                st.metric("✅ 坐标完整度", f"{completion_rate:.0f}%")

            # 显示导入状态
            self._render_import_status()
        else:
            self._render_no_data_status()
    
    def _render_import_status(self):
        """渲染导入状态"""
        if self.data_manager.has_extracted_text() and "已导入" in self.data_manager.get_extracted_text():
            st.success("✅ 数据已导入")
        elif self.data_manager.has_saved_json():
            st.info("✅ 数据已生成")
        else:
            st.info("⏳ 等待数据导入")
    
    def _render_no_data_status(self):
        """渲染无数据状态"""
        st.info("📭 暂无数据")
        if self.data_manager.has_extracted_text() and not self.data_manager.has_saved_json():
            st.warning("⏳ 已提取文字，等待生成结构化数据")
        else:
            st.info("💡 请在主页面导入或提取数据")


class SidebarComponents:
    """侧边栏组件管理器"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
        self.reset_operations = SidebarResetOperations(data_manager)
        self.data_status = SidebarDataStatus(data_manager)
    
    def render_reset_operations(self):
        """渲染重置操作组件"""
        self.reset_operations.render()
    
    def render_data_status(self):
        """渲染数据状态组件"""
        self.data_status.render()
    
    def check_processor_reset_needed(self) -> bool:
        """检查是否需要重置处理器"""
        if hasattr(st.session_state, '_need_processor_reset') and st.session_state._need_processor_reset:
            st.session_state._need_processor_reset = False
            return True
        return False 