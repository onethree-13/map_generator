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

import re
import streamlit as st
import time
import pandas as pd
import numpy as np
from utils.data_manager import DataManager, clean_text
import urllib.parse


class CoordinateManagementTab:
    """坐标管理标签页"""
    
    def __init__(self, data_manager: DataManager, processor):
        self.data_manager = data_manager
        self.processor = processor
        self.request_interval = 0.5  # 请求间隔（秒）
    
    def render(self):
        """渲染坐标管理标签页"""
        st.info("步骤5：获取地理坐标")

        if not self.data_manager.has_saved_json():
            st.warning("暂无数据，请先完成数据提取步骤。")
            return
        
        # 批量操作按钮
        self._render_batch_operations()
        
        # 可编辑坐标表格
        self._render_editable_table()
    
    def _render_batch_operations(self):
        """渲染批量操作按钮"""
        st.markdown("### 🔧 批量操作")
        
        # 配置选项
        st.markdown("#### ⚙️ 地址处理配置")
        col1, col2 = st.columns(2)
        
        with col1:
            default_prefix = st.text_input(
                "默认地址前缀",
                value="",
                placeholder="例如：上海市长宁区",
                help="为所有地址添加统一前缀，提高地理编码准确性"
            )
        
        with col2:
            use_clean_address = st.checkbox(
                "使用干净地址功能",
                value=True,
                help="启用后会对地址进行清理和截取处理，提取关键地址信息"
            )
        
        # 批量操作按钮
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗺️ 重新获取所有坐标", type="primary", use_container_width=True):
                self._get_all_coordinates(default_prefix, use_clean_address)
        
        with col2:
            if st.button("📍 获取缺失坐标", type="secondary", use_container_width=True):
                self._get_missing_coordinates(default_prefix, use_clean_address)
    
    def _render_editable_table(self):
        """渲染可编辑坐标表格"""
        st.markdown("---")
        st.markdown("### 📋 坐标管理表格")
        
        saved_json = self.data_manager.get_saved_json()
        data_items = saved_json.get("data", [])
        
        if not data_items:
            st.info("📭 暂无地点数据")
            return
        
        # 准备表格数据
        table_data = []
        for i, item in enumerate(data_items):
            name = item.get("name", f"地点 {i+1}")
            address = item.get("address", "")
            center = item.get("center", {})
            lat = center.get("lat", 0)
            lng = center.get("lng", 0)
            
            # 编码地名用于URL
            encoded_name = urllib.parse.quote(name)
            encoded_address = urllib.parse.quote(address)
            
            # 经纬度显示（可编辑）
            coord_text = f"{lng},{lat}" if (lat != 0 and lng != 0) else "0,0"
            
            # 确认位置链接
            confirm_link = f"https://apis.map.qq.com/uri/v1/marker?marker=coord:{lat},{lng};title:{encoded_name}"
            
            # 手动选点链接
            manual_link = f"https://guihuayun.com/maps/getxy.php?area={encoded_address}"
            
            table_data.append({
                "编号": i + 1,
                "地点名": name,
                "经纬度": coord_text,
                "确认位置": confirm_link if (lat != 0 and lng != 0) else "暂无坐标",
                "手动选点": manual_link
            })
        
        # 显示表格
        df = pd.DataFrame(table_data)
        
        # 使用data_editor创建可编辑表格
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "编号": st.column_config.NumberColumn("编号", width="small", disabled=True),
                "地点名": st.column_config.TextColumn("地点名", width="medium", disabled=True),
                "经纬度": st.column_config.TextColumn(
                    "经纬度", 
                    width="medium",
                    help="格式：经度,纬度 (例如：116.397470,39.908823)"
                ),
                "确认位置": st.column_config.LinkColumn("确认位置", width="small"),
                "手动选点": st.column_config.LinkColumn("手动选点", width="small")
            },
            key="coordinate_table",
            disabled=["编号", "地点名", "确认位置", "手动选点"]
        )
        
        # 保存按钮
        if st.button("💾 保存坐标修改", type="primary"):
            self._save_coordinate_changes(edited_df, data_items)
        
        # 显示操作提示
        st.info("💡 提示：可以直接编辑经纬度列，格式为 经度,纬度（如：116.397470,39.908823）")
    
    def _save_coordinate_changes(self, edited_df, original_data):
        """保存坐标修改"""
        try:
            saved_json = self.data_manager.get_saved_json()
            
            for i, row in edited_df.iterrows():
                coord_text = row["经纬度"]
                
                # 解析坐标
                if coord_text and coord_text != "0,0":
                    try:
                        parts = coord_text.split(",")
                        if len(parts) == 2:
                            lng = float(parts[0].strip())
                            lat = float(parts[1].strip())
                            
                            # 验证坐标范围
                            if -90 <= lat <= 90 and -180 <= lng <= 180:
                                saved_json["data"][i]["center"] = {"lat": lat, "lng": lng}
                            else:
                                st.error(f"第 {i+1} 行坐标超出有效范围")
                                return
                        else:
                            st.error(f"第 {i+1} 行坐标格式错误")
                            return
                    except ValueError:
                        st.error(f"第 {i+1} 行坐标格式错误，请使用数字")
                        return
                else:
                    # 清空坐标
                    saved_json["data"][i]["center"] = {"lat": 0, "lng": 0}
            
            # 保存数据
            self.data_manager.set_saved_json(saved_json)
            st.success("✅ 坐标修改已保存！")
            st.rerun()
            
        except Exception as e:
            st.error(f"保存坐标时出错: {e}")
            
    def _clean_address(self, address: str) -> str:
        """
        清理地址字符串
        
        Args:
            address: 原始地址
            
        Returns:
            清理后的地址
        """
        if not address:
            return ""
        
        # 使用data_manager的clean_text函数
        cleaned = clean_text(address)
        
        if not cleaned:
            return ""
        
        # 地址特殊处理逻辑
        # 1. 提取到"号楼"为止的地址部分
        match = re.search(r'^.*?号楼', cleaned)
        if match:
            return match.group(0)
        
        # 2. 提取到"号"为止的地址部分
        match = re.search(r'^.*?号', cleaned)
        if match:
            return match.group(0)
        
        # 3. 如果没有"号"，尝试提取到"路"、"街"、"巷"等
        for suffix in ['路', '街', '巷', '道', '大道', '大街']:
            match = re.search(f'^.*?{suffix}', cleaned)
            if match:
                return match.group(0)
        
        # 3. 如果都没有，返回清理后的原地址
        return cleaned
    
    def _process_address(self, address: str, default_prefix: str = "", use_clean_address: bool = True) -> str:
        """
        处理地址字符串
        
        Args:
            address: 原始地址
            default_prefix: 默认前缀
            use_clean_address: 是否使用地址清理功能
            
        Returns:
            处理后的地址
        """
        if not address:
            return ""
        
        # 根据选项决定是否使用地址清理
        if use_clean_address:
            processed_address = self._clean_address(address)
        else:
            processed_address = clean_text(address)
        
        # 添加默认前缀
        if default_prefix and processed_address:
            return default_prefix + processed_address
        
        return processed_address
    
    def _get_all_coordinates(self, default_prefix: str = "", use_clean_address: bool = True):
        """获取所有地点坐标"""
        if not self.processor.geo_service:
            st.error("地理编码服务未初始化，请检查API配置。")
            return
        
        saved_json = self.data_manager.get_saved_json()
        data_items = saved_json.get("data", [])
        
        if not data_items:
            st.warning("暂无地点数据")
            return
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        success_count = 0
        total = len(data_items)
        
        try:
            for i, item in enumerate(data_items):
                name = item.get("name", "")
                address = item.get("address", "")
                
                # 处理地址
                processed_address = self._process_address(address, default_prefix, use_clean_address)
                processed_name = self._process_address(name, default_prefix, False)
                print(processed_address)
                
                status_text.text(f"正在获取坐标: {name} ({i+1}/{total})")
                
                # 获取坐标
                coords = self.processor.geo_service.get_coordinates(processed_name, processed_address)
                
                if coords:
                    item["center"] = coords
                    success_count += 1
                else:
                    # 确保有center字段
                    if "center" not in item:
                        item["center"] = {"lat": 0, "lng": 0}
                
                # 更新进度条
                progress_bar.progress((i + 1) / total)
                
                # 请求间隔，避免频率限制
                if i < total - 1:
                    time.sleep(self.request_interval)
            
            # 保存更新后的数据
            self.data_manager.set_saved_json(saved_json)
            
            progress_bar.progress(100)
            status_text.text("✅ 坐标获取完成！")
            st.success(f"成功获取 {success_count}/{total} 个地点的坐标！")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"获取坐标时出错: {e}")
    
    def _get_missing_coordinates(self, default_prefix: str = "", use_clean_address: bool = True):
        """仅获取缺失坐标的地点"""
        if not self.processor.geo_service:
            st.error("地理编码服务未初始化，请检查API配置。")
            return
        
        saved_json = self.data_manager.get_saved_json()
        data_items = saved_json.get("data", [])
        
        # 找出缺失坐标的地点
        missing_items = []
        for i, item in enumerate(data_items):
            center = item.get("center", {})
            if center.get("lat", 0) == 0 or center.get("lng", 0) == 0:
                missing_items.append((i, item))
        
        if not missing_items:
            st.success("所有地点都已有坐标！")
            return
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        success_count = 0
        total = len(missing_items)
        
        try:
            for idx, (original_index, item) in enumerate(missing_items):
                name = item.get("name", "")
                address = item.get("address", "")
                
                # 处理地址
                processed_address = self._process_address(address, default_prefix, use_clean_address)
                processed_name = self._process_address(name, default_prefix, False)
                
                status_text.text(f"正在获取缺失坐标: {name} ({idx+1}/{total})")
                
                # 获取坐标
                coords = self.processor.geo_service.get_coordinates(processed_name, processed_address)
                
                if coords:
                    data_items[original_index]["center"] = coords
                    success_count += 1
                
                # 更新进度条
                progress_bar.progress((idx + 1) / total)
                
                # 请求间隔，避免频率限制
                if idx < total - 1:
                    time.sleep(self.request_interval)
            
            # 保存更新后的数据
            self.data_manager.set_saved_json(saved_json)
            
            progress_bar.progress(100)
            status_text.text("✅ 缺失坐标获取完成！")
            st.success(f"成功获取 {success_count}/{total} 个地点的缺失坐标！")
            time.sleep(1)
            st.rerun()
            
        except Exception as e:
            st.error(f"获取缺失坐标时出错: {e}")
    
    def _get_coordinates_statistics(self) -> dict:
        """获取坐标统计信息"""
        saved_json = self.data_manager.get_saved_json()
        data_items = saved_json.get("data", [])
        
        total = len(data_items)
        has_coords = 0
        has_address = 0
        has_name_only = 0
        
        for item in data_items:
            center = item.get("center", {})
            if center.get("lat", 0) != 0 and center.get("lng", 0) != 0:
                has_coords += 1
            
            if item.get("address", "").strip():
                has_address += 1
            elif item.get("name", "").strip():
                has_name_only += 1
        
        return {
            "total": total,
            "has_coordinates": has_coords,
            "missing_coordinates": total - has_coords,
            "has_address": has_address,
            "has_name_only": has_name_only,
            "no_location_info": total - has_address - has_name_only
        }