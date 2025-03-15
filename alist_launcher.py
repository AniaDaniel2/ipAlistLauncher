# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import os
import socket
import subprocess
import sys
from win10toast import ToastNotifier

# 常量配置
CONFIG_NAME = "alist_launcher_config.json"
DEFAULT_PORT = 5244
ICON_NAME = "app.ico"

class PathManager:
    @staticmethod
    def config_path():
        return os.path.join(os.path.expanduser('~'), CONFIG_NAME)
    
    @staticmethod
    def asset_path(filename):
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_dir, filename)

class AppConfig:
    def __init__(self):
        self.port = tk.StringVar(value=str(DEFAULT_PORT))
        self.process = None
        self.toaster = ToastNotifier()
        
    @property
    def current_port(self):
        try:
            return int(self.port.get())
        except ValueError:
            return DEFAULT_PORT

class NetworkService:
    @staticmethod
    def detect_ips():
        def get_ipv4():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    return s.getsockname()[0]
            except Exception:
                return None

        def get_ipv6():
            try:
                for res in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET6):
                    addr = res[4][0]
                    if addr != "::1" and not addr.startswith("fe80"):
                        return addr.split("%")[0]
            except Exception:
                return None

        return (get_ipv4(), get_ipv6())

class ConfigHandler:
    @staticmethod
    def load_config():
        config_file = PathManager.config_path()
        try:
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            messagebox.showerror("配置错误", f"配置文件读取失败:\n{str(e)}")
        return None

    @staticmethod
    def save_config(exe_path, port):
        config = {
            "path": os.path.abspath(exe_path),
            "port": int(port)
        }
        try:
            with open(PathManager.config_path(), "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("配置错误", f"配置保存失败:\n{str(e)}")
            return False

    @staticmethod
    def remove_config():
        try:
            os.remove(PathManager.config_path())
            return True
        except FileNotFoundError:
            return True
        except Exception as e:
            messagebox.showerror("配置错误", f"配置删除失败:\n{str(e)}")
            return False

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Alist 服务管理器")
        self.geometry("680x480")
        self.minsize(600, 400)
        self.config = AppConfig()
        self.style = ttk.Style()
        
        self._setup_ui()
        self._load_existing_config()
        self._bind_events()

    def _setup_ui(self):
        self._configure_styles()
        self._create_main_frame()
        self._create_port_setting()
        self._create_address_panel()
        self._create_action_buttons()
        self._set_window_icon()

    def _configure_styles(self):
        self.style.theme_use("clam")
        self.configure(bg="#F5F5F5")
        self.style.configure("TFrame", background="#F5F5F5")
        self.style.configure("TButton", 
                           foreground="white",
                           background="#2196F3",
                           padding=8,
                           font=("Microsoft YaHei", 10))
        self.style.map("TButton",
                     background=[("active", "#1976D2"), ("disabled", "#BBDEFB")])

    def _create_main_frame(self):
        self.main_frame = ttk.Frame(self, padding=(20, 15))
        self.main_frame.pack(expand=True, fill=tk.BOTH)
        self.main_frame.columnconfigure(0, weight=1)

    def _create_port_setting(self):
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=0, column=0, sticky="ew", pady=10)
        
        ttk.Label(frame, text="服务端口:").pack(side=tk.LEFT)
        ttk.Entry(frame, textvariable=self.config.port, width=10).pack(side=tk.LEFT, padx=10)
        ttk.Button(frame, text="保存设置", command=self._save_settings).pack(side=tk.RIGHT)

    def _create_address_panel(self):
        frame = ttk.LabelFrame(self.main_frame, text=" 访问地址 ", padding=15)
        frame.grid(row=1, column=0, sticky="nsew", pady=15)
        frame.columnconfigure(0, weight=1)

        ipv4, ipv6 = NetworkService.detect_ips()
        port = self.config.current_port

        self._add_address_row(frame, "IPv4 地址:", ipv4, port, 0)
        self._add_address_row(frame, "IPv6 地址:", ipv6, port, 1)

    def _add_address_row(self, parent, label, ip, port, row):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=0, sticky="ew", pady=8)
        
        ttk.Label(frame, text=label, width=10, anchor="w").pack(side=tk.LEFT)
        address = self._format_address(ip, port) if ip else "未检测到地址"
        ttk.Label(frame, text=address, font=("Consolas", 11)).pack(side=tk.LEFT, padx=10)
        ttk.Button(frame, text="复制", 
                 command=lambda: self._copy_to_clipboard(ip, port),
                 state="normal" if ip else "disabled").pack(side=tk.RIGHT)

    def _create_action_buttons(self):
        frame = ttk.Frame(self.main_frame)
        frame.grid(row=2, column=0, sticky="se", pady=20)
        
        ttk.Button(frame, text="🔄 重启服务", command=self._restart_service).pack(side=tk.LEFT, padx=8)
        ttk.Button(frame, text="📁 选择程序", command=self._change_program).pack(side=tk.LEFT, padx=8)
        ttk.Button(frame, text="⚙️ 重置配置", command=self._reset_config).pack(side=tk.LEFT, padx=8)
        ttk.Button(frame, text="❌ 退出", command=self.destroy).pack(side=tk.RIGHT)

    def _set_window_icon(self):
        try:
            self.iconbitmap(PathManager.asset_path(ICON_NAME))
        except Exception as e:
            print(f"图标加载失败: {str(e)}")

    def _bind_events(self):
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _load_existing_config(self):
        if cfg := ConfigHandler.load_config():
            self.config.port.set(str(cfg.get("port", DEFAULT_PORT)))
            self._start_alist_service(cfg["path"])

    def _save_settings(self):
        if not 1 <= self.config.current_port <= 65535:
            messagebox.showerror("错误", "端口号必须在1-65535之间")
            return False
        
        if path := filedialog.askopenfilename(
            title="选择Alist程序",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        ):
            if ConfigHandler.save_config(path, self.config.current_port):
                self._show_notification("配置更新", "新设置已保存")
                self._restart_service()
                return True
        return False

    def _start_alist_service(self, exe_path):
        if self.config.process:
            self.config.process.terminate()
        
        try:
            self.config.process = subprocess.Popen(
                [exe_path, "server", "--port", str(self.config.current_port)],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self._show_notification("服务启动", "Alist服务已开始运行")
        except Exception as e:
            messagebox.showerror("启动失败", f"无法启动程序:\n{str(e)}")

    def _restart_service(self):
        if cfg := ConfigHandler.load_config():
            self._start_alist_service(cfg["path"])

    def _change_program(self):
        if path := filedialog.askopenfilename(
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
        ):
            ConfigHandler.save_config(path, self.config.current_port)
            self._restart_service()

    def _reset_config(self):
        ConfigHandler.remove_config()
        self.config.port.set(str(DEFAULT_PORT))
        self._show_notification("配置重置", "已恢复默认设置")

    def _copy_to_clipboard(self, ip, port):
        self.clipboard_clear()
        self.clipboard_append(f"http://{ip}:{port}")
        self._show_notification("复制成功", "地址已复制到剪贴板")

    def _show_notification(self, title, message):
        try:
            self.config.toaster.show_toast(title, message, duration=3)
        except Exception as e:
            print(f"通知发送失败: {str(e)}")

    @staticmethod
    def _format_address(ip, port):
        return f"{ip}:{port}" if ":" not in ip else f"[{ip}]:{port}"

    def _on_close(self):
        if self.config.process:
            self.config.process.terminate()
        self.destroy()

if __name__ == "__main__":
    try:
        app = Application()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("致命错误", f"程序初始化失败:\n{str(e)}")