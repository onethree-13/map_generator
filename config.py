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
配置管理模块
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

class Config:
    """应用配置类"""
    
    # 默认配置
    DEFAULT_CONFIG = {
        "TENCENT_API_KEY": "",  # 腾讯地图API密钥，请通过环境变量设置
        "AMAP_API_KEY": "",     # 高德地图API密钥，请通过环境变量设置
        "OPENAI_API_KEY": "",   # OpenAI API密钥，请通过环境变量设置
        "OPENAI_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "OCR_MODEL": "qwen-vl-max-latest",
        "TEXT_MODEL": "qwen-max-latest",
        "REQUEST_INTERVAL": 1,
        "MAX_FILE_SIZE": 10 * 1024 * 1024,  # 10MB
        "SUPPORTED_FORMATS": ["png", "jpg", "jpeg", "webp"],
        "DEFAULT_FILENAME": "map_data.json",
        "DEFAULT_MAP_SERVICE": "amap",  # 默认使用高德地图
        "MAP_SERVICES": {
            "amap": {
                "name": "高德地图",
                "api_key_env": "AMAP_API_KEY",
                "geocoding_url": "https://restapi.amap.com/v3/geocode/geo"
            },
            "tencent": {
                "name": "腾讯地图", 
                "api_key_env": "TENCENT_API_KEY",
                "geocoding_url": "https://apis.map.qq.com/ws/geocoder/v1/"
            }
        }
    }
    
    def __init__(self):
        self.config = self.DEFAULT_CONFIG.copy()
        # 先加载.env文件
        self.load_env_file()
        # 再从环境变量加载配置
        self.load_from_env()
    
    def load_env_file(self):
        """加载.env文件"""
        try:
            # 加载项目根目录下的.env文件
            load_dotenv()
            print("已加载.env文件")
        except Exception as e:
            print(f"加载.env文件失败: {e}")
    
    def load_from_env(self):
        """从环境变量加载配置"""
        for key in self.config:
            env_value = os.getenv(key)
            if env_value:
                # 尝试转换类型
                if isinstance(self.config[key], int):
                    try:
                        self.config[key] = int(env_value)
                    except ValueError:
                        pass
                elif isinstance(self.config[key], float):
                    try:
                        self.config[key] = float(env_value)
                    except ValueError:
                        pass
                elif isinstance(self.config[key], list):
                    self.config[key] = env_value.split(',')
                else:
                    self.config[key] = env_value
    
    def get(self, key: str, default=None):
        """获取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self.config[key] = value
    
    def update(self, updates: Dict[str, Any]):
        """批量更新配置"""
        self.config.update(updates)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return self.config.copy()
    
    def get_map_service_config(self, service_name: str = None) -> Dict[str, Any]:
        """获取地图服务配置"""
        if service_name is None:
            service_name = self.get("DEFAULT_MAP_SERVICE", "amap")
        
        services = self.get("MAP_SERVICES", {})
        return services.get(service_name, services.get("amap", {}))
    
    def get_available_map_services(self) -> Dict[str, str]:
        """获取可用的地图服务列表"""
        services = self.get("MAP_SERVICES", {})
        return {key: config["name"] for key, config in services.items()}

# 全局配置实例
config = Config()

# 便捷访问函数
def get_config(key: str, default=None):
    """获取配置值"""
    return config.get(key, default)

def set_config(key: str, value: Any):
    """设置配置值"""
    config.set(key, value)

def update_config(updates: Dict[str, Any]):
    """批量更新配置"""
    config.update(updates) 