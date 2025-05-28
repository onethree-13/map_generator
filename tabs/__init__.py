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