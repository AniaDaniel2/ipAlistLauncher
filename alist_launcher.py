# alist_launcher.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import socket
import pyperclip
import subprocess
from ttkthemes import ThemedTk

# 配置参数
CONFIG_PATH = os.path.join(os.path.expanduser('~'), 'alist_launcher_config.json')
ICON_PATH = 'alist.ico'
WIN11_FONT = ("Segoe UI Variable", 10)
WIN11_BG = "#f3f3f3"

def get_ips():
    """获取本机IPv4和IPv6地址"""
    ipv4 = ipv6 = None
    
    # 获取IPv4
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 80))
            ipv4 = s.getsockname()[0]
    except Exception as e:
        print(f"IPv4获取失败: {e}")

    # 获取IPv6
    try:
        for res in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET6):
            addr = res[4][0]
            if addr != '::1' and not addr.startswith('fe80'):
                ipv6 = addr.split('%')[0]
                break
    except Exception as e:
        print(f"IPv6获取失败: {e}")

    return ipv4, ipv6

def load_config():
    """加载配置文件"""
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, 'r') as f:
                config = json.load(f)
                if 'path' in config and os.path.exists(config['path']):
                    return config
            os.remove(CONFIG_PATH)
    except Exception as e:
        print(f"配置加载错误: {e}")
    return None

def save_config(path):
    """保存配置文件"""
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump({'path': os.path.abspath(path)}, f)
        return True
    except Exception as e:
        messagebox.showerror("配置错误", f"保存失败: {e}")
        return False

def setup_styles():
    """设置Windows 11风格"""
    style = ttk.Style()
    style.theme_use('vista')
    
    style.configure('Alist.TButton', 
                   font=WIN11_FONT,
                   background='#0078d4',
                   foreground='black',
                   bordercolor='#0078d4',
                   padding=(12, 4))
    
    style.map('Alist.TButton',
             background=[('active', '#006cbd'), ('disabled', '#f3f3f3')],
             bordercolor=[('active', '#006cbd'), ('disabled', '#f3f3f3')])

def create_ui(root):
    """创建主界面"""
    main_frame = ttk.Frame(root)
    main_frame.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    # IP地址显示
    ip_frame = ttk.LabelFrame(main_frame, text=" 网络地址 ", padding=(15, 10))
    ip_frame.pack(fill=tk.X, pady=10)

    ipv4, ipv6 = get_ips()

    # IPv4行
    ipv4_row = ttk.Frame(ip_frame)
    ipv4_row.pack(fill=tk.X, pady=5)
    ttk.Label(ipv4_row, text="IPv4:", width=6, anchor=tk.W).pack(side=tk.LEFT)
    ttk.Label(ipv4_row, text=f"{ipv4}:5244" if ipv4 else "未找到地址").pack(side=tk.LEFT, expand=True)
    ttk.Button(ipv4_row, text="复制", style='Alist.TButton',
              command=lambda: copy_address(ipv4, 'IPv4', False)).pack(side=tk.RIGHT)

    # IPv6行
    ipv6_row = ttk.Frame(ip_frame)
    ipv6_row.pack(fill=tk.X, pady=5)
    ttk.Label(ipv6_row, text="IPv6:", width=6, anchor=tk.W).pack(side=tk.LEFT)
    ttk.Label(ipv6_row, text=f"[{ipv6}]:5244" if ipv6 else "未找到地址").pack(side=tk.LEFT, expand=True)
    ttk.Button(ipv6_row, text="复制", style='Alist.TButton',
              command=lambda: copy_address(ipv6, 'IPv6', True)).pack(side=tk.RIGHT)

    # 底部按钮
    btn_frame = ttk.Frame(main_frame)
    btn_frame.pack(fill=tk.X, pady=10)
    
    ttk.Button(btn_frame, text="重新选择", style='Alist.TButton',
              command=lambda: reset_config(root)).pack(side=tk.RIGHT, padx=5)
    ttk.Button(btn_frame, text="退出", style='Alist.TButton',
              command=root.destroy).pack(side=tk.RIGHT)

def copy_address(ip, ip_type, is_v6):
    """处理复制操作"""
    if ip:
        addr = f"[{ip}]:5244" if is_v6 else f"{ip}:5244"
        pyperclip.copy(addr)
        messagebox.showinfo("成功", f"已复制{ip_type}地址")
    else:
        messagebox.showerror("错误", f"未找到{ip_type}地址")

def reset_config(root):
    """重置配置"""
    if messagebox.askyesno("确认", "是否要重置程序路径？"):
        try:
            os.remove(CONFIG_PATH)
            root.destroy()
            main()
        except Exception as e:
            messagebox.showerror("错误", f"重置失败: {e}")

def main():
    # 初始化窗口
    root = ThemedTk(theme="vista")
    root.title("Alist启动器 beta0.1")
    root.configure(bg=WIN11_BG)
    
    # 设置图标
    try:
        root.iconbitmap(ICON_PATH)
    except:
        try:
            root.iconbitmap(default=ICON_PATH)
        except:
            pass
    
    # 高DPI适配
    if os.name == 'nt':
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    
    # 窗口设置
    root.minsize(400, 220)
    root.geometry("480x260")
    setup_styles()

    # 配置检查
    config = load_config()
    if not config:
        root.withdraw()
        path = filedialog.askopenfilename(
            title="选择Alist helper程序",
            filetypes=[("Alist helper程序", "AlistHelper*.exe"), ("可执行文件", "*.exe")]
        )
        if path and save_config(path):
            try:
                subprocess.Popen(f'"{path}"', shell=True)
            except Exception as e:
                messagebox.showerror("错误", f"启动失败: {e}")
        root.destroy()
        return

    # 启动程序
    try:
        subprocess.Popen(f'"{config["path"]}"', shell=True)
    except Exception as e:
        messagebox.showerror("错误", f"启动失败: {e}")
        os.remove(CONFIG_PATH)
        root.destroy()
        main()
        return

    # 显示UI
    create_ui(root)
    root.mainloop()

if __name__ == "__main__":
    main()