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

#!/usr/bin/env python3
"""
AI地图数据提取工具启动脚本
支持虚拟环境创建和管理，使用阿里云镜像源加速安装
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

# 虚拟环境配置
VENV_NAME = "map_env"
PYPI_MIRROR = "https://mirrors.aliyun.com/pypi/simple/"

def get_venv_paths():
    """获取虚拟环境路径"""
    venv_dir = Path(VENV_NAME)
    
    if platform.system() == "Windows":
        python_exe = venv_dir / "Scripts" / "python.exe"
        pip_exe = venv_dir / "Scripts" / "pip.exe"
        activate_script = venv_dir / "Scripts" / "activate.bat"
    else:
        python_exe = venv_dir / "bin" / "python"
        pip_exe = venv_dir / "bin" / "pip"
        activate_script = venv_dir / "bin" / "activate"
    
    return venv_dir, python_exe, pip_exe, activate_script

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    
    print(f"✅ Python版本检查通过: {sys.version}")
    return True

def create_venv():
    """创建虚拟环境"""
    venv_dir, python_exe, pip_exe, activate_script = get_venv_paths()
    
    if venv_dir.exists():
        print(f"✅ 虚拟环境已存在: {VENV_NAME}")
        return True
    
    print(f"📦 创建虚拟环境: {VENV_NAME}")
    try:
        subprocess.check_call([sys.executable, "-m", "venv", VENV_NAME])
        print(f"✅ 虚拟环境创建成功: {VENV_NAME}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 虚拟环境创建失败: {e}")
        return False

def activate_venv():
    """激活虚拟环境并返回Python可执行文件路径"""
    venv_dir, python_exe, pip_exe, activate_script = get_venv_paths()
    
    if not python_exe.exists():
        print(f"❌ 虚拟环境Python不存在: {python_exe}")
        return None, None
    
    print(f"🔧 使用虚拟环境: {python_exe}")
    return str(python_exe), str(pip_exe)

def upgrade_pip(pip_exe):
    """升级pip到最新版本"""
    print("🔄 升级pip...")
    try:
        subprocess.check_call([pip_exe, "install", "--upgrade", "pip"])
        print("✅ pip升级完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"⚠️ pip升级失败，继续安装: {e}")
        return True  # 即使升级失败也继续

def install_requirements(pip_exe):
    """使用阿里云镜像源安装依赖"""
    if not os.path.exists("requirements.txt"):
        print("❌ 找不到requirements.txt文件")
        return False
    
    print(f"📦 使用阿里云镜像源安装依赖...")
    print(f"镜像源: {PYPI_MIRROR}")
    
    try:
        # 先升级pip
        upgrade_pip(pip_exe)
        
        # 安装依赖
        cmd = [pip_exe, "install", "-r", "requirements.txt", "-i", PYPI_MIRROR, "--trusted-host", "mirrors.aliyun.com"]
        subprocess.check_call(cmd)
        print("✅ 依赖安装完成")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        print("💡 请尝试手动安装:")
        print(f"   {pip_exe} install -r requirements.txt -i {PYPI_MIRROR}")
        return False

def check_dependencies(python_exe):
    """检查关键依赖是否已安装"""
    print("🔍 检查关键依赖...")
    
    critical_packages = ["streamlit", "openai", "requests", "pandas", "pillow"]
    missing_packages = []
    
    for package in critical_packages:
        try:
            result = subprocess.run(
                [python_exe, "-c", f"import {package}; print('{package}: OK')"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"  ✅ {package}")
        except subprocess.CalledProcessError:
            missing_packages.append(package)
            print(f"  ❌ {package}")
    
    if missing_packages:
        print(f"⚠️ 缺少依赖: {', '.join(missing_packages)}")
        return False
    
    print("✅ 所有关键依赖已安装")
    return True

def run_streamlit_app(python_exe):
    """在虚拟环境中启动Streamlit应用"""
    if not os.path.exists("app.py"):
        print("❌ 找不到主程序文件 app.py")
        return False
    
    print("\n🌐 启动AI地图数据提取工具...")
    print("=" * 60)
    print("🔗 应用地址: http://localhost:8501")
    print("⌨️  按 Ctrl+C 退出应用")
    print("💡 如果浏览器未自动打开，请手动访问上述地址")
    print("=" * 60)
    
    try:
        # 在虚拟环境中运行streamlit
        cmd = [
            python_exe, "-m", "streamlit", "run", "app.py",
            "--server.address", "localhost",
            "--server.port", "8501",
            "--server.headless", "true",
            "--server.fileWatcherType", "none"
        ]
        
        subprocess.run(cmd)
        return True
        
    except KeyboardInterrupt:
        print("\n👋 应用已关闭")
        return True
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False

def show_environment_info():
    """显示环境信息"""
    venv_dir, python_exe, pip_exe, activate_script = get_venv_paths()
    
    print("\n📋 环境信息:")
    print(f"  🐍 Python版本: {sys.version}")
    print(f"  📁 工作目录: {os.getcwd()}")
    print(f"  🏠 虚拟环境: {venv_dir.absolute()}")
    print(f"  🔧 Python路径: {python_exe}")
    print(f"  📦 pip路径: {pip_exe}")
    print(f"  🌏 镜像源: {PYPI_MIRROR}")

def main():
    """主函数"""
    print("🗺️ AI地图数据提取工具 - 启动脚本")
    print("版本: 1.1.1 (支持虚拟环境)")
    print("=" * 60)
    
    # 1. 检查Python版本
    if not check_python_version():
        return
    
    # 2. 创建虚拟环境
    if not create_venv():
        return
    
    # 3. 激活虚拟环境
    python_exe, pip_exe = activate_venv()
    if not python_exe:
        return
    
    # 4. 安装依赖
    print(f"\n📦 依赖管理 (虚拟环境: {VENV_NAME})")
    if not install_requirements(pip_exe):
        print("\n💡 你也可以手动安装依赖:")
        print(f"   1. 激活虚拟环境: {VENV_NAME}")
        if platform.system() == "Windows":
            print(f"      {VENV_NAME}\\Scripts\\activate.bat")
        else:
            print(f"      source {VENV_NAME}/bin/activate")
        print(f"   2. 安装依赖: pip install -r requirements.txt -i {PYPI_MIRROR}")
        return
    
    # 5. 检查依赖
    if not check_dependencies(python_exe):
        print("⚠️ 某些依赖缺失，但尝试启动应用...")
    
    # 6. 显示环境信息
    show_environment_info()
    
    # 7. 启动应用
    input("\n按回车键启动应用...")
    if not run_streamlit_app(python_exe):
        return
    
    print("\n🎉 感谢使用AI地图数据提取工具！")

if __name__ == "__main__":
    main() 