import streamlit as st
import json
import pandas as pd
from utils.data_manager import DataManager


class DataExportTab:
    """数据导出标签页"""
    
    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager
    
    def render(self):
        """渲染数据导出标签页"""
        st.info("步骤5: 数据导出")

        if not self.data_manager.has_saved_json():
            st.warning("暂无数据可导出，请先完成数据提取步骤。")
            return

        # 数据预览
        self._render_data_preview()
        
        # 导出选项
        self._render_export_options()
        
        # 完整数据预览
        self._render_complete_data_preview()
    
    def _render_data_preview(self):
        """渲染数据预览"""
        st.subheader("📊 最终数据预览")
        
        # 显示数据统计
        stats = self.data_manager.get_data_statistics(use_editing=False)
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        with col_stat1:
            st.metric("📍 总地点数", stats["total_locations"])
        with col_stat2:
            st.metric("🌐 有坐标", stats["has_coordinates"])
        with col_stat3:
            st.metric("📞 有电话", stats["has_phone"])
        with col_stat4:
            completion_rate = (stats['has_coordinates'] / stats['total_locations'] * 100) if stats['total_locations'] > 0 else 0
            st.metric("✅ 完整度", f"{completion_rate:.0f}%")
    
    def _render_export_options(self):
        """渲染导出选项"""
        col1, col2 = st.columns([2, 1])

        with col1:
            filename = st.text_input("文件名", value="map_data.json")

            # 导出设置
            export_settings = st.expander("🔧 导出设置")
            with export_settings:
                include_map_info = st.checkbox(
                    "包含地图信息", value=True, help="包含在地图信息页面设置的元数据")
                remove_empty = st.checkbox(
                    "移除空字段", value=True, help="移除值为空的字段")
                remove_zero_coords = st.checkbox(
                    "移除无效坐标", value=False, help="移除坐标为(0,0)的项目")
                include_meta = st.checkbox(
                    "包含元数据", value=False, help="包含地理编码的元数据信息")

        with col2:
            st.markdown("### 📥 导出数据")

            # 导出完整地图JSON
            if st.button("📄 导出完整地图JSON", type="primary", use_container_width=True):
                self._export_complete_map_json(filename, include_map_info, remove_empty, remove_zero_coords, include_meta)

            # 导出纯数据JSON
            if st.button("📊 导出纯数据JSON", type="secondary", use_container_width=True):
                self._export_data_only_json(filename, remove_empty, remove_zero_coords, include_meta)

            # 导出CSV
            if st.button("📊 导出CSV文件", type="secondary", use_container_width=True):
                self._export_csv(filename)
    
    def _export_complete_map_json(self, filename, include_map_info, remove_empty, remove_zero_coords, include_meta):
        """导出完整地图JSON"""
        final_data = self.data_manager.export_from_saved_json(remove_empty, remove_zero_coords)
        
        if not include_map_info:
            final_data = {"data": final_data["data"]}
        
        # 提供下载
        json_str = json.dumps(final_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="💾 下载完整地图JSON",
            data=json_str,
            file_name=filename,
            mime="application/json",
            use_container_width=True
        )

        data_count = len(final_data["data"])
        if include_map_info:
            st.success(f"✅ 完整地图数据已准备完成！包含地图信息和 {data_count} 个地点。")
        else:
            st.success(f"✅ 地点数据已准备完成！共包含 {data_count} 个地点。")
    
    def _export_data_only_json(self, filename, remove_empty, remove_zero_coords, include_meta):
        """导出纯数据JSON"""
        final_data = self.data_manager.export_data_only_from_saved(remove_empty, remove_zero_coords)
        
        json_str = json.dumps({"data": final_data}, ensure_ascii=False, indent=2)
        data_filename = filename.replace('.json', '_data.json')
        st.download_button(
            label="📊 下载纯数据JSON",
            data=json_str,
            file_name=data_filename,
            mime="application/json",
            use_container_width=True
        )
    
    def _export_csv(self, filename):
        """导出CSV文件"""
        # 转换为表格格式
        rows = []
        for item in self.data_manager.get_saved_json().get("data", []):
            row = {
                "名称": item.get("name", ""),
                "地址": item.get("address", ""),
                "电话": item.get("phone", ""),
                "网站/公众号": item.get("webName", ""),
                "简介": item.get("intro", ""),
                "标签": ", ".join(item.get("tags", [])),
                "纬度": item.get("center", {}).get("lat", 0),
                "经度": item.get("center", {}).get("lng", 0)
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        csv = df.to_csv(index=False, encoding='utf-8-sig')

        csv_filename = filename.replace('.json', '.csv')
        st.download_button(
            label="📊 下载CSV文件",
            data=csv,
            file_name=csv_filename,
            mime="text/csv",
            use_container_width=True
        )
    
    def _render_complete_data_preview(self):
        """渲染完整数据预览"""
        st.subheader("🔍 完整数据预览")

        # 显示完整的saved_json数据
        saved_json = self.data_manager.get_saved_json()
        
        # 显示地图信息（如果有）
        if saved_json.get("name") or saved_json.get("description") or saved_json.get("origin"):
            st.subheader("🗺️ 地图信息")
            map_info = {
                "name": saved_json.get("name", ""),
                "description": saved_json.get("description", ""),
                "origin": saved_json.get("origin", ""),
                "filter": saved_json.get("filter", {})
            }
            st.json(map_info)
            st.markdown("---")

        st.subheader("📍 地点数据")
        st.json(saved_json) 