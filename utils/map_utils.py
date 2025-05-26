"""
地图工具模块
提供地图中心位置和缩放级别计算功能
"""

import math
from typing import List, Dict, Any, Tuple, Optional


class MapUtils:
    """地图工具类"""
    
    # 缩放级别对应的距离（米）
    ZOOM_DISTANCE_MAP = {
        3: 1000000,
        4: 500000,
        5: 200000,
        6: 100000,
        7: 50000,
        8: 25000,
        9: 20000,
        10: 10000,
        11: 5000,
        12: 2000,
        13: 1000,
        14: 500,
        15: 200,
        16: 100,
        17: 50,
        18: 20,
        19: 10,
        20: 5,
    }
    
    @staticmethod
    def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        计算两点间的距离（米）
        使用 Haversine 公式
        
        Args:
            lat1, lng1: 第一个点的纬度和经度
            lat2, lng2: 第二个点的纬度和经度
            
        Returns:
            距离（米）
        """
        # 地球半径（米）
        R = 6371000
        
        # 转换为弧度
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        # Haversine 公式
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    @staticmethod
    def calculate_center(points: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
        """
        计算所有点的中心位置
        
        Args:
            points: 包含坐标信息的点列表
            
        Returns:
            中心位置 {"lat": float, "lng": float}，如果没有有效点则返回None
        """
        valid_points = []
        
        for point in points:
            center = point.get("center", {})
            lat = center.get("lat", 0)
            lng = center.get("lng", 0)
            
            # 过滤掉无效坐标
            if lat != 0 and lng != 0 and -90 <= lat <= 90 and -180 <= lng <= 180:
                valid_points.append({"lat": lat, "lng": lng})
        
        if not valid_points:
            return None
        
        # 计算平均值
        total_lat = sum(point["lat"] for point in valid_points)
        total_lng = sum(point["lng"] for point in valid_points)
        count = len(valid_points)
        
        return {
            "lat": total_lat / count,
            "lng": total_lng / count
        }
    
    @staticmethod
    def calculate_bounds(points: List[Dict[str, Any]]) -> Optional[Dict[str, float]]:
        """
        计算所有点的边界
        
        Args:
            points: 包含坐标信息的点列表
            
        Returns:
            边界信息 {"min_lat": float, "max_lat": float, "min_lng": float, "max_lng": float}
        """
        valid_points = []
        
        for point in points:
            center = point.get("center", {})
            lat = center.get("lat", 0)
            lng = center.get("lng", 0)
            
            # 过滤掉无效坐标
            if lat != 0 and lng != 0 and -90 <= lat <= 90 and -180 <= lng <= 180:
                valid_points.append({"lat": lat, "lng": lng})
        
        if not valid_points:
            return None
        
        lats = [point["lat"] for point in valid_points]
        lngs = [point["lng"] for point in valid_points]
        
        return {
            "min_lat": min(lats),
            "max_lat": max(lats),
            "min_lng": min(lngs),
            "max_lng": max(lngs)
        }
    
    @staticmethod
    def calculate_zoom_level(points: List[Dict[str, Any]], padding_factor: float = 1.5) -> int:
        """
        根据点的分布计算合适的缩放级别
        
        Args:
            points: 包含坐标信息的点列表
            padding_factor: 边距因子，用于在边界外留出空间
            
        Returns:
            缩放级别（3-20）
        """
        bounds = MapUtils.calculate_bounds(points)
        if not bounds:
            return 15  # 默认缩放级别
        
        # 如果只有一个点，返回较高的缩放级别
        valid_points = [p for p in points if p.get("center", {}).get("lat", 0) != 0]
        if len(valid_points) <= 1:
            return 16
        
        # 计算边界的对角线距离
        diagonal_distance = MapUtils.calculate_distance(
            bounds["min_lat"], bounds["min_lng"],
            bounds["max_lat"], bounds["max_lng"]
        )
        
        # 应用边距因子
        required_distance = diagonal_distance * padding_factor
        
        # 根据距离选择合适的缩放级别
        # 从小缩放级别开始，找到第一个能容纳所有点的级别
        for zoom_level in sorted(MapUtils.ZOOM_DISTANCE_MAP.keys()):
            if required_distance <= MapUtils.ZOOM_DISTANCE_MAP[zoom_level]:
                return max(10, zoom_level)  # 最小不低于10级
        
        return 15  # 默认返回15级
    
    @staticmethod
    def calculate_map_config(points: List[Dict[str, Any]], 
                           initial_zoom_offset: int = 0,
                           min_zoom_offset: int = -1,
                           max_zoom_offset: int = 5) -> Dict[str, Any]:
        """
        计算完整的地图配置
        
        Args:
            points: 包含坐标信息的点列表
            initial_zoom_offset: 初始缩放级别偏移
            min_zoom_offset: 最小缩放级别偏移
            max_zoom_offset: 最大缩放级别偏移
            
        Returns:
            地图配置字典，包含center和zoom
        """
        center = MapUtils.calculate_center(points)
        if not center:
            # 默认中心位置（上海市中心）
            center = {"lat": 31.230416, "lng": 121.473701}
        
        base_zoom = MapUtils.calculate_zoom_level(points)
        
        # 计算三个缩放级别
        initial_zoom = max(3, min(20, base_zoom + initial_zoom_offset))
        min_zoom = max(3, min(20, base_zoom + min_zoom_offset))
        max_zoom = max(3, min(20, base_zoom + max_zoom_offset))
        
        # 确保逻辑关系正确
        min_zoom = min(min_zoom, initial_zoom)
        max_zoom = max(max_zoom, initial_zoom)
        
        return {
            "center": center,
            "zoom": [initial_zoom, min_zoom, max_zoom]
        }


# 便捷函数
def calculate_map_center_and_zoom(json_data: Dict[str, Any], 
                                initial_zoom_offset: int = 0,
                                min_zoom_offset: int = -1,
                                max_zoom_offset: int = 5) -> Dict[str, Any]:
    """
    根据JSON数据中的points计算地图中心和缩放配置
    
    Args:
        json_data: 包含data字段的JSON数据
        initial_zoom_offset: 初始缩放级别偏移
        min_zoom_offset: 最小缩放级别偏移  
        max_zoom_offset: 最大缩放级别偏移
        
    Returns:
        包含center和zoom的配置字典
    """
    points = json_data.get("data", [])
    return MapUtils.calculate_map_config(
        points, 
        initial_zoom_offset, 
        min_zoom_offset, 
        max_zoom_offset
    )


def get_zoom_distance_info() -> Dict[int, int]:
    """
    获取缩放级别对应的距离信息
    
    Returns:
        缩放级别到距离的映射字典
    """
    return MapUtils.ZOOM_DISTANCE_MAP.copy()


def format_map_config_for_export(json_data: Dict[str, Any],
                                name: str = "地图",
                                origin: str = "地图生成器",
                                filter_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    格式化地图配置用于导出
    
    Args:
        json_data: 包含data字段的JSON数据
        name: 地图名称
        origin: 数据来源
        filter_config: 过滤器配置
        
    Returns:
        完整的地图配置字典
    """
    map_config = calculate_map_center_and_zoom(json_data)
    
    result = {
        "name": name,
        "center": map_config["center"],
        "zoom": map_config["zoom"],
        "origin": origin
    }
    
    if filter_config:
        result["filter"] = filter_config
    else:
        result["filter"] = {
            "inclusive": {},
            "exclusive": {}
        }
    
    return result 