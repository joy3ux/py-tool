import os
import sys
import subprocess
from PyInstaller.__main__ import run

def get_tkinter_tcl_path():
    """获取当前 Python 安装的 Tcl/Tk 路径"""
    import tkinter
    root = tkinter.Tk()
    tcl_dir = root.tk.exprstring('$tcl_library')
    tk_dir = root.tk.exprstring('$tk_library')
    root.destroy()
    return tcl_dir, tk_dir

def build_executable():
    # 获取 Tcl/Tk 路径
    tcl_dir, tk_dir = get_tkinter_tcl_path()
    
    # 确保路径存在
    if not os.path.exists(tcl_dir) or not os.path.exists(tk_dir):
        print(f"错误: 找不到 Tcl/Tk 文件\nTcl: {tcl_dir}\nTk: {tk_dir}")
        sys.exit(1)
    
    # PyInstaller 配置
    options = [
        'image_compressor.py',
        '--name=ImageCompressor',
        '--onefile',
        '--windowed',
        '--add-data', f'{tcl_dir};tcl',
        '--add-data', f'{tk_dir};tk',
        '--clean'
    ]
    
    # 添加图标（如果存在）
    if os.path.exists("app_icon.ico"):
        options.append('--icon=app_icon.ico')
    
    print("开始打包...")
    print(f"Tcl 路径: {tcl_dir}")
    print(f"Tk 路径: {tk_dir}")
    
    run(options)

if __name__ == "__main__":
    build_executable()
