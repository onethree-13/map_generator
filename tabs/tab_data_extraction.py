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
import base64
import time
from utils.data_manager import DataManager


class DataExtractionTab:
    """数据提取标签页"""
    
    def __init__(self, data_manager: DataManager, processor):
        self.data_manager = data_manager
        self.processor = processor
    
    def render(self):
        """渲染数据提取标签页"""
        st.info("步骤1: 输入地图点信息")

        # 输入模式选择
        input_mode = st.radio(
            "请选择数据输入方式：",
            ["📷 上传图片", "🌐 图片链接", "📝 直接输入文本", "📋 直接导入JSON"],
            horizontal=True,
            help="支持多种数据输入方式，选择最适合您的方式"
        )

        st.markdown("---")

        # 根据输入模式显示不同的界面
        if input_mode == "📷 上传图片":
            self._render_image_upload()
        elif input_mode == "🌐 图片链接":
            self._render_image_url()
        elif input_mode == "📝 直接输入文本":
            self._render_text_input()
        elif input_mode == "📋 直接导入JSON":
            self._render_json_import()

        # 显示提取的文字内容和JSON生成（只有在非JSON导入模式下才显示）
        if self.data_manager.has_extracted_text() and "已导入" not in self.data_manager.get_extracted_text():
            self._render_content_editing()
    
    def _render_image_upload(self):
        """渲染图片上传界面"""
        st.subheader("📷 图片上传")
        st.info("💡 支持PNG、JPG、JPEG、WEBP格式的图片文件，文件最大为10MB")
        
        uploaded_file = st.file_uploader(
            "选择图片文件",
            type=['png', 'jpg', 'jpeg', 'webp'],
            help="支持PNG、JPG、JPEG、WEBP格式的图片文件"
        )

        if uploaded_file is not None:
            col1, col2 = st.columns([1, 1])

            with col1:
                st.image(uploaded_file, caption="上传的图片", use_container_width=True)
                st.info(f"""
                **文件信息:**
                - 文件名: {uploaded_file.name}
                - 文件大小: {uploaded_file.size / 1024:.1f} KB
                - 文件类型: {uploaded_file.type}
                """)

            with col2:
                st.subheader("🤖 AI文字提取")
                if st.button("🚀 开始提取文字", type="primary", use_container_width=True, key="extract_upload"):
                    self._extract_text_from_uploaded_file(uploaded_file)
    
    def _render_image_url(self):
        """渲染图片链接输入界面"""
        st.subheader("🌐 图片链接输入")
        st.info("💡 支持PNG、JPG、JPEG、WEBP格式的图片文件，文件最大为10MB")
        
        image_url = st.text_input(
            "请输入图片链接地址：",
            placeholder="https://example.com/image.jpg",
            help="支持HTTP/HTTPS图片链接，建议使用常见图片格式"
        )

        if image_url:
            col1, col2 = st.columns([1, 1])

            with col1:
                try:
                    st.image(image_url, caption="图片预览", use_container_width=True)
                    st.success("✅ 图片链接有效")
                except Exception as e:
                    st.error(f"❌ 图片链接无效: {str(e)}")
                    st.info("💡 请检查图片链接是否正确，确保可以直接访问")

            with col2:
                st.subheader("🤖 AI文字提取")
                if st.button("🚀 开始提取文字", type="primary", use_container_width=True, key="extract_url"):
                    self._extract_text_from_url(image_url)
    
    def _render_text_input(self):
        """渲染文本直接输入界面"""
        st.subheader("📝 文本直接输入")
        st.info("💡 如果您已经有了需要整理的文字内容，可以直接输入进行结构化处理")

        text_input = st.text_area(
            "请输入要处理的文字内容：",
            placeholder="请输入包含地点信息的文字内容，如从其他来源复制的地址、电话、商家信息等...",
            height=200,
            help="支持直接输入文字进行结构化处理，跳过OCR步骤"
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            if text_input:
                st.write(f"**文字长度:** {len(text_input)} 字符")
                st.write(f"**行数:** {len(text_input.split(chr(10)))} 行")

        with col2:
            if st.button("✅ 确认使用此文本", type="primary", use_container_width=True, key="extract_text"):
                try:
                    self.data_manager.set_extracted_text(text_input)
                    st.success("✅ 文本内容已确认！")
                    st.info("💡 请继续下一步：生成结构化数据")
                    st.rerun()
                except ValueError as e:
                    st.error(f"❌ 输入错误: {str(e)}")
                except Exception as e:
                    st.error(f"❌ 处理失败: {str(e)}")
    
    def _render_json_import(self):
        """渲染JSON导入界面"""
        st.subheader("📋 JSON数据直接导入")
        st.info("💡 如果您已经有JSON格式的地点数据，可以直接粘贴进行编辑和修改")

        json_input = st.text_area(
            "请粘贴JSON数据：",
            placeholder=self._get_json_placeholder(),
            height=300,
            help="支持完整地图JSON或仅包含data数组的JSON格式"
        )

        col1, col2 = st.columns([2, 1])

        with col1:
            if json_input:
                self._validate_and_preview_json(json_input)

        with col2:
            if st.button("✅ 导入JSON数据", type="primary", use_container_width=True, key="import_json"):
                self._import_json_data(json_input)

    def _render_content_editing(self):
        """渲染内容编辑界面（包含提取的文字和JSON生成）"""
        st.markdown("---")
        st.header("步骤2: 内容编辑与JSON生成")

        # 创建两列布局
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📄 提取的文字内容")
            
            # 可编辑的文字内容
            current_text = self.data_manager.get_extracted_text()
            edited_text = st.text_area(
                "编辑提取的文字内容：",
                value=current_text,
                height=300,
                help="您可以编辑提取的文字内容，修改后会影响JSON生成结果",
                key="extracted_text_editor"
            )
            
            # 如果文字内容被修改，更新到data_manager
            if edited_text != current_text:
                if st.button("💾 保存文字修改", key="save_text_changes"):
                    self.data_manager.set_extracted_text(edited_text)
                    st.success("✅ 文字内容已保存！")
                    st.rerun()

        with col2:
            st.subheader("🎯 JSON结构生成")
            
            # 自定义指导提示
            custom_prompt = st.text_area(
                "自定义指导提示 (可选)",
                value="",
                height=100,
                placeholder="在这里输入额外的指导要求，例如：\n- 请特别注意识别餐厅的营业时间\n- 优先提取景点的门票信息\n- 重点关注商家的优惠活动信息\n- 请严格按照地址格式整理",
                help="这些自定义指导将帮助AI更准确地理解和整理您的数据"
            )

            # JSON生成按钮组
            col_btn1, col_btn2, col_btn3 = st.columns(3)

            with col_btn1:
                if st.button("🔄 生成JSON结构", type="primary", use_container_width=True, key="generate_json"):
                    self._execute_json_generation(custom_prompt)

            with col_btn2:
                if st.button("✅ 应用生成结果", use_container_width=True,
                            disabled=not self.data_manager.has_pending_edits(),
                            help="将生成的结果应用到保存版本", key="apply_json"):
                    self._apply_json_generation()

            with col_btn3:
                if st.button("↩️ 撤销生成", use_container_width=True,
                            disabled=not self.data_manager.has_pending_edits(),
                            help="撤销生成结果，恢复到之前状态", key="undo_json"):
                    self._undo_json_generation()

        # 显示生成的JSON内容（全宽度）
        st.markdown("---")
        st.subheader("📋 生成的JSON结构")
        
        # 显示生成状态
        if self.data_manager.has_pending_edits():
            st.info("💡 有新生成的数据待确认，请点击'应用生成结果'保存，或点击'撤销生成'取消")
            # 显示待确认的JSON
            editing_json = self.data_manager.get_editing_json()
            if editing_json:
                json_str = json.dumps(editing_json, ensure_ascii=False, indent=2)
                st.text_area(
                    "待确认的JSON结构：",
                    value=json_str,
                    height=400,
                    help="这是AI生成的JSON结构，请确认后点击'应用生成结果'",
                    disabled=True,
                    key="pending_json_display"
                )
        elif self.data_manager.has_saved_json():
            st.success("📝 JSON数据已生成并保存！可在其他标签页查看和编辑完整数据。")
            # 显示已保存的JSON
            saved_json = self.data_manager.get_saved_json()
            json_str = json.dumps(saved_json, ensure_ascii=False, indent=2)
            st.text_area(
                "已保存的JSON结构：",
                value=json_str,
                height=400,
                help="这是已保存的JSON结构",
                disabled=True,
                key="saved_json_display"
            )
        else:
            st.info("💡 点击'生成JSON结构'按钮开始生成结构化数据")
    
    def _execute_json_generation(self, custom_prompt):
        """执行JSON结构生成"""
        progress_placeholder = st.empty()
        
        try:
            with st.spinner("正在整理数据..."):
                json_data = self.processor.generate_json_structure(
                    self.data_manager.get_extracted_text(),
                    custom_prompt,
                    progress_placeholder
                )

            progress_placeholder.empty()
            if json_data:
                # 保存到editing_json作为待确认的结果
                self.data_manager.set_editing_json(json_data)
                st.success("✅ JSON结构生成成功！请确认结果后点击'应用生成结果'")
                st.rerun()
            else:
                st.error("❌ JSON生成失败，请检查提取的文字内容")
        except ValueError as e:
            progress_placeholder.empty()
            st.error(f"❌ 配置错误: {str(e)}")
            st.info("💡 请在侧边栏中配置正确的通义千问API密钥，然后点击\"更新配置\"按钮")
        except Exception as e:
            progress_placeholder.empty()
            st.error(f"❌ 处理失败: {str(e)}")
            st.info("💡 请检查网络连接和API密钥配置")
    
    def _apply_json_generation(self):
        """应用JSON生成结果到保存版本"""
        self.data_manager.apply_edits()
        st.success("✅ JSON生成结果已应用到保存版本！")
        st.rerun()
    
    def _undo_json_generation(self):
        """撤销JSON生成结果"""
        self.data_manager.discard_edits()
        st.success("✅ 已撤销JSON生成结果")
        st.rerun()
    
    def _extract_text_from_uploaded_file(self, uploaded_file):
        """从上传的文件提取文字"""
        progress_placeholder = st.empty()

        try:
            with st.spinner("正在分析图片..."):
                extracted_text = self.processor.extract_text_from_image(uploaded_file, progress_placeholder)
            
            progress_placeholder.empty()
            self.data_manager.set_extracted_text(extracted_text)
            st.success("✅ 文字提取完成！")
            st.rerun()
        except ValueError as e:
            progress_placeholder.empty()
            st.error(f"❌ 配置错误: {str(e)}")
            st.info("💡 请在侧边栏中配置正确的通义千问API密钥，然后点击\"更新配置\"按钮")
        except Exception as e:
            progress_placeholder.empty()
            st.error(f"❌ 处理失败: {str(e)}")
            st.info("💡 请检查网络连接和API密钥配置")
    
    def _extract_text_from_url(self, image_url):
        """从图片URL提取文字"""
        progress_placeholder = st.empty()

        try:
            with st.spinner("正在处理图片..."):
                extracted_text, img_pil = self.processor.extract_text_from_url(image_url, progress_placeholder)

            progress_placeholder.empty()
            self.data_manager.set_extracted_text(extracted_text)
            st.success("✅ 文字提取完成！")

            st.info(f"""
            **图片信息:**
            - 尺寸: {img_pil.size[0]} x {img_pil.size[1]} 像素
            - 模式: {img_pil.mode}
            - 格式: PNG (转换后)
            """)
            st.rerun()
        except ValueError as e:
            progress_placeholder.empty()
            st.error(f"❌ 处理错误: {str(e)}")
            if "API密钥" in str(e):
                st.info("💡 请在侧边栏中配置正确的通义千问API密钥，然后点击\"更新配置\"按钮")
            else:
                st.info("💡 请检查图片链接是否正确，或尝试其他图片")
        except Exception as e:
            progress_placeholder.empty()
            st.error(f"❌ 处理失败: {str(e)}")
            st.info("💡 请检查网络连接和图片链接")
    
    def _get_json_placeholder(self):
        """获取JSON输入的placeholder文本"""
        return """请粘贴完整的JSON数据，支持以下格式：

1. 完整地图格式：
{
  "name": "地图名称",
  "description": "地图描述",
  "origin": "数据来源",
  "filter": {
    "inclusive": {"类型": ["餐厅", "咖啡厅"]},
    "exclusive": {}
  },
  "data": [
    {
      "name": "地点名称",
      "address": "地址",
      "phone": "电话",
      "webName": "网站/公众号",
      "webLink": "网站链接",
      "intro": "简介",
      "tags": ["标签"],
      "center": {"lat": 0, "lng": 0}
    }
  ]
}

2. 仅数据格式：
{
  "data": [
    {
      "name": "地点名称",
      "address": "地址",
      "phone": "电话",
      "webName": "网站/公众号",
      "webLink": "网站链接",
      "intro": "简介",
      "tags": ["标签"],
      "center": {"lat": 0, "lng": 0}
    }
  ]
}"""
    
    def _validate_and_preview_json(self, json_input):
        """验证和预览JSON"""
        # 使用data_manager的JSON语法验证
        is_valid, error_msg = self.data_manager.validate_json_syntax(json_input)
        
        if not is_valid:
            st.error(f"❌ {error_msg}")
            st.info("💡 请检查JSON语法是否正确，注意逗号、引号、括号等符号")
            return
        else:
            st.success("✅ JSON格式正确！")

    
    def _import_json_data(self, json_input):
        """导入JSON数据"""
        if not json_input.strip():
            st.error("❌ 请先输入JSON数据")
            return

        # 使用data_manager的JSON语法验证
        is_valid, error_msg = self.data_manager.validate_json_syntax(json_input)
        
        if not is_valid:
            st.error(f"❌ {error_msg}")
            return

        try:
            parsed_json = json.loads(json_input)

            # 处理不同的JSON格式
            if isinstance(parsed_json, list):
                parsed_json = {"data": parsed_json}

            if "data" not in parsed_json:
                st.error("❌ JSON中必须包含'data'字段")
                return

            # 检查是否包含地图信息
            map_info_fields = ["name", "description", "origin", "filter"]
            has_map_info = any(key in parsed_json for key in map_info_fields)

            if has_map_info:
                # 导入完整的JSON结构（包含地图信息）
                self.data_manager.set_saved_json(parsed_json)
                st.success("✅ 地点数据和地图信息导入成功！")
                st.info("🗺️ 地图信息已同步更新，可在'地图信息'标签页查看")

                # 显示导入的地图信息预览
                self._show_imported_map_info(parsed_json)
            else:
                # 仅导入地点数据，创建基本结构
                basic_json = {
                    "name": "",
                    "description": "",
                    "origin": "",
                    "filter": {"inclusive": {}, "exclusive": {}},
                    "data": parsed_json["data"]
                }
                self.data_manager.set_saved_json(basic_json)
                st.success("✅ 地点数据导入成功！")
                st.info("💡 如需要，可在'地图信息'标签页设置地图基本信息")


            # 设置提取的文字为特殊标记
            self.data_manager.set_extracted_text(f"已导入 {len(parsed_json['data'])} 个地点的JSON数据")
            st.rerun()

        except Exception as e:
            st.error(f"❌ 导入失败: {str(e)}")
    

    
    def _show_imported_map_info(self, parsed_json):
        """显示导入的地图信息预览"""
        imported_fields = []
        if "name" in parsed_json:
            imported_fields.append(f"名称: {parsed_json['name']}")
        if "description" in parsed_json:
            imported_fields.append(f"描述: {parsed_json['description'][:50]}...")
        if "origin" in parsed_json:
            imported_fields.append(f"来源: {parsed_json['origin']}")
        if "filter" in parsed_json:
            filter_count = len(parsed_json["filter"].get("inclusive", {})) + \
                          len(parsed_json["filter"].get("exclusive", {}))
            imported_fields.append(f"过滤器: {filter_count} 个类别")

        if imported_fields:
            st.markdown("**导入的地图信息:**")
            for field in imported_fields:
                st.write(f"• {field}") 