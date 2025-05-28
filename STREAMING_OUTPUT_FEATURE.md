# JSON流式输出功能与界面改进

## 功能概述

为了提升用户体验，我们为JSON生成和AI编辑功能添加了流式输出显示，类似于图片文字提取功能。同时，我们还改进了界面设计，将提取的文字和生成的JSON都显示在可编辑的text_area中，让用户可以实时查看和编辑内容。

## 主要改进

### 1. 流式输出显示
- JSON生成过程中实时显示AI生成的内容
- AI编辑过程中显示实时进度
- 与图片文字提取功能保持一致的用户体验

### 2. 界面优化
- **可编辑的文字内容**: 提取的文字显示在可编辑的text_area中，用户可以修改
- **实时JSON显示**: 生成的JSON结构立即显示在text_area中，不会消失
- **双列布局**: 文字编辑和JSON生成并排显示，提高效率
- **移除折叠界面**: 移除了`_render_extracted_text`方法，内容直接可见

## 修改的文件

### 1. `utils/map_data_processor.py`

#### `generate_json_structure` 方法
- **修改前**: 使用非流式API调用，用户只能看到spinner等待
- **修改后**: 添加了 `progress_placeholder` 参数，支持流式输出
- **新功能**: 实时显示JSON生成过程，每个chunk都会更新显示内容

```python
def generate_json_structure(self, extracted_text, custom_prompt="", progress_placeholder=None):
    # ... 其他代码 ...
    completion = self.openai_client.chat.completions.create(
        # ... 其他参数 ...
        stream=True,  # 启用流式输出
    )

    full_content = ""
    for chunk in completion:
        if chunk.choices and chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            full_content += content
            if progress_placeholder:
                progress_placeholder.text(f"正在生成JSON结构...\n{full_content}")
                time.sleep(0.05)
```

#### `ai_edit_json_data` 方法
- **修改前**: 使用非流式API调用
- **修改后**: 添加了 `progress_placeholder` 参数，支持流式输出
- **新功能**: 实时显示AI编辑过程

### 2. `tabs/tab_data_extraction.py`

#### 重大界面改进
- **移除**: `_render_extracted_text()` 方法
- **新增**: `_render_content_editing()` 方法，整合文字编辑和JSON生成
- **改进**: 双列布局，左侧文字编辑，右侧JSON生成控制

#### 新的界面结构
```python
def _render_content_editing(self):
    """渲染内容编辑界面（包含提取的文字和JSON生成）"""
    # 双列布局
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # 可编辑的文字内容
        edited_text = st.text_area(
            "编辑提取的文字内容：",
            value=current_text,
            height=300,
            key="extracted_text_editor"
        )
    
    with col2:
        # JSON生成控制
        # 自定义提示和生成按钮
    
    # 全宽度显示生成的JSON
    st.text_area("生成的JSON结构", ...)
```

#### `_execute_json_generation` 方法
- **修改**: 添加了 `progress_placeholder` 创建和传递
- **新功能**: 在JSON生成过程中显示实时进度

### 3. `tabs/tab_data_editing.py`

#### `_execute_ai_edit` 方法
- **修改**: 添加了流式输出支持
- **新功能**: AI编辑过程中显示实时进度

### 4. `tabs/tab_tag_management.py`

#### `_execute_ai_tag_editing` 方法
- **修改**: 添加了流式输出支持
- **新功能**: AI标签编辑过程中显示实时进度

## 用户体验改进

### 之前的体验
- 用户点击"生成JSON结构"后只能看到spinner
- 提取的文字内容隐藏在折叠面板中
- 无法编辑提取的文字内容
- JSON生成结果不直观显示

### 现在的体验
- **实时反馈**: 用户可以实时看到AI生成的JSON内容
- **可编辑内容**: 提取的文字内容可以直接编辑和保存
- **直观显示**: JSON结果立即显示在text_area中，不会消失
- **高效布局**: 双列布局让文字编辑和JSON生成并行进行
- **持久化内容**: 生成的内容保持可见，用户可以随时查看

## 界面布局

### 新的布局结构
```
┌─────────────────────────────────────────────────────────────┐
│                    步骤2: 内容编辑与JSON生成                    │
├─────────────────────────┬───────────────────────────────────┤
│     📄 提取的文字内容      │        🎯 JSON结构生成           │
│                        │                                  │
│  ┌─────────────────────┐ │  ┌─────────────────────────────┐  │
│  │                    │ │  │     自定义指导提示           │  │
│  │   可编辑文字内容     │ │  │                            │  │
│  │                    │ │  └─────────────────────────────┘  │
│  │                    │ │                                  │
│  └─────────────────────┘ │  [生成] [应用] [撤销]             │
│  [💾 保存文字修改]        │                                  │
└─────────────────────────┴───────────────────────────────────┤
│                    📋 生成的JSON结构                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                                                        │ │
│  │              JSON内容显示区域                           │ │
│  │                                                        │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 技术细节

### 流式输出实现
1. **API调用**: 在OpenAI API调用中添加 `stream=True` 参数
2. **内容累积**: 逐个处理返回的chunk，累积完整内容
3. **实时显示**: 每收到一个chunk就更新progress placeholder
4. **延迟控制**: 添加 `time.sleep(0.05)` 控制显示速度

### 界面状态管理
1. **文字编辑**: 实时检测文字内容变化，提供保存按钮
2. **JSON状态**: 区分待确认和已保存的JSON，分别显示
3. **按钮状态**: 根据数据状态动态启用/禁用按钮

### 兼容性
- 所有修改都是向后兼容的
- `progress_placeholder` 参数是可选的，默认为 `None`
- 如果不传递该参数，功能仍然正常工作，只是没有流式显示

### 错误处理
- 在所有异常处理中都添加了 `progress_placeholder.empty()`
- 确保即使出错也会清理显示内容

## 使用示例

```python
# 在Streamlit应用中使用
progress_placeholder = st.empty()

try:
    result = processor.generate_json_structure(
        text_content,
        custom_prompt,
        progress_placeholder
    )
    progress_placeholder.empty()  # 清理显示
except Exception as e:
    progress_placeholder.empty()  # 确保清理
    # 处理错误
```

## 注意事项

1. **性能**: 流式输出会略微增加处理时间，但提升了用户体验
2. **网络**: 需要稳定的网络连接以确保流式数据传输
3. **API配额**: 流式调用与普通调用消耗相同的API配额
4. **显示控制**: 通过 `time.sleep(0.05)` 控制显示速度，避免过快闪烁
5. **内容编辑**: 用户编辑文字内容后需要点击保存按钮才会更新到系统中

## 未来改进

1. 可以考虑添加进度百分比显示
2. 可以添加取消功能，允许用户中断长时间的生成过程
3. 可以优化显示格式，使JSON内容更易读
4. 可以添加JSON内容的语法高亮显示
5. 可以添加JSON内容的在线编辑功能 