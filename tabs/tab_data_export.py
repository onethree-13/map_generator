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
import json
import pandas as pd
from utils.data_manager import DataManager
from utils.map_utils import calculate_map_center_and_zoom, format_map_config_for_export


class DataExportTab:
    """数据导出标签页"""

    def __init__(self, data_manager: DataManager):
        self.data_manager = data_manager

    def render(self):
        """渲染数据导出标签页"""
        st.info("步骤6: 数据导出")

        if not self.data_manager.has_saved_json():
            st.warning("暂无数据可导出，请先完成数据提取步骤。")
            return

        # 导出选项
        self._render_export_options()
        
        st.markdown("---")

        # 地图预览
        self._render_map_preview()

    def _render_map_preview(self):
        """渲染地图预览"""
        st.subheader("🗺️ 地图预览")

        saved_json = self.data_manager.get_saved_json()
        data_items = saved_json.get("data", [])

        # 检查是否有有效坐标的地点
        valid_locations = [
            item for item in data_items
            if item.get("center", {}).get("lat", 0) != 0 and item.get("center", {}).get("lng", 0) != 0
        ]

        if not valid_locations:
            st.warning("⚠️ 暂无有效坐标数据，无法显示地图预览。请先完成坐标获取步骤。")
            return

        # 计算地图中心和缩放
        map_config = calculate_map_center_and_zoom(saved_json)
        center = map_config["center"]

        # 准备地图数据
        map_data = []
        for item in valid_locations:
            center_coords = item.get("center", {})
            map_data.append({
                "lat": center_coords.get("lat"),
                "lon": center_coords.get("lng"),  # streamlit使用lon而不是lng
                "name": item.get("name", "未知地点"),
                "address": item.get("address", ""),
                "size": 20  # 点的大小
            })

        # 显示地图统计信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📍 地图中心", f"{center['lat']:.4f}, {center['lng']:.4f}")
        with col2:
            st.metric("🎯 有效地点", len(valid_locations))
        with col3:
            zoom_level = map_config["zoom"][0]
            st.metric("🔍 建议缩放", f"级别 {zoom_level}")

        # 显示地图
        try:
            # 创建DataFrame
            df = pd.DataFrame(map_data)

            # 使用streamlit的地图组件
            st.map(
                df,
                latitude="lat",
                longitude="lon",
                size="size",
                zoom=map_config["zoom"][0] - 2,  # streamlit地图的缩放级别需要调整
                use_container_width=True
            )

            # 显示地图说明
            st.info(f"🗺️ 地图显示了 {len(valid_locations)} 个有效地点。红点表示各个地点的位置。")

        except Exception as e:
            st.error(f"地图渲染出错: {str(e)}")

            # 备用：显示坐标列表
            st.subheader("📍 坐标列表")
            coords_df = pd.DataFrame([
                {
                    "地点名称": item.get("name", ""),
                    "纬度": item.get("center", {}).get("lat", 0),
                    "经度": item.get("center", {}).get("lng", 0),
                    "地址": item.get("address", "")
                }
                for item in valid_locations
            ])
            st.dataframe(coords_df, use_container_width=True)

    def _render_export_options(self):
        """渲染导出选项"""
        st.markdown("### 📥 导出数据")

        col1, col2 = st.columns([1, 1])

        with col1:
            filename = st.text_input("文件名", value="map_data.json")

        with col2:
            st.markdown("&nbsp;")  # 空行对齐

        # 直接提供下载按钮
        self._render_download_buttons(filename)

    def _render_download_buttons(self, filename):
        """渲染下载按钮"""
        col1, col2 = st.columns(2)

        with col1:
            # 准备完整地图JSON数据
            final_data = self.data_manager.export_from_saved_json(True, True)
            map_config = calculate_map_center_and_zoom(final_data)
            final_data["center"] = map_config["center"]
            final_data["zoom"] = map_config["zoom"]

            json_str = json.dumps(final_data, ensure_ascii=False, indent=2)
            st.download_button(
                label="📄 下载完整地图JSON",
                data=json_str,
                file_name=filename,
                mime="application/json",
                use_container_width=True,
                type="primary"
            )

        with col2:
            # 准备CSV数据
            rows = []
            for item in self.data_manager.get_saved_json().get("data", []):
                row = {
                    "名称": item.get("name", ""),
                    "地址": item.get("address", ""),
                    "电话": item.get("phone", ""),
                    "网站/视频/公众号": item.get("webName", ""),
                    "网站链接": item.get("webLink", ""),
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
