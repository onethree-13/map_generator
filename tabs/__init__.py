"""
标签页模块包
包含所有的标签页类
"""

from .tab_data_extraction import DataExtractionTab
from .tab_map_info import MapInfoTab
from .tab_data_editing import DataEditingTab
from .tab_tag_management import TagManagementTab
from .tab_coordinate_management import CoordinateManagementTab
from .tab_data_export import DataExportTab
from .tab_json_editor import JSONEditorTab
from .tab_manager import TabManager

__all__ = [
    'DataExtractionTab',
    'MapInfoTab', 
    'DataEditingTab',
    'TagManagementTab',
    'CoordinateManagementTab',
    'DataExportTab',
    'JSONEditorTab',
    'TabManager'
] 