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

"""
地理编码服务模块
提供单点地址到经纬度的转换功能
支持高德地图和腾讯地图API
"""

import requests
import time
import re
from typing import Dict, Any, Optional
import json
from utils.data_manager import clean_text


class GeocodingService:
    """地理编码服务类 - 支持多种地图服务"""
    
    def __init__(self, api_key: str, service_type: str = "amap"):
        """
        初始化地理编码服务
        
        Args:
            api_key: 地图API密钥
            service_type: 服务类型 ("amap" 或 "tencent")
        """
        self.api_key = api_key
        self.service_type = service_type
        self.max_retries = 3  # 最大重试次数
        
        # 根据服务类型设置API配置
        if service_type == "amap":
            self.base_url = "https://restapi.amap.com/v3/geocode/geo"
            self.service_name = "高德地图"
        elif service_type == "tencent":
            self.base_url = "https://apis.map.qq.com/ws/geocoder/v1/"
            self.service_name = "腾讯地图"
        else:
            raise ValueError(f"不支持的地图服务类型: {service_type}")
    
    def get_coordinates(self, name: str, address: str) -> Optional[Dict[str, float]]:
        """
        获取地点坐标（主要接口）
        
        Args:
            name: 地点名称
            address: 地址字符串
            
        Returns:
            包含lat和lng的字典，失败时返回None
        """
        # 优先使用地址，如果地址为空则使用名称
        search_text = address.strip() if address.strip() else name.strip()
        
        if not search_text:
            return None
        
        result = self._geocode_address(search_text)
        
        if result["success"] and result["lat"] != 0 and result["lng"] != 0:
            return {
                "lat": result["lat"],
                "lng": result["lng"]
            }
        
        # 如果地址失败且地址不等于名称，尝试使用名称
        if address.strip() and name.strip() and address.strip() != name.strip():
            result = self._geocode_address(name.strip())
            if result["success"] and result["lat"] != 0 and result["lng"] != 0:
                return {
                    "lat": result["lat"],
                    "lng": result["lng"]
                }
        
        return None
    
    def _geocode_address(self, address: str) -> Dict[str, Any]:
        """
        地址地理编码（内部方法）
        
        Args:
            address: 地址字符串
            
        Returns:
            包含详细信息的结果字典
        """
        # 地址预处理
        cleaned_address = clean_text(address)
        
        if not cleaned_address:
            return {
                "lat": 0,
                "lng": 0,
                "success": False,
                "error": "地址为空"
            }
        
        # 重试机制
        for attempt in range(self.max_retries):
            try:
                if self.service_type == "amap":
                    result = self._geocode_amap(cleaned_address)
                elif self.service_type == "tencent":
                    result = self._geocode_tencent(cleaned_address)
                else:
                    return {
                        "lat": 0,
                        "lng": 0,
                        "success": False,
                        "error": f"不支持的服务类型: {self.service_type}"
                    }
                
                if result["success"]:
                    return result
                
                # 如果是最后一次尝试，返回错误
                if attempt == self.max_retries - 1:
                    return result
                
                # 否则继续重试
                time.sleep(1)
                continue
                    
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return {
                        "lat": 0,
                        "lng": 0,
                        "success": False,
                        "error": f"请求异常: {str(e)}"
                    }
                time.sleep(1)
                continue
        
        # 不应该到达这里
        return {
            "lat": 0,
            "lng": 0,
            "success": False,
            "error": "所有重试都失败"
        }
    
    def _geocode_amap(self, address: str) -> Dict[str, Any]:
        """高德地图地理编码"""
        params = {
            "address": address,
            "key": self.api_key,
            "output": "json"
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data["status"] == "1" and data["geocodes"]:
                geocode = data["geocodes"][0]
                location = geocode["location"].split(",")
                
                return {
                    "lat": float(location[1]),  # 高德地图返回格式：经度,纬度
                    "lng": float(location[0]),
                    "success": True,
                    "formatted_address": geocode.get("formatted_address", address)
                }
            else:
                return {
                    "lat": 0,
                    "lng": 0,
                    "success": False,
                    "error": data.get("info", "未知错误"),
                    "error_code": data.get("infocode", "")
                }
                
        except requests.exceptions.Timeout:
            return {
                "lat": 0,
                "lng": 0,
                "success": False,
                "error": "请求超时"
            }
        except requests.exceptions.RequestException as e:
            return {
                "lat": 0,
                "lng": 0,
                "success": False,
                "error": f"网络请求错误: {str(e)}"
            }
        except json.JSONDecodeError:
            return {
                "lat": 0,
                "lng": 0,
                "success": False,
                "error": "API响应格式错误"
            }
        except (ValueError, IndexError) as e:
            return {
                "lat": 0,
                "lng": 0,
                "success": False,
                "error": f"坐标解析错误: {str(e)}"
            }
    
    def _geocode_tencent(self, address: str) -> Dict[str, Any]:
        """腾讯地图地理编码"""
        params = {
            "address": address,
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
                    "formatted_address": data["result"].get("formatted_addresses", {}).get("recommend", address)
                }
            else:
                return {
                    "lat": 0,
                    "lng": 0,
                    "success": False,
                    "error": data.get('message', '未知错误'),
                    "error_code": data.get('status', -1)
                }
                
        except requests.exceptions.Timeout:
            return {
                "lat": 0,
                "lng": 0,
                "success": False,
                "error": "请求超时"
            }
        except requests.exceptions.RequestException as e:
            return {
                "lat": 0,
                "lng": 0,
                "success": False,
                "error": f"网络请求错误: {str(e)}"
            }
        except json.JSONDecodeError:
            return {
                "lat": 0,
                "lng": 0,
                "success": False,
                "error": "API响应格式错误"
            }
    
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
    
    def get_service_info(self) -> Dict[str, str]:
        """获取服务信息"""
        return {
            "service_type": self.service_type,
            "service_name": self.service_name,
            "base_url": self.base_url
        }


# 工厂函数
def create_geocoding_service(api_key: str, service_type: str = "amap") -> GeocodingService:
    """
    创建地理编码服务实例
    
    Args:
        api_key: API密钥
        service_type: 服务类型 ("amap" 或 "tencent")
        
    Returns:
        地理编码服务实例
    """
    return GeocodingService(api_key, service_type) 