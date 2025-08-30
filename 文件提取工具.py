import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class FileExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文件夹文件提取工具")
        self.root.geometry("600x400")
        
        # 创建界面元素
        self.create_widgets()
        
    def create_widgets(self):
        # 标题
        title_label = tk.Label(self.root, text="文件夹文件提取工具", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # 说明文本
        desc_text = """
        此工具可以将选定文件夹中的所有子文件（包括嵌套子文件夹中的文件）
        提取到当前目录中，并自动删除所有空的文件夹。
        
        使用方法：
        1. 点击"选择文件夹"按钮选择要处理的目录
        2. 点击"开始处理"按钮执行文件提取
        3. 处理完成后会显示处理结果
        """
        desc_label = tk.Label(self.root, text=desc_text, justify=tk.LEFT)
        desc_label.pack(pady=10, padx=20)
        
        # 选择文件夹区域
        folder_frame = tk.Frame(self.root)
        folder_frame.pack(pady=10, fill=tk.X, padx=20)
        
        tk.Label(folder_frame, text="目标文件夹:").pack(side=tk.LEFT)
        self.folder_path = tk.StringVar()
        folder_entry = tk.Entry(folder_frame, textvariable=self.folder_path, width=50)
        folder_entry.pack(side=tk.LEFT, padx=5)
        
        browse_btn = tk.Button(folder_frame, text="浏览", command=self.browse_folder)
        browse_btn.pack(side=tk.LEFT)
        
        # 进度条
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        self.progress.pack(pady=10, fill=tk.X, padx=20)
        
        # 日志区域
        tk.Label(self.root, text="操作日志:").pack(anchor=tk.W, padx=20)
        self.log_text = tk.Text(self.root, height=10)
        self.log_text.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # 按钮区域
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.process_btn = tk.Button(button_frame, text="开始处理", command=self.process_files)
        self.process_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = tk.Button(button_frame, text="清空日志", command=self.clear_log)
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        self.quit_btn = tk.Button(button_frame, text="退出", command=self.root.quit)
        self.quit_btn.pack(side=tk.LEFT, padx=5)
    
    def browse_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path.set(folder_selected)
    
    def log_message(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
    
    def process_files(self):
        target_dir = self.folder_path.get()
        if not target_dir or not os.path.exists(target_dir):
            messagebox.showerror("错误", "请选择有效的文件夹路径！")
            return
        
        self.process_btn.config(state=tk.DISABLED)
        self.progress.start()
        self.log_message("开始处理文件夹: " + target_dir)
        
        try:
            # 收集所有文件并移动到目标目录
            moved_files = self.move_files_to_root(target_dir)
            
            # 删除空文件夹
            removed_dirs = self.remove_empty_folders(target_dir)
            
            # 显示结果
            self.log_message(f"处理完成！移动了 {moved_files} 个文件，删除了 {removed_dirs} 个空文件夹。")
            messagebox.showinfo("完成", f"处理完成！\n移动了 {moved_files} 个文件\n删除了 {removed_dirs} 个空文件夹")
            
        except Exception as e:
            self.log_message(f"处理过程中发生错误: {str(e)}")
            messagebox.showerror("错误", f"处理过程中发生错误: {str(e)}")
        finally:
            self.progress.stop()
            self.process_btn.config(state=tk.NORMAL)
    
    def move_files_to_root(self, root_dir):
        count = 0
        for foldername, subfolders, filenames in os.walk(root_dir):
            # 跳过根目录本身
            if foldername == root_dir:
                continue
                
            for filename in filenames:
                src_path = os.path.join(foldername, filename)
                dest_path = os.path.join(root_dir, filename)
                
                # 处理文件名冲突
                base, ext = os.path.splitext(filename)
                counter = 1
                while os.path.exists(dest_path):
                    new_filename = f"{base}_{counter}{ext}"
                    dest_path = os.path.join(root_dir, new_filename)
                    counter += 1
                
                # 移动文件
                shutil.move(src_path, dest_path)
                self.log_message(f"移动文件: {filename} -> {os.path.basename(dest_path)}")
                count += 1
                
        return count
    
    def remove_empty_folders(self, root_dir):
        count = 0
        # 从最深层的文件夹开始删除
        for foldername, subfolders, filenames in os.walk(root_dir, topdown=False):
            # 跳过根目录
            if foldername == root_dir:
                continue
                
            # 如果文件夹为空，删除它
            if not os.listdir(foldername):
                os.rmdir(foldername)
                self.log_message(f"删除空文件夹: {os.path.basename(foldername)}")
                count += 1
                
        return count

if __name__ == "__main__":
    root = tk.Tk()
    app = FileExtractorApp(root)
    root.mainloop()
