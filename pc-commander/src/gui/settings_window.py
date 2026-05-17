import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
from src.utils.config import load_config, save_config
from src.utils.startup import set_startup, is_startup_enabled
from src.security.auth import validate_telegram_token

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_VERSION = "1.0.0"
APP_NAME = "PC Commander"


class SettingsWindow(ctk.CTk):
    def __init__(self, on_start_callback=None, on_stop_callback=None):
        super().__init__()
        self.on_start_callback = on_start_callback
        self.on_stop_callback = on_stop_callback
        self.config = load_config()
        self.is_running = False

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("700x650")
        self.resizable(False, False)
        self.iconbitmap(default="") if sys.platform == "win32" else None

        self._build_ui()
        self._load_values()

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color="#1a1a2e")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)

        ctk.CTkLabel(
            header, text="🖥️  PC Commander",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#4fc3f7"
        ).pack(side="left", padx=20, pady=15)

        self.status_label = ctk.CTkLabel(
            header, text="⭕ متوقف",
            font=ctk.CTkFont(size=13),
            text_color="#ef5350"
        )
        self.status_label.pack(side="right", padx=20)

        ctk.CTkLabel(
            header, text=f"v{APP_VERSION}",
            font=ctk.CTkFont(size=11),
            text_color="#666"
        ).pack(side="right", padx=5)

        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=1, column=0, padx=15, pady=10, sticky="nsew")

        for tab in ["تيليغرام", "الذكاء الاصطناعي", "الاتصال", "الإعدادات", "المراقبة", "السجلات"]:
            self.tabview.add(tab)

        self._build_telegram_tab()
        self._build_ai_tab()
        self._build_tunnel_tab()
        self._build_settings_tab()
        self._build_monitoring_tab()
        self._build_logs_tab()

        btn_frame = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color="#0d0d1a")
        btn_frame.grid(row=2, column=0, sticky="ew")
        btn_frame.grid_propagate(False)

        self.start_btn = ctk.CTkButton(
            btn_frame, text="▶  تشغيل", width=140, height=38,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2e7d32", hover_color="#1b5e20",
            command=self._toggle_service
        )
        self.start_btn.pack(side="left", padx=20, pady=10)

        ctk.CTkButton(
            btn_frame, text="💾  حفظ الإعدادات", width=160, height=38,
            font=ctk.CTkFont(size=13),
            fg_color="#1565c0", hover_color="#0d47a1",
            command=self._save_settings
        ).pack(side="left", padx=5, pady=10)

        ctk.CTkButton(
            btn_frame, text="🗕  تصغير", width=100, height=38,
            font=ctk.CTkFont(size=13),
            fg_color="#424242", hover_color="#212121",
            command=self._minimize_to_tray
        ).pack(side="right", padx=20, pady=10)

    def _build_telegram_tab(self):
        tab = self.tabview.tab("تيليغرام")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="إعدادات بوت تيليغرام",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 5))

        frame = ctk.CTkFrame(tab)
        frame.pack(fill="x", padx=20, pady=5)
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="Bot Token:", width=130, anchor="w").grid(row=0, column=0, padx=10, pady=8)
        self.bot_token_var = ctk.StringVar()
        token_entry = ctk.CTkEntry(frame, textvariable=self.bot_token_var, show="•", width=350)
        token_entry.grid(row=0, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkButton(
            frame, text="تحقق", width=80,
            fg_color="#1565c0", hover_color="#0d47a1",
            command=self._verify_telegram
        ).grid(row=0, column=2, padx=10, pady=8)

        self.telegram_status = ctk.CTkLabel(frame, text="", text_color="#aaa")
        self.telegram_status.grid(row=1, column=0, columnspan=3, padx=10, pady=2)

        ctk.CTkLabel(frame, text="معرفاتك (User IDs):", width=130, anchor="w").grid(row=2, column=0, padx=10, pady=8)
        self.allowed_users_var = ctk.StringVar()
        ctk.CTkEntry(frame, textvariable=self.allowed_users_var, placeholder_text="123456789, 987654321").grid(
            row=2, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(
            tab,
            text="💡 للحصول على Bot Token: أرسل /newbot لـ @BotFather في تيليغرام\n"
                 "💡 للحصول على User ID: أرسل رسالة لـ @userinfobot",
            font=ctk.CTkFont(size=11), text_color="#888", justify="right"
        ).pack(pady=10)

    def _build_ai_tab(self):
        tab = self.tabview.tab("الذكاء الاصطناعي")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="إعدادات الذكاء الاصطناعي",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 5))

        provider_frame = ctk.CTkFrame(tab)
        provider_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(provider_frame, text="المزود:").pack(side="left", padx=15, pady=10)
        self.ai_provider_var = ctk.StringVar(value="openai")
        ctk.CTkRadioButton(provider_frame, text="OpenAI (ChatGPT)",
                           variable=self.ai_provider_var, value="openai",
                           command=self._on_ai_provider_change).pack(side="left", padx=10, pady=10)
        ctk.CTkRadioButton(provider_frame, text="Google Gemini",
                           variable=self.ai_provider_var, value="gemini",
                           command=self._on_ai_provider_change).pack(side="left", padx=10, pady=10)

        self.openai_frame = ctk.CTkFrame(tab)
        self.openai_frame.pack(fill="x", padx=20, pady=5)
        self.openai_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.openai_frame, text="OpenAI API Key:", width=140, anchor="w").grid(row=0, column=0, padx=10, pady=8)
        self.openai_key_var = ctk.StringVar()
        ctk.CTkEntry(self.openai_frame, textvariable=self.openai_key_var, show="•").grid(row=0, column=1, padx=10, pady=8, sticky="ew")
        ctk.CTkButton(self.openai_frame, text="تحقق", width=80,
                      fg_color="#1565c0", hover_color="#0d47a1",
                      command=lambda: self._verify_ai("openai")).grid(row=0, column=2, padx=10, pady=8)

        ctk.CTkLabel(self.openai_frame, text="النموذج:", width=140, anchor="w").grid(row=1, column=0, padx=10, pady=8)
        self.openai_model_var = ctk.StringVar(value="gpt-4o")
        ctk.CTkOptionMenu(self.openai_frame, variable=self.openai_model_var,
                          values=["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]).grid(row=1, column=1, padx=10, pady=8, sticky="w")

        self.gemini_frame = ctk.CTkFrame(tab)
        self.gemini_frame.pack(fill="x", padx=20, pady=5)
        self.gemini_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.gemini_frame, text="Gemini API Key:", width=140, anchor="w").grid(row=0, column=0, padx=10, pady=8)
        self.gemini_key_var = ctk.StringVar()
        ctk.CTkEntry(self.gemini_frame, textvariable=self.gemini_key_var, show="•").grid(row=0, column=1, padx=10, pady=8, sticky="ew")
        ctk.CTkButton(self.gemini_frame, text="تحقق", width=80,
                      fg_color="#1565c0", hover_color="#0d47a1",
                      command=lambda: self._verify_ai("gemini")).grid(row=0, column=2, padx=10, pady=8)

        ctk.CTkLabel(self.gemini_frame, text="النموذج:", width=140, anchor="w").grid(row=1, column=0, padx=10, pady=8)
        self.gemini_model_var = ctk.StringVar(value="gemini-pro")
        ctk.CTkOptionMenu(self.gemini_frame, variable=self.gemini_model_var,
                          values=["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"]).grid(row=1, column=1, padx=10, pady=8, sticky="w")

        self.ai_status = ctk.CTkLabel(tab, text="", text_color="#aaa")
        self.ai_status.pack(pady=5)

        ctk.CTkLabel(
            tab,
            text="💡 OpenAI: platform.openai.com  |  Gemini: makersuite.google.com",
            font=ctk.CTkFont(size=11), text_color="#888"
        ).pack(pady=5)

    def _build_tunnel_tab(self):
        tab = self.tabview.tab("الاتصال")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="إعدادات الاتصال عن بُعد",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 5))

        provider_frame = ctk.CTkFrame(tab)
        provider_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(provider_frame, text="طريقة الاتصال:").pack(side="left", padx=15, pady=10)
        self.tunnel_provider_var = ctk.StringVar(value="cloudflare")
        ctk.CTkRadioButton(provider_frame, text="Cloudflare Tunnel (مجاني)",
                           variable=self.tunnel_provider_var, value="cloudflare",
                           command=self._on_tunnel_change).pack(side="left", padx=10, pady=10)
        ctk.CTkRadioButton(provider_frame, text="ngrok",
                           variable=self.tunnel_provider_var, value="ngrok",
                           command=self._on_tunnel_change).pack(side="left", padx=10, pady=10)

        self.cloudflare_frame = ctk.CTkFrame(tab)
        self.cloudflare_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(
            self.cloudflare_frame,
            text="✅ Cloudflare Tunnel مجاني بالكامل ولا يحتاج حساب!\n"
                 "سيتم تحميل cloudflared تلقائياً إذا لم يكن مثبتاً.",
            font=ctk.CTkFont(size=12), text_color="#81c784", justify="left"
        ).pack(padx=15, pady=10)

        self.ngrok_frame = ctk.CTkFrame(tab)
        self.ngrok_frame.pack(fill="x", padx=20, pady=5)
        self.ngrok_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.ngrok_frame, text="ngrok Auth Token:", width=140, anchor="w").grid(row=0, column=0, padx=10, pady=8)
        self.ngrok_token_var = ctk.StringVar()
        ctk.CTkEntry(self.ngrok_frame, textvariable=self.ngrok_token_var, show="•").grid(row=0, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(
            self.ngrok_frame,
            text="💡 احصل على Token من: dashboard.ngrok.com",
            font=ctk.CTkFont(size=11), text_color="#888"
        ).grid(row=1, column=0, columnspan=3, padx=10, pady=2)

        anydesk_frame = ctk.CTkFrame(tab)
        anydesk_frame.pack(fill="x", padx=20, pady=10)
        anydesk_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(anydesk_frame, text="⚙️ إعدادات AnyDesk",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, columnspan=3, padx=10, pady=8)

        ctk.CTkLabel(anydesk_frame, text="مسار AnyDesk:", width=140, anchor="w").grid(row=1, column=0, padx=10, pady=5)
        self.anydesk_path_var = ctk.StringVar()
        ctk.CTkEntry(anydesk_frame, textvariable=self.anydesk_path_var).grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkButton(anydesk_frame, text="تصفح", width=70,
                      command=self._browse_anydesk).grid(row=1, column=2, padx=10, pady=5)

    def _build_settings_tab(self):
        tab = self.tabview.tab("الإعدادات")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="الإعدادات العامة",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 5))

        frame = ctk.CTkFrame(tab)
        frame.pack(fill="x", padx=20, pady=5)

        self.startup_var = ctk.BooleanVar()
        ctk.CTkCheckBox(
            frame, text="التشغيل التلقائي مع بدء ويندوز",
            variable=self.startup_var, font=ctk.CTkFont(size=13)
        ).pack(padx=15, pady=10, anchor="w")

        self.dnd_var = ctk.BooleanVar()
        ctk.CTkCheckBox(
            frame, text="وضع عدم الإزعاج (إيقاف التنفيذ مؤقتاً)",
            variable=self.dnd_var, font=ctk.CTkFont(size=13)
        ).pack(padx=15, pady=5, anchor="w")

        self.log_commands_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            frame, text="تسجيل جميع الأوامر المنفذة",
            variable=self.log_commands_var, font=ctk.CTkFont(size=13)
        ).pack(padx=15, pady=5, anchor="w")

        self.notify_unauth_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            frame, text="إشعار عند محاولة وصول غير مصرح",
            variable=self.notify_unauth_var, font=ctk.CTkFont(size=13)
        ).pack(padx=15, pady=5, anchor="w")

        self.daily_report_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            frame, text="إرسال تقرير يومي تلقائي",
            variable=self.daily_report_var, font=ctk.CTkFont(size=13)
        ).pack(padx=15, pady=5, anchor="w")

        time_frame = ctk.CTkFrame(tab)
        time_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(time_frame, text="وقت التقرير اليومي:", width=160, anchor="w").pack(side="left", padx=15, pady=10)
        self.report_time_var = ctk.StringVar(value="08:00")
        ctk.CTkEntry(time_frame, textvariable=self.report_time_var, width=100,
                     placeholder_text="HH:MM").pack(side="left", padx=10)

    def _build_monitoring_tab(self):
        tab = self.tabview.tab("المراقبة")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="حدود التنبيهات",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 5))

        frame = ctk.CTkFrame(tab)
        frame.pack(fill="x", padx=20, pady=5)
        frame.grid_columnconfigure(1, weight=1)

        monitors = [
            ("حد المعالج (CPU %):", "cpu_alert", 90),
            ("حد الذاكرة (RAM %):", "ram_alert", 90),
            ("حد القرص (Disk %):", "disk_alert", 90),
            ("حد الحرارة (°C):", "temp_alert", 80),
        ]

        self.monitor_vars = {}
        for i, (label, key, default) in enumerate(monitors):
            ctk.CTkLabel(frame, text=label, width=180, anchor="w").grid(row=i, column=0, padx=15, pady=8)
            var = ctk.IntVar(value=default)
            self.monitor_vars[key] = var
            slider = ctk.CTkSlider(frame, from_=50, to=100, variable=var, width=250)
            slider.grid(row=i, column=1, padx=10, pady=8, sticky="ew")
            ctk.CTkLabel(frame, textvariable=var, width=40).grid(row=i, column=2, padx=10, pady=8)

    def _build_logs_tab(self):
        tab = self.tabview.tab("السجلات")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        btn_frame = ctk.CTkFrame(tab)
        btn_frame.pack(fill="x", padx=20, pady=10)

        ctk.CTkButton(btn_frame, text="🔄 تحديث", width=100,
                      command=self._refresh_logs).pack(side="left", padx=10, pady=8)
        ctk.CTkButton(btn_frame, text="🗑️ مسح", width=100,
                      fg_color="#c62828", hover_color="#b71c1c",
                      command=self._clear_logs).pack(side="left", padx=5, pady=8)
        ctk.CTkButton(btn_frame, text="📁 فتح مجلد السجلات", width=160,
                      command=self._open_logs_folder).pack(side="left", padx=5, pady=8)

        self.log_textbox = ctk.CTkTextbox(tab, font=ctk.CTkFont(size=11, family="Consolas"))
        self.log_textbox.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self._refresh_logs()

    def _load_values(self):
        cfg = self.config
        self.bot_token_var.set(cfg["telegram"].get("bot_token", ""))
        self.allowed_users_var.set(", ".join(str(u) for u in cfg["telegram"].get("allowed_users", [])))
        self.ai_provider_var.set(cfg["ai"].get("provider", "openai"))
        self.openai_key_var.set(cfg["ai"].get("openai_key", ""))
        self.gemini_key_var.set(cfg["ai"].get("gemini_key", ""))
        self.openai_model_var.set(cfg["ai"].get("model_openai", "gpt-4o"))
        self.gemini_model_var.set(cfg["ai"].get("model_gemini", "gemini-pro"))
        self.tunnel_provider_var.set(cfg["tunnel"].get("provider", "cloudflare"))
        self.ngrok_token_var.set(cfg["tunnel"].get("ngrok_token", ""))
        self.anydesk_path_var.set(cfg["anydesk"].get("path", ""))
        self.startup_var.set(is_startup_enabled())
        self.dnd_var.set(cfg["general"].get("do_not_disturb", False))
        self.log_commands_var.set(cfg["security"].get("log_commands", True))
        self.notify_unauth_var.set(cfg["security"].get("notify_on_unauthorized", True))
        self.daily_report_var.set(cfg["general"].get("daily_report_enabled", True))
        self.report_time_var.set(cfg["general"].get("daily_report_time", "08:00"))
        mon = cfg.get("monitoring", {})
        self.monitor_vars["cpu_alert"].set(mon.get("cpu_alert_threshold", 90))
        self.monitor_vars["ram_alert"].set(mon.get("ram_alert_threshold", 90))
        self.monitor_vars["disk_alert"].set(mon.get("disk_alert_threshold", 90))
        self.monitor_vars["temp_alert"].set(mon.get("temp_alert_threshold", 80))
        self._on_ai_provider_change()
        self._on_tunnel_change()

    def _save_settings(self):
        users_raw = self.allowed_users_var.get().strip()
        allowed = [u.strip() for u in users_raw.split(",") if u.strip().isdigit()]

        self.config["telegram"]["bot_token"] = self.bot_token_var.get().strip()
        self.config["telegram"]["allowed_users"] = allowed
        self.config["ai"]["provider"] = self.ai_provider_var.get()
        self.config["ai"]["openai_key"] = self.openai_key_var.get().strip()
        self.config["ai"]["gemini_key"] = self.gemini_key_var.get().strip()
        self.config["ai"]["model_openai"] = self.openai_model_var.get()
        self.config["ai"]["model_gemini"] = self.gemini_model_var.get()
        self.config["tunnel"]["provider"] = self.tunnel_provider_var.get()
        self.config["tunnel"]["ngrok_token"] = self.ngrok_token_var.get().strip()
        self.config["anydesk"]["path"] = self.anydesk_path_var.get().strip()
        self.config["general"]["do_not_disturb"] = self.dnd_var.get()
        self.config["general"]["daily_report_enabled"] = self.daily_report_var.get()
        self.config["general"]["daily_report_time"] = self.report_time_var.get().strip()
        self.config["security"]["log_commands"] = self.log_commands_var.get()
        self.config["security"]["notify_on_unauthorized"] = self.notify_unauth_var.get()
        self.config["monitoring"]["cpu_alert_threshold"] = self.monitor_vars["cpu_alert"].get()
        self.config["monitoring"]["ram_alert_threshold"] = self.monitor_vars["ram_alert"].get()
        self.config["monitoring"]["disk_alert_threshold"] = self.monitor_vars["disk_alert"].get()
        self.config["monitoring"]["temp_alert_threshold"] = self.monitor_vars["temp_alert"].get()

        save_config(self.config)
        set_startup(self.startup_var.get())

        messagebox.showinfo("تم", "✅ تم حفظ الإعدادات بنجاح!")

    def _toggle_service(self):
        if not self.is_running:
            self._start_service()
        else:
            self._stop_service()

    def _start_service(self):
        self._save_settings()
        if not self.config["telegram"].get("bot_token"):
            messagebox.showerror("خطأ", "يرجى إدخال Bot Token أولاً")
            return

        provider = self.config["ai"].get("provider", "openai")
        if provider == "openai" and not self.config["ai"].get("openai_key"):
            messagebox.showerror("خطأ", "يرجى إدخال OpenAI API Key")
            return
        if provider == "gemini" and not self.config["ai"].get("gemini_key"):
            messagebox.showerror("خطأ", "يرجى إدخال Gemini API Key")
            return

        if self.on_start_callback:
            try:
                self.on_start_callback(self.config)
                self.is_running = True
                self.start_btn.configure(text="⏹  إيقاف", fg_color="#c62828", hover_color="#b71c1c")
                self.status_label.configure(text="🟢 يعمل", text_color="#66bb6a")
            except Exception as e:
                messagebox.showerror("خطأ", f"فشل التشغيل:\n{e}")

    def _stop_service(self):
        if self.on_stop_callback:
            self.on_stop_callback()
        self.is_running = False
        self.start_btn.configure(text="▶  تشغيل", fg_color="#2e7d32", hover_color="#1b5e20")
        self.status_label.configure(text="⭕ متوقف", text_color="#ef5350")

    def _verify_telegram(self):
        token = self.bot_token_var.get().strip()
        if not token:
            self.telegram_status.configure(text="⚠️ أدخل الـ Token أولاً", text_color="#ffb300")
            return
        self.telegram_status.configure(text="⏳ جاري التحقق...", text_color="#aaa")
        self.update()

        def check():
            result = validate_telegram_token(token)
            if result["valid"]:
                self.telegram_status.configure(
                    text=f"✅ صالح - البوت: {result['bot_name']} (@{result['username']})",
                    text_color="#66bb6a"
                )
            else:
                self.telegram_status.configure(
                    text=f"❌ {result.get('error', 'غير صالح')}",
                    text_color="#ef5350"
                )

        threading.Thread(target=check, daemon=True).start()

    def _verify_ai(self, provider: str):
        def check():
            try:
                if provider == "openai":
                    from src.ai.openai_handler import OpenAIHandler
                    key = self.openai_key_var.get().strip()
                    handler = OpenAIHandler(key)
                    valid = handler.verify_key()
                else:
                    from src.ai.gemini_handler import GeminiHandler
                    key = self.gemini_key_var.get().strip()
                    handler = GeminiHandler(key)
                    valid = handler.verify_key()

                self.ai_status.configure(
                    text=f"✅ مفتاح {provider} صالح" if valid else f"❌ مفتاح {provider} غير صالح",
                    text_color="#66bb6a" if valid else "#ef5350"
                )
            except Exception as e:
                self.ai_status.configure(text=f"❌ خطأ: {e}", text_color="#ef5350")

        self.ai_status.configure(text="⏳ جاري التحقق...", text_color="#aaa")
        threading.Thread(target=check, daemon=True).start()

    def _on_ai_provider_change(self):
        pass

    def _on_tunnel_change(self):
        pass

    def _browse_anydesk(self):
        path = filedialog.askopenfilename(
            title="اختر ملف AnyDesk",
            filetypes=[("Executable", "*.exe"), ("All", "*.*")]
        )
        if path:
            self.anydesk_path_var.set(path)

    def _refresh_logs(self):
        from src.utils.config import get_logs_dir
        logs_dir = get_logs_dir()
        self.log_textbox.delete("1.0", "end")
        try:
            from datetime import datetime
            log_file = logs_dir / f"commander_{datetime.now().strftime('%Y%m%d')}.log"
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    content = f.read()
                self.log_textbox.insert("end", content or "لا توجد سجلات اليوم")
            else:
                self.log_textbox.insert("end", "لا توجد سجلات اليوم")
        except Exception as e:
            self.log_textbox.insert("end", f"خطأ في قراءة السجلات: {e}")

    def _clear_logs(self):
        if messagebox.askyesno("تأكيد", "هل تريد مسح جميع السجلات؟"):
            self.log_textbox.delete("1.0", "end")

    def _open_logs_folder(self):
        from src.utils.config import get_logs_dir
        import os
        if sys.platform == "win32":
            os.startfile(str(get_logs_dir()))

    def _minimize_to_tray(self):
        self.withdraw()

    def set_running_status(self, running: bool):
        self.is_running = running
        if running:
            self.start_btn.configure(text="⏹  إيقاف", fg_color="#c62828", hover_color="#b71c1c")
            self.status_label.configure(text="🟢 يعمل", text_color="#66bb6a")
        else:
            self.start_btn.configure(text="▶  تشغيل", fg_color="#2e7d32", hover_color="#1b5e20")
            self.status_label.configure(text="⭕ متوقف", text_color="#ef5350")
