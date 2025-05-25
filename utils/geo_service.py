"""
地理编码服务模块
提供地址到经纬度的转换功能
"""

import requests
import time
import re
from typing import Dict, Any, Optional, List
import json

class GeocodingService:
    """地理编码服务类"""
    
    def __init__(self, api_key: str, default_prefix: str = ""):
        """
        初始化地理编码服务
        
        Args:
            api_key: 腾讯地图API密钥
            default_prefix: 默认地址前缀
        """
        self.api_key = api_key
        self.default_prefix = default_prefix
        self.base_url = "https://apis.map.qq.com/ws/geocoder/v1/"
        self.request_interval = 1  # 请求间隔（秒）
    
    def geocode_address(self, address: str, use_prefix: bool = True) -> Dict[str, Any]:
        """
        地址地理编码
        
        Args:
            address: 地址字符串
            use_prefix: 是否使用默认前缀
            
        Returns:
            包含经纬度信息的字典
        """
        # 地址预处理
        cleaned_address = self._clean_address(address)
        
        # 添加前缀
        if use_prefix and self.default_prefix:
            full_address = self.default_prefix + cleaned_address
        else:
            full_address = cleaned_address
        
        # 构建请求参数
        params = {
            "address": full_address,
            "key": self.api_key,
            "output": "json"
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == 0:
                location = data["result"]["location"]
                return {
                    "lat": location["lat"],
                    "lng": location["lng"],
                    "success": True,
                    "formatted_address": data["result"].get("formatted_addresses", {}).get("recommend", full_address),
                    "confidence": data["result"].get("reliability", 0),
                    "original_address": address,
                    "processed_address": full_address
                }
            else:
                return {
                    "lat": 0,
                    "lng": 0,
                    "success": False,
                    "error": data.get('message', '未知错误'),
                    "error_code": data.get('status', -1),
                    "original_address": address,
                    "processed_address": full_address
                }
                
        except requests.exceptions.Timeout:
            return {
                "lat": 0,
                "lng": 0,
                "success": False,
                "error": "请求超时",
                "original_address": address
            }
        except requests.exceptions.RequestException as e:
            return {
                "lat": 0,
                "lng": 0,
                "success": False,
                "error": f"网络请求错误: {str(e)}",
                "original_address": address
            }
        except json.JSONDecodeError:
            return {
                "lat": 0,
                "lng": 0,
                "success": False,
                "error": "API响应格式错误",
                "original_address": address
            }
        except Exception as e:
            return {
                "lat": 0,
                "lng": 0,
                "success": False,
                "error": f"未知错误: {str(e)}",
                "original_address": address
            }
    
    def batch_geocode(self, addresses: List[str], progress_callback=None) -> List[Dict[str, Any]]:
        """
        批量地理编码
        
        Args:
            addresses: 地址列表
            progress_callback: 进度回调函数
            
        Returns:
            结果列表
        """
        results = []
        total = len(addresses)
        
        for i, address in enumerate(addresses):
            if progress_callback:
                progress_callback(i, total, address)
            
            result = self.geocode_address(address)
            results.append(result)
            
            # 请求间隔，避免频率限制
            if i < total - 1:  # 最后一个请求不需要等待
                time.sleep(self.request_interval)
        
        return results
    
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
        
        # 提取到"号"为止的地址部分
        match = re.search(r'^.*?号', address)
        if match:
            return match.group(0)
        
        # 如果没有"号"，返回原地址
        return address.strip()
    
    def update_json_coordinates(self, json_data: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """
        更新JSON数据中的坐标信息
        
        Args:
            json_data: 包含地点信息的JSON数据
            progress_callback: 进度回调函数
            
        Returns:
            更新后的JSON数据
        """
        if not json_data or "data" not in json_data:
            return json_data
        
        data_items = json_data["data"]
        total = len(data_items)
        
        for i, item in enumerate(data_items):
            if "address" in item and item["address"]:
                if progress_callback:
                    progress_callback(i, total, item["address"])
                
                # 获取坐标
                result = self.geocode_address(item["address"])
                
                # 更新坐标信息
                if "center" not in item:
                    item["center"] = {}
                
                item["center"]["lat"] = result["lat"]
                item["center"]["lng"] = result["lng"]
                
                # 可选：添加地理编码元信息
                if result["success"]:
                    item["geo_info"] = {
                        "formatted_address": result.get("formatted_address"),
                        "confidence": result.get("confidence", 0),
                        "processed_address": result.get("processed_address")
                    }
                else:
                    item["geo_error"] = {
                        "error": result["error"],
                        "processed_address": result.get("processed_address")
                    }
                
                # 请求间隔
                if i < total - 1:
                    time.sleep(self.request_interval)
        
        return json_data
    
    def validate_coordinates(self, lat: float, lng: float) -> bool:
        """
        验证坐标是否有效
        
        Args:
            lat: 纬度
            lng: 经度
            
        Returns:
            是否有效
        """
        return (
            -90 <= lat <= 90 and
            -180 <= lng <= 180 and
            not (lat == 0 and lng == 0)
        )
    
    def get_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """
        计算两点间距离（公里）
        
        Args:
            lat1, lng1: 第一个点的坐标
            lat2, lng2: 第二个点的坐标
            
        Returns:
            距离（公里）
        """
        import math
        
        # 转换为弧度
        lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
        
        # Haversine公式
        dlat = lat2 - lat1
        dlng = lng2 - lng1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # 地球半径（公里）
        r = 6371
        
        return c * r

# 工厂函数
def create_geocoding_service(api_key: str, default_prefix: str = "") -> GeocodingService:
    """
    创建地理编码服务实例
    
    Args:
        api_key: API密钥
        default_prefix: 默认地址前缀
        
    Returns:
        地理编码服务实例
    """
    return GeocodingService(api_key, default_prefix)

# 兼容性函数，与原get_lat_long.py保持接口一致
def update_coordinates(json_data: Dict[str, Any], api_key: str, default_prefix: str = "上海市长宁区") -> Dict[str, Any]:
    """
    更新JSON数据中的经纬度信息（兼容性函数）
    
    Args:
        json_data: JSON数据
        api_key: API密钥
        default_prefix: 地址前缀
        
    Returns:
        更新后的JSON数据
    """
    service = GeocodingService(api_key, default_prefix)
    return service.update_json_coordinates(json_data) 