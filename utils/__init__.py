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
Utils package for map generator components.

This package contains utility components for the map generator application:
- DataManager: Manages all JSON data, extracted text, and map information
- MapDataProcessor: Handles AI-related functionality for map data processing
- GeoService: Provides geographical services and coordinate operations
- SidebarComponents: Contains sidebar UI components and configuration
- MapUtils: Provides map center and zoom calculation utilities
- JSONEditor: Provides unified JSON preview and editing functionality
"""

from .data_manager import DataManager
from .map_data_processor import MapDataProcessor
from .geo_service import GeocodingService
from .sidebar_components import SidebarComponents
from .map_utils import MapUtils, calculate_map_center_and_zoom, format_map_config_for_export
from .json_editor import JSONEditor

__all__ = [
    'DataManager',
    'MapDataProcessor', 
    'GeocodingService',
    'SidebarComponents',
    'MapUtils',
    'calculate_map_center_and_zoom',
    'format_map_config_for_export',
    'JSONEditor'
] 