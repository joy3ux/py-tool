from PIL import Image, ImageTk
import os
import io
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import sys

def compress_image(input_path, output_path, target_kb=500, max_quality=85, min_quality=5, progress_callback=None):
    """
    压缩图片到指定大小
    :param input_path: 输入图片路径
    :param output_path: 输出图片路径
    :param target_kb: 目标大小(KB)
    :param max_quality: 起始质量(85-95为最佳平衡点)
    :param min_quality: 最低质量(避免过度失真)
    :param progress_callback: 进度回调函数
    """
    try:
        # 检查文件是否存在
        if not os.path.exists(input_path):
            return False, "源文件不存在"
        
        # 检查文件大小是否已满足要求
        file_size = os.path.getsize(input_path)
        if file_size <= target_kb * 1024:
            Image.open(input_path).save(output_path)
            if progress_callback:
                progress_callback(100, "图片已小于目标大小，无需压缩", True)
            return True, "图片已小于目标大小，无需压缩"

        img = Image.open(input_path)
        original_format = img.format
        
        # 处理透明通道（转换为JPEG需要RGB）
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
            original_format = 'JPEG'

        # 尝试仅通过调整质量压缩
        quality = max_quality
        while quality >= min_quality:
            buffer = io.BytesIO()
            img.save(buffer, format=original_format, quality=quality)
            size_kb = len(buffer.getvalue()) / 1024
            
            # 计算当前进度百分比
            progress = int((max_quality - quality) / (max_quality - min_quality) * 50)
            if progress_callback:
                progress_callback(progress, f"尝试质量: {quality}%, 当前大小: {size_kb:.1f}KB")
            
            if size_kb <= target_kb:
                with open(output_path, 'wb') as f:
                    f.write(buffer.getvalue())
                if progress_callback:
                    progress_callback(100, f"质量压缩成功: {quality}%, 大小: {size_kb:.2f}KB", True)
                return True, f"质量压缩成功: {quality}%, 大小: {size_kb:.2f}KB"
            
            # 质量调整步长根据剩余空间动态变化
            quality_step = max(1, min(5, int((size_kb - target_kb) / 50)))  # 限制步长范围
            quality -= quality_step
        
        # 如果质量压缩失败，启用尺寸缩减
        scale_factor = 0.9  # 每次缩小10%
        while scale_factor >= 0.1:  # 最小缩放到原图的10%
            # 计算新尺寸
            new_width = int(img.width * scale_factor)
            new_height = int(img.height * scale_factor)
            
            # 避免尺寸过小
            if new_width < 10 or new_height < 10:
                break
                
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)
            
            buffer = io.BytesIO()
            resized_img.save(buffer, format=original_format, quality=85)  # 使用中等质量
            
            size_kb = len(buffer.getvalue()) / 1024
            
            # 更新进度条 (50%-100%)
            progress = 50 + int((0.9 - scale_factor) / (0.9 - 0.1) * 50)
            if progress_callback:
                progress_callback(progress, f"尝试缩放: {scale_factor*100:.1f}%, 大小: {size_kb:.1f}KB")
            
            if size_kb <= target_kb:
                with open(output_path, 'wb') as f:
                    f.write(buffer.getvalue())
                if progress_callback:
                    progress_callback(100, f"尺寸压缩成功: {scale_factor*100:.1f}%, 大小: {size_kb:.2f}KB", True)
                return True, f"尺寸压缩成功: {scale_factor*100:.1f}%, 大小: {size_kb:.2f}KB"
            
            scale_factor = round(scale_factor * 0.9, 2)  # 继续缩小

        return False, "无法压缩到目标大小，建议使用专业工具处理"
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"处理过程中出错: {str(e)}"


class ImageCompressorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图片压缩工具")
        self.root.geometry("650x750")  # 增加窗口大小
        self.root.resizable(True, True)
        self.root.minsize(600, 500)  # 设置最小尺寸
        
        # 设置图标（如果存在）
        self.set_icon()
        
        # 创建UI
        self.create_widgets()
        
        # 初始化变量
        self.input_path = ""
        self.output_path = ""
        self.compression_thread = None
        
    def set_icon(self):
        """尝试设置应用图标"""
        try:
            # 尝试从可执行文件所在目录加载图标
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
                
            icon_path = os.path.join(base_path, "app_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass
        
    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件选择部分
        file_frame = ttk.LabelFrame(main_frame, text="文件选择", padding=10)
        file_frame.pack(fill=tk.X, pady=5)
        
        # 输入文件
        input_frame = ttk.Frame(file_frame)
        input_frame.pack(fill=tk.X, pady=5)
        ttk.Label(input_frame, text="源文件:", width=8).pack(side=tk.LEFT)
        self.input_entry = ttk.Entry(input_frame)
        self.input_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(input_frame, text="浏览...", command=self.browse_input, width=8).pack(side=tk.RIGHT)
        
        # 输出文件
        output_frame = ttk.Frame(file_frame)
        output_frame.pack(fill=tk.X, pady=5)
        ttk.Label(output_frame, text="输出文件:", width=8).pack(side=tk.LEFT)
        self.output_entry = ttk.Entry(output_frame)
        self.output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(output_frame, text="浏览...", command=self.browse_output, width=8).pack(side=tk.RIGHT)
        
        # 压缩设置
        settings_frame = ttk.LabelFrame(main_frame, text="压缩设置", padding=10)
        settings_frame.pack(fill=tk.X, pady=10)
        
        # 目标大小设置
        target_frame = ttk.Frame(settings_frame)
        target_frame.pack(fill=tk.X, pady=5)
        ttk.Label(target_frame, text="目标大小 (KB):", width=15).pack(side=tk.LEFT)
        self.target_var = tk.IntVar(value=500)
        ttk.Entry(target_frame, textvariable=self.target_var, width=10).pack(side=tk.LEFT, padx=5)
        
        # 质量设置
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.pack(fill=tk.X, pady=5)
        ttk.Label(quality_frame, text="最高质量:", width=15).pack(side=tk.LEFT)
        self.max_quality_var = tk.IntVar(value=85)
        quality_scale = ttk.Scale(
            quality_frame, 
            from_=70, 
            to=100, 
            variable=self.max_quality_var,
            orient=tk.HORIZONTAL,
            length=200
        )
        quality_scale.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Label(quality_frame, textvariable=self.max_quality_var, width=3).pack(side=tk.LEFT, padx=(0, 5))
        
        # 预览区域
        preview_frame = ttk.LabelFrame(main_frame, text="图片预览", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 创建画布用于预览
        self.preview_canvas = tk.Canvas(preview_frame, bg='#f0f0f0', height=250)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 预览占位文本
        self.preview_text = self.preview_canvas.create_text(
            150, 100, 
            text="选择图片后将显示预览",
            font=("Arial", 10),
            fill="#999999"
        )
        
        # 进度条
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=10)
        
        self.progress_var = tk.IntVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, expand=True)
        
        # 状态信息
        self.status_var = tk.StringVar(value="准备就绪")
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(fill=tk.X, pady=(0, 10))
        
        # 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 使用grid布局按钮以确保正确显示
        ttk.Button(button_frame, text="开始压缩", command=self.start_compression, width=15).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="打开输出文件夹", command=self.open_output_dir, width=15).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="退出", command=self.root.quit, width=10).grid(row=0, column=2, padx=5)
        
        # 配置列权重，使按钮居中
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        
    def browse_input(self):
        file_path = filedialog.askopenfilename(
            title="选择源图片",
            filetypes=[
                ("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self.input_path = file_path
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, file_path)
            
            # 自动生成输出路径
            dir_name, file_name = os.path.split(file_path)
            name, ext = os.path.splitext(file_name)
            self.output_path = os.path.join(dir_name, f"{name}_compressed{ext}")
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, self.output_path)
            
            # 显示预览
            self.show_preview(file_path)
    
    def show_preview(self, file_path):
        """显示图片预览"""
        try:
            # 清除之前的预览
            self.preview_canvas.delete("preview")
            self.preview_canvas.itemconfig(self.preview_text, text="")
            
            img = Image.open(file_path)
            # 调整大小以适应预览区域
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width < 10 or canvas_height < 10:
                canvas_width, canvas_height = 300, 250
            
            width, height = img.size
            ratio = min(canvas_width/width, canvas_height/height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            
            # 将图像转换为PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # 在画布中央显示图像
            self.preview_canvas.image = photo  # 保持引用
            self.preview_canvas.create_image(
                canvas_width//2, 
                canvas_height//2, 
                image=photo, 
                anchor=tk.CENTER,
                tags="preview"
            )
            
            # 显示图片信息
            file_size = os.path.getsize(file_path) / 1024
            self.status_var.set(f"已加载图片: {width}×{height} 分辨率, 大小: {file_size:.1f}KB")
            
            # 绑定画布大小变化事件
            self.preview_canvas.bind("<Configure>", lambda e: self.update_preview(file_path))
            
        except Exception as e:
            self.preview_canvas.itemconfig(self.preview_text, text=f"无法加载预览: {str(e)}")
            self.status_var.set(f"加载预览失败: {str(e)}")
    
    def update_preview(self, file_path):
        """当画布大小变化时更新预览"""
        if self.input_path:
            self.show_preview(self.input_path)
    
    def browse_output(self):
        if not self.input_path:
            messagebox.showerror("错误", "请先选择源文件")
            return
            
        initial_dir, initial_file = os.path.split(self.output_path if self.output_path else self.input_path)
        file_path = filedialog.asksaveasfilename(
            title="保存压缩图片",
            initialdir=initial_dir,
            initialfile=initial_file,
            filetypes=[
                ("JPEG文件", "*.jpg"),
                ("PNG文件", "*.png"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            self.output_path = file_path
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, file_path)
    
    def start_compression(self):
        if not self.input_path or not os.path.exists(self.input_path):
            messagebox.showerror("错误", "请选择有效的源文件")
            return
            
        if not self.output_path:
            messagebox.showerror("错误", "请指定输出文件路径")
            return
            
        # 禁用按钮避免重复点击
        self.root.config(cursor="watch")
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button) and widget["text"] != "退出":
                widget.state(['disabled'])
        
        # 重置进度
        self.progress_var.set(0)
        self.status_var.set("开始压缩...")
        
        # 在新线程中执行压缩
        self.compression_thread = threading.Thread(
            target=self.run_compression,
            args=(self.input_path, self.output_path),
            daemon=True
        )
        self.compression_thread.start()
        
        # 检查线程状态
        self.check_thread()
    
    def run_compression(self, input_path, output_path):
        target_kb = self.target_var.get()
        max_quality = self.max_quality_var.get()
        
        def progress_callback(progress, message, done=False):
            self.root.after(100, lambda: self.update_progress(progress, message, done))
        
        success, message = compress_image(
            input_path, 
            output_path,
            target_kb=target_kb,
            max_quality=max_quality,
            progress_callback=progress_callback
        )
        
        if not success:
            self.root.after(100, lambda: self.compression_failed(message))
    
    def update_progress(self, progress, message, done):
        self.progress_var.set(progress)
        self.status_var.set(message)
        if done:
            self.compression_complete()
    
    def check_thread(self):
        if self.compression_thread.is_alive():
            self.root.after(100, self.check_thread)
        else:
            self.root.config(cursor="")
    
    def compression_complete(self):
        # 启用按钮
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button) and widget["text"] != "退出":
                widget.state(['!disabled'])
        
        # 显示结果
        if os.path.exists(self.output_path):
            size_kb = os.path.getsize(self.output_path) / 1024
            messagebox.showinfo("压缩成功", 
                               f"图片压缩完成!\n\n"
                               f"输出文件: {os.path.basename(self.output_path)}\n"
                               f"最终大小: {size_kb:.2f} KB")
    
    def compression_failed(self, message):
        # 启用按钮
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Button) and widget["text"] != "退出":
                widget.state(['!disabled'])
        
        self.root.config(cursor="")
        messagebox.showerror("压缩失败", message)
    
    def open_output_dir(self):
        if self.output_path and os.path.exists(self.output_path):
            output_dir = os.path.dirname(self.output_path)
            os.startfile(output_dir)
        elif self.input_path:
            input_dir = os.path.dirname(self.input_path)
            os.startfile(input_dir)
        else:
            messagebox.showerror("错误", "没有可用的输出目录")

if __name__ == "__main__":
    root = tk.Tk()
    
    # 设置图标（如果存在）
    try:
        # 检测当前运行环境（打包后还是开发环境）
        if getattr(sys, 'frozen', False):
            # 打包后的可执行文件路径
            base_path = os.path.dirname(sys.executable)
        else:
            # 开发环境脚本路径
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # 尝试加载图标
        icon_path = os.path.join(base_path, "app_icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception as e:
        print(f"加载图标失败: {e}")
    
    app = ImageCompressorApp(root)
    root.mainloop()
