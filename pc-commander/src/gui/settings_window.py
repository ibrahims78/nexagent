import sys
import threading
from tkinter import messagebox, filedialog
import customtkinter as ctk
from src.utils.config import load_config, save_config
from src.utils.startup import set_startup, is_startup_enabled
from src.utils.security_auth import validate_telegram_token

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

APP_VERSION = "1.3.0"
APP_NAME = "NexAgent"


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

        for tab in ["تيليغرام", "الذكاء الاصطناعي", "الاتصال", "إيقاظ الحاسب", "تسجيل الدخول", "الإعدادات", "المراقبة", "السجلات"]:
            self.tabview.add(tab)

        self._build_telegram_tab()
        self._build_ai_tab()
        self._build_tunnel_tab()
        self._build_wol_tab()
        self._build_login_tab()
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
        self.gemini_model_var = ctk.StringVar(value="gemini-2.5-flash-preview-05-20")
        ctk.CTkOptionMenu(self.gemini_frame, variable=self.gemini_model_var,
                          values=["gemini-2.5-flash-preview-05-20", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]).grid(row=1, column=1, padx=10, pady=8, sticky="w")

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

        ctk.CTkLabel(provider_frame, text="النفق الرئيسي:").pack(side="left", padx=15, pady=10)
        self.tunnel_provider_var = ctk.StringVar(value="cloudflare")
        ctk.CTkRadioButton(provider_frame, text="Cloudflare (مجاني)",
                           variable=self.tunnel_provider_var, value="cloudflare",
                           command=self._on_tunnel_change).pack(side="left", padx=8, pady=10)
        ctk.CTkRadioButton(provider_frame, text="ngrok",
                           variable=self.tunnel_provider_var, value="ngrok",
                           command=self._on_tunnel_change).pack(side="left", padx=8, pady=10)
        ctk.CTkRadioButton(provider_frame, text="Tailscale",
                           variable=self.tunnel_provider_var, value="tailscale",
                           command=self._on_tunnel_change).pack(side="left", padx=8, pady=10)

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

        lan_frame = ctk.CTkFrame(tab)
        lan_frame.pack(fill="x", padx=20, pady=5)
        lan_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            lan_frame, text="🏠  الوصول من الشبكة المحلية (LAN)",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 2), sticky="w")

        ctk.CTkLabel(
            lan_frame,
            text="يسمح للأجهزة في نفس الشبكة بالوصول لـ HTTP API مباشرة بدون إنترنت",
            font=ctk.CTkFont(size=11), text_color="#888"
        ).grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 6), sticky="w")

        self.lan_access_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(
            lan_frame,
            text="السماح بالوصول من الشبكة المحلية",
            variable=self.lan_access_var,
            font=ctk.CTkFont(size=12)
        ).grid(row=2, column=0, columnspan=2, padx=15, pady=(0, 10), sticky="w")

        webhook_frame = ctk.CTkFrame(tab)
        webhook_frame.pack(fill="x", padx=20, pady=5)
        webhook_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            webhook_frame, text="⚡  وضع Webhook (أسرع من Polling)",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 2), sticky="w")

        ctk.CTkLabel(
            webhook_frame,
            text="يحتاج URL ثابتاً من النفق — يُفعَّل تلقائياً عند توفر النفق",
            font=ctk.CTkFont(size=11), text_color="#888"
        ).grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 6), sticky="w")

        self.use_webhook_var = ctk.BooleanVar(value=False)
        ctk.CTkSwitch(
            webhook_frame,
            text="تفعيل وضع Webhook",
            variable=self.use_webhook_var,
            font=ctk.CTkFont(size=12)
        ).grid(row=2, column=0, columnspan=2, padx=15, pady=(0, 6), sticky="w")

        ctk.CTkLabel(webhook_frame, text="Webhook URL:", width=120, anchor="w").grid(row=3, column=0, padx=10, pady=6)
        self.webhook_url_var = ctk.StringVar()
        ctk.CTkEntry(
            webhook_frame, textvariable=self.webhook_url_var,
            placeholder_text="https://abc123.trycloudflare.com (يُملأ تلقائياً)"
        ).grid(row=3, column=1, padx=10, pady=6, sticky="ew")

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

        self.watchdog_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            frame, text="🐕 Watchdog - مراقبة البوت وإعادة تشغيله تلقائياً",
            variable=self.watchdog_var, font=ctk.CTkFont(size=13)
        ).pack(padx=15, pady=5, anchor="w")

        time_frame = ctk.CTkFrame(tab)
        time_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(time_frame, text="وقت التقرير اليومي:", width=160, anchor="w").pack(side="left", padx=15, pady=10)
        self.report_time_var = ctk.StringVar(value="08:00")
        ctk.CTkEntry(time_frame, textvariable=self.report_time_var, width=100,
                     placeholder_text="HH:MM").pack(side="left", padx=10)

        sec_frame = ctk.CTkFrame(tab)
        sec_frame.pack(fill="x", padx=20, pady=10)
        sec_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            sec_frame, text="🔒  أمان الجلسة (PIN)",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 4), sticky="w")
        ctk.CTkLabel(
            sec_frame,
            text="يطلب رمزاً سرياً من كل مستخدم عند بدء كل جلسة - طبقة حماية إضافية",
            font=ctk.CTkFont(size=11), text_color="#888"
        ).grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 8), sticky="w")

        self.require_pin_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            sec_frame, text="تفعيل طلب PIN عند كل جلسة جديدة",
            variable=self.require_pin_var, font=ctk.CTkFont(size=12)
        ).grid(row=2, column=0, columnspan=3, padx=15, pady=5, sticky="w")

        ctk.CTkLabel(sec_frame, text="رمز PIN:", width=120, anchor="w").grid(row=3, column=0, padx=10, pady=6)
        self.session_pin_var = ctk.StringVar()
        ctk.CTkEntry(sec_frame, textvariable=self.session_pin_var,
                     show="●", placeholder_text="رمز سري (4-8 أرقام)").grid(row=3, column=1, padx=10, pady=6, sticky="ew")
        ctk.CTkLabel(
            sec_frame,
            text="💡 ينتهي بعد 60 دقيقة خمول  •  3 محاولات خاطئة = حجب تلقائي",
            font=ctk.CTkFont(size=10), text_color="#666"
        ).grid(row=4, column=0, columnspan=3, padx=10, pady=(0, 8), sticky="w")

    def _build_wol_tab(self):
        tab = self.tabview.tab("إيقاظ الحاسب")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="إيقاظ الحاسب عن بُعد (Wake-on-LAN)",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 5))

        ctk.CTkLabel(
            tab,
            text="يتيح تشغيل حاسبك حتى وهو مطفأ عبر تيليغرام",
            font=ctk.CTkFont(size=11), text_color="#888"
        ).pack(pady=(0, 10))

        frame = ctk.CTkFrame(tab)
        frame.pack(fill="x", padx=20, pady=5)
        frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="MAC Address الحاسب:", width=170, anchor="w").grid(row=0, column=0, padx=10, pady=8)
        self.wol_mac_var = ctk.StringVar()
        ctk.CTkEntry(frame, textvariable=self.wol_mac_var,
                     placeholder_text="A1:B2:C3:D4:E5:F6").grid(row=0, column=1, padx=10, pady=8, sticky="ew")
        ctk.CTkButton(frame, text="اكتشف", width=80,
                      fg_color="#1565c0", hover_color="#0d47a1",
                      command=self._detect_mac).grid(row=0, column=2, padx=10, pady=8)

        ctk.CTkLabel(frame, text="IP الحاسب:", width=170, anchor="w").grid(row=1, column=0, padx=10, pady=8)
        self.wol_ip_var = ctk.StringVar()
        ctk.CTkEntry(frame, textvariable=self.wol_ip_var,
                     placeholder_text="192.168.1.100").grid(row=1, column=1, padx=10, pady=8, sticky="ew")

        ctk.CTkLabel(frame, text="Broadcast IP:", width=170, anchor="w").grid(row=2, column=0, padx=10, pady=8)
        self.wol_broadcast_var = ctk.StringVar(value="255.255.255.255")
        ctk.CTkEntry(frame, textvariable=self.wol_broadcast_var,
                     placeholder_text="192.168.1.255").grid(row=2, column=1, padx=10, pady=8, sticky="ew")

        backup_frame = ctk.CTkFrame(tab)
        backup_frame.pack(fill="x", padx=20, pady=10)
        backup_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(backup_frame, text="📱 المستخدمون الاحتياطيون",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, columnspan=3, padx=10, pady=8)

        ctk.CTkLabel(backup_frame, text="User IDs الاحتياطيين:", width=170, anchor="w").grid(row=1, column=0, padx=10, pady=8)
        self.wol_backup_users_var = ctk.StringVar()
        ctk.CTkEntry(backup_frame, textvariable=self.wol_backup_users_var,
                     placeholder_text="123456789, 987654321").grid(row=1, column=1, padx=10, pady=8, sticky="ew")

        self.wol_auto_notify_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            backup_frame,
            text="إرسال إشعار تلقائي للاحتياطي عند فشل الإيقاظ",
            variable=self.wol_auto_notify_var,
            font=ctk.CTkFont(size=12)
        ).grid(row=2, column=0, columnspan=3, padx=15, pady=5, sticky="w")

        self.wol_monitor_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            backup_frame,
            text="إشعار تلقائي عندما يكون الحاسب جاهزاً",
            variable=self.wol_monitor_var,
            font=ctk.CTkFont(size=12)
        ).grid(row=3, column=0, columnspan=3, padx=15, pady=5, sticky="w")

        test_frame = ctk.CTkFrame(tab)
        test_frame.pack(fill="x", padx=20, pady=5)

        ctk.CTkButton(
            test_frame, text="🔍 فحص حالة الحاسب", width=180,
            fg_color="#1565c0", hover_color="#0d47a1",
            command=self._test_wol_status
        ).pack(side="left", padx=10, pady=10)

        ctk.CTkButton(
            test_frame, text="📡 اختبار إرسال إشارة الإيقاظ", width=220,
            fg_color="#2e7d32", hover_color="#1b5e20",
            command=self._test_wol_send
        ).pack(side="left", padx=5, pady=10)

        self.wol_status_label = ctk.CTkLabel(tab, text="", text_color="#aaa",
                                              font=ctk.CTkFont(size=12))
        self.wol_status_label.pack(pady=5)

        ctk.CTkLabel(
            tab,
            text="💡 راجع ملف SETUP_ANDROID_AR.txt لإعداد الهاتف الاحتياطي",
            font=ctk.CTkFont(size=11), text_color="#888"
        ).pack(pady=5)

    def _build_login_tab(self):
        tab = self.tabview.tab("تسجيل الدخول")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="إدارة تسجيل الدخول",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 5))
        ctk.CTkLabel(
            tab,
            text="تحكم في طريقة دخول ويندوز عند الإقلاع",
            font=ctk.CTkFont(size=11), text_color="#888"
        ).pack(pady=(0, 10))

        autologon_frame = ctk.CTkFrame(tab)
        autologon_frame.pack(fill="x", padx=20, pady=5)
        autologon_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            autologon_frame,
            text="🔑  Autologon (تسجيل دخول تلقائي)",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        ctk.CTkLabel(
            autologon_frame,
            text="أداة Microsoft الرسمية - تدخل ويندوز تلقائياً عند الإقلاع",
            font=ctk.CTkFont(size=11), text_color="#888"
        ).grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="w")

        ctk.CTkLabel(autologon_frame, text="اسم المستخدم:", width=150, anchor="w").grid(row=2, column=0, padx=10, pady=6)
        self.autologon_user_var = ctk.StringVar()
        from src.pc_control.autologon import get_current_username
        self.autologon_user_var.set(get_current_username())
        ctk.CTkEntry(autologon_frame, textvariable=self.autologon_user_var,
                     placeholder_text="اسم مستخدم ويندوز").grid(row=2, column=1, padx=10, pady=6, sticky="ew")

        ctk.CTkLabel(autologon_frame, text="كلمة المرور:", width=150, anchor="w").grid(row=3, column=0, padx=10, pady=6)
        self.autologon_pass_var = ctk.StringVar()
        ctk.CTkEntry(autologon_frame, textvariable=self.autologon_pass_var,
                     show="●", placeholder_text="كلمة مرور ويندوز").grid(row=3, column=1, padx=10, pady=6, sticky="ew")

        ctk.CTkLabel(autologon_frame, text="Domain (اختياري):", width=150, anchor="w").grid(row=4, column=0, padx=10, pady=6)
        self.autologon_domain_var = ctk.StringVar()
        from src.pc_control.autologon import get_current_domain
        self.autologon_domain_var.set(get_current_domain())
        ctk.CTkEntry(autologon_frame, textvariable=self.autologon_domain_var,
                     placeholder_text="WORKGROUP أو اسم النطاق").grid(row=4, column=1, padx=10, pady=6, sticky="ew")

        btn_row = ctk.CTkFrame(autologon_frame, fg_color="transparent")
        btn_row.grid(row=5, column=0, columnspan=2, pady=10)

        ctk.CTkButton(
            btn_row, text="✅ تفعيل Autologon", width=180,
            fg_color="#2e7d32", hover_color="#1b5e20",
            command=self._enable_autologon
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            btn_row, text="❌ تعطيل Autologon", width=180,
            fg_color="#c62828", hover_color="#b71c1c",
            command=self._disable_autologon
        ).pack(side="left", padx=8)

        self.autologon_status_label = ctk.CTkLabel(autologon_frame, text="", font=ctk.CTkFont(size=12))
        self.autologon_status_label.grid(row=6, column=0, columnspan=2, pady=5)

        self._refresh_autologon_status()

        pre_login_frame = ctk.CTkFrame(tab)
        pre_login_frame.pack(fill="x", padx=20, pady=10)
        pre_login_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            pre_login_frame,
            text="📲  Pre-Login Agent (إشعار عند الإقلاع)",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=(10, 5), sticky="w")
        ctk.CTkLabel(
            pre_login_frame,
            text="يرسل إشعاراً لتيليغرام عند كل إقلاع - يمكنك تسجيل الدخول عن بُعد",
            font=ctk.CTkFont(size=11), text_color="#888"
        ).grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 8), sticky="w")

        btn_row2 = ctk.CTkFrame(pre_login_frame, fg_color="transparent")
        btn_row2.grid(row=2, column=0, columnspan=2, pady=8)

        ctk.CTkButton(
            btn_row2, text="⚙️ تثبيت Pre-Login Agent", width=210,
            fg_color="#1565c0", hover_color="#0d47a1",
            command=self._install_pre_login
        ).pack(side="left", padx=8)
        ctk.CTkButton(
            btn_row2, text="🗑️ إلغاء التثبيت", width=150,
            fg_color="#555", hover_color="#444",
            command=self._uninstall_pre_login
        ).pack(side="left", padx=8)

        self.pre_login_status_label = ctk.CTkLabel(
            pre_login_frame, text="", font=ctk.CTkFont(size=12), text_color="#aaa"
        )
        self.pre_login_status_label.grid(row=3, column=0, columnspan=2, pady=5)

        ctk.CTkLabel(
            tab,
            text="💡 للاستخدام الأمثل: فعّل Autologon + ثبّت Pre-Login Agent معاً",
            font=ctk.CTkFont(size=11), text_color="#66bb6a"
        ).pack(pady=8)

    def _refresh_autologon_status(self):
        try:
            from src.pc_control.autologon import is_autologon_enabled
            if is_autologon_enabled():
                self.autologon_status_label.configure(
                    text="✅ Autologon مفعّل حالياً", text_color="#66bb6a"
                )
            else:
                self.autologon_status_label.configure(
                    text="⏸️ Autologon غير مفعّل", text_color="#aaa"
                )
        except Exception:
            self.autologon_status_label.configure(text="", text_color="#aaa")

    def _enable_autologon(self):
        username = self.autologon_user_var.get().strip()
        password = self.autologon_pass_var.get()
        domain   = self.autologon_domain_var.get().strip()
        if not username or not password:
            self.autologon_status_label.configure(
                text="⚠️ أدخل اسم المستخدم وكلمة المرور", text_color="#ffb300"
            )
            return
        self.autologon_status_label.configure(text="⏳ جاري الضبط...", text_color="#aaa")
        self.update()
        def setup():
            from src.pc_control.autologon import setup_autologon
            result = setup_autologon(username, password, domain)
            self.autologon_status_label.configure(
                text=result[:80],
                text_color="#66bb6a" if "✅" in result else "#ef5350"
            )
            self.autologon_pass_var.set("")
        threading.Thread(target=setup, daemon=True).start()

    def _disable_autologon(self):
        self.autologon_status_label.configure(text="⏳ جاري الإلغاء...", text_color="#aaa")
        self.update()
        def disable():
            from src.pc_control.autologon import disable_autologon
            result = disable_autologon()
            self.autologon_status_label.configure(
                text=result,
                text_color="#66bb6a" if "✅" in result else "#ef5350"
            )
        threading.Thread(target=disable, daemon=True).start()

    def _install_pre_login(self):
        import subprocess
        from pathlib import Path
        bat = Path(__file__).parents[3] / "pre_login" / "install_pre_login.bat"
        if not bat.exists():
            self.pre_login_status_label.configure(
                text="❌ ملف install_pre_login.bat غير موجود", text_color="#ef5350"
            )
            return
        try:
            subprocess.Popen(
                ["powershell", "-Command", f"Start-Process '{bat}' -Verb RunAs"]
            )
            self.pre_login_status_label.configure(
                text="🚀 تم فتح نافذة التثبيت (تأكد من الموافقة)", text_color="#66bb6a"
            )
        except Exception as e:
            self.pre_login_status_label.configure(text=f"❌ {e}", text_color="#ef5350")

    def _uninstall_pre_login(self):
        import subprocess
        try:
            subprocess.run(
                ["schtasks", "/delete", "/tn", "PCCommander_PreLogin", "/f"],
                capture_output=True, timeout=10
            )
            self.pre_login_status_label.configure(
                text="✅ تم إلغاء التثبيت", text_color="#66bb6a"
            )
        except Exception as e:
            self.pre_login_status_label.configure(text=f"❌ {e}", text_color="#ef5350")

    def _toggle_stream(self):
        from src.streaming.screen_stream import start_stream, stop_stream, get_stream_status
        cfg = {
            "stream": {
                "port":    int(self.stream_port_var.get() or 8765),
                "password": self.stream_pass_var.get() or "",
                "fps":     int(self.stream_fps_var.get()),
                "quality": int(self.stream_quality_var.get()),
                "scale":   float(self.stream_scale_var.get()),
            }
        }
        status = get_stream_status(cfg)
        def run():
            if status["running"]:
                result = stop_stream()
                self.stream_toggle_btn.configure(
                    text="▶ تشغيل البث", fg_color="#2e7d32", hover_color="#1b5e20"
                )
                self.stream_status_label.configure(text="⏸️ البث متوقف", text_color="#aaa")
            else:
                result = start_stream(cfg)
                if "✅" in result:
                    self.stream_toggle_btn.configure(
                        text="⏹ إيقاف البث", fg_color="#c62828", hover_color="#b71c1c"
                    )
                    port = cfg["stream"]["port"]
                    self.stream_status_label.configure(
                        text=f"🟢 البث يعمل على المنفذ {port}", text_color="#66bb6a"
                    )
                else:
                    self.stream_status_label.configure(text=result[:70], text_color="#ef5350")
        threading.Thread(target=run, daemon=True).start()

    def _copy_stream_url(self):
        try:
            import socket
            port = int(self.stream_port_var.get() or 8765)
            ip = socket.gethostbyname(socket.gethostname())
            url = f"http://{ip}:{port}"
            self.clipboard_clear()
            self.clipboard_append(url)
            self.stream_status_label.configure(
                text=f"📋 تم نسخ الرابط: {url}", text_color="#42a5f5"
            )
        except Exception as e:
            self.stream_status_label.configure(text=f"❌ {e}", text_color="#ef5350")

    def _build_monitoring_tab(self):
        tab = self.tabview.tab("المراقبة")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(tab, text="حدود التنبيهات",
                     font=ctk.CTkFont(size=15, weight="bold")).pack(pady=(15, 5))

        stream_frame = ctk.CTkFrame(tab)
        stream_frame.pack(fill="x", padx=20, pady=(0, 10))
        stream_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            stream_frame,
            text="📡  بث الشاشة الحي (MJPEG)",
            font=ctk.CTkFont(size=13, weight="bold")
        ).grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 2), sticky="w")
        ctk.CTkLabel(
            stream_frame,
            text="يتيح مشاهدة شاشتك من أي متصفح عبر الإنترنت",
            font=ctk.CTkFont(size=11), text_color="#888"
        ).grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 8), sticky="w")

        ctk.CTkLabel(stream_frame, text="المنفذ (Port):", width=150, anchor="w").grid(row=2, column=0, padx=10, pady=5)
        self.stream_port_var = ctk.StringVar(value="8765")
        ctk.CTkEntry(stream_frame, textvariable=self.stream_port_var, width=100).grid(row=2, column=1, padx=10, pady=5, sticky="w")

        ctk.CTkLabel(stream_frame, text="كلمة المرور:", width=150, anchor="w").grid(row=3, column=0, padx=10, pady=5)
        self.stream_pass_var = ctk.StringVar(value="")
        ctk.CTkEntry(stream_frame, textvariable=self.stream_pass_var, show="●").grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(stream_frame, text="FPS:", width=150, anchor="w").grid(row=4, column=0, padx=10, pady=5)
        self.stream_fps_var = ctk.IntVar(value=5)
        fps_slider = ctk.CTkSlider(stream_frame, from_=1, to=15, variable=self.stream_fps_var, width=200)
        fps_slider.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(stream_frame, textvariable=self.stream_fps_var, width=30).grid(row=4, column=2, padx=5)

        ctk.CTkLabel(stream_frame, text="جودة الصورة (%):", width=150, anchor="w").grid(row=5, column=0, padx=10, pady=5)
        self.stream_quality_var = ctk.IntVar(value=60)
        quality_slider = ctk.CTkSlider(stream_frame, from_=20, to=95, variable=self.stream_quality_var, width=200)
        quality_slider.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(stream_frame, textvariable=self.stream_quality_var, width=30).grid(row=5, column=2, padx=5)

        ctk.CTkLabel(stream_frame, text="حجم الصورة (Scale):", width=150, anchor="w").grid(row=6, column=0, padx=10, pady=5)
        self.stream_scale_var = ctk.DoubleVar(value=0.8)

        def _format_scale(v):
            return f"{float(v):.0%}"
        scale_slider = ctk.CTkSlider(stream_frame, from_=0.3, to=1.0, variable=self.stream_scale_var, width=200)
        scale_slider.grid(row=6, column=1, padx=10, pady=5, sticky="ew")
        self.stream_scale_lbl = ctk.CTkLabel(stream_frame, text="80%", width=35)
        self.stream_scale_lbl.grid(row=6, column=2, padx=5)
        scale_slider.configure(command=lambda v: self.stream_scale_lbl.configure(text=f"{float(v):.0%}"))

        stream_btn_row = ctk.CTkFrame(stream_frame, fg_color="transparent")
        stream_btn_row.grid(row=7, column=0, columnspan=3, pady=10)

        self.stream_toggle_btn = ctk.CTkButton(
            stream_btn_row, text="▶ تشغيل البث", width=160,
            fg_color="#2e7d32", hover_color="#1b5e20",
            command=self._toggle_stream
        )
        self.stream_toggle_btn.pack(side="left", padx=8)

        ctk.CTkButton(
            stream_btn_row, text="🔗 نسخ الرابط", width=130,
            fg_color="#1565c0", hover_color="#0d47a1",
            command=self._copy_stream_url
        ).pack(side="left", padx=8)

        self.stream_status_label = ctk.CTkLabel(
            stream_frame, text="⏸️ البث متوقف", font=ctk.CTkFont(size=12), text_color="#aaa"
        )
        self.stream_status_label.grid(row=8, column=0, columnspan=3, pady=5)

        sep = ctk.CTkLabel(tab, text="", height=5)
        sep.pack()

        ctk.CTkLabel(tab, text="حدود التنبيهات",
                     font=ctk.CTkFont(size=13, weight="bold")).pack(pady=(5, 5))

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
        self.lan_access_var.set(cfg.get("server", {}).get("lan_access", False))
        self.use_webhook_var.set(cfg["tunnel"].get("use_webhook", False))
        self.webhook_url_var.set(cfg["tunnel"].get("webhook_url", ""))
        self.anydesk_path_var.set(cfg["anydesk"].get("path", ""))
        wol = cfg.get("wol", {})
        self.wol_mac_var.set(wol.get("mac_address", ""))
        self.wol_ip_var.set(wol.get("pc_ip", ""))
        self.wol_broadcast_var.set(wol.get("broadcast_ip", "255.255.255.255"))
        self.wol_backup_users_var.set(", ".join(str(u) for u in wol.get("backup_users", [])))
        self.wol_auto_notify_var.set(wol.get("auto_notify_backup", True))
        self.wol_monitor_var.set(wol.get("monitor_startup", True))
        self.startup_var.set(is_startup_enabled())
        self.dnd_var.set(cfg["general"].get("do_not_disturb", False))
        self.log_commands_var.set(cfg["security"].get("log_commands", True))
        self.notify_unauth_var.set(cfg["security"].get("notify_on_unauthorized", True))
        self.watchdog_var.set(cfg["security"].get("watchdog_enabled", True))
        self.require_pin_var.set(cfg["security"].get("require_pin", False))
        self.session_pin_var.set(cfg["security"].get("session_pin", ""))
        self.daily_report_var.set(cfg["general"].get("daily_report_enabled", True))
        self.report_time_var.set(cfg["general"].get("daily_report_time", "08:00"))
        mon = cfg.get("monitoring", {})
        self.monitor_vars["cpu_alert"].set(mon.get("cpu_alert_threshold", 90))
        self.monitor_vars["ram_alert"].set(mon.get("ram_alert_threshold", 90))
        self.monitor_vars["disk_alert"].set(mon.get("disk_alert_threshold", 90))
        self.monitor_vars["temp_alert"].set(mon.get("temp_alert_threshold", 80))
        self._on_ai_provider_change()
        self._on_tunnel_change()
        self._detect_running_bot()

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
        self.config["tunnel"]["use_webhook"] = self.use_webhook_var.get()
        self.config["tunnel"]["webhook_url"] = self.webhook_url_var.get().strip()
        if "server" not in self.config:
            self.config["server"] = {}
        self.config["server"]["lan_access"] = self.lan_access_var.get()
        self.config["anydesk"]["path"] = self.anydesk_path_var.get().strip()
        wol_backup_raw = self.wol_backup_users_var.get().strip()
        wol_backup = [u.strip() for u in wol_backup_raw.split(",") if u.strip().isdigit()]
        self.config["wol"]["mac_address"] = self.wol_mac_var.get().strip()
        self.config["wol"]["pc_ip"] = self.wol_ip_var.get().strip()
        self.config["wol"]["broadcast_ip"] = self.wol_broadcast_var.get().strip()
        self.config["wol"]["backup_users"] = wol_backup
        self.config["wol"]["auto_notify_backup"] = self.wol_auto_notify_var.get()
        self.config["wol"]["monitor_startup"] = self.wol_monitor_var.get()
        self.config["general"]["do_not_disturb"] = self.dnd_var.get()
        self.config["general"]["daily_report_enabled"] = self.daily_report_var.get()
        self.config["general"]["daily_report_time"] = self.report_time_var.get().strip()
        self.config["security"]["log_commands"] = self.log_commands_var.get()
        self.config["security"]["notify_on_unauthorized"] = self.notify_unauth_var.get()
        self.config["security"]["watchdog_enabled"] = self.watchdog_var.get()
        self.config["security"]["require_pin"] = self.require_pin_var.get()
        self.config["security"]["session_pin"] = self.session_pin_var.get().strip()
        self.config["monitoring"]["cpu_alert_threshold"] = self.monitor_vars["cpu_alert"].get()
        self.config["monitoring"]["ram_alert_threshold"] = self.monitor_vars["ram_alert"].get()
        self.config["monitoring"]["disk_alert_threshold"] = self.monitor_vars["disk_alert"].get()
        self.config["monitoring"]["temp_alert_threshold"] = self.monitor_vars["temp_alert"].get()
        if "stream" not in self.config:
            self.config["stream"] = {}
        self.config["stream"]["port"]     = int(self.stream_port_var.get() or 8765)
        self.config["stream"]["password"] = self.stream_pass_var.get() or ""
        self.config["stream"]["fps"]      = int(self.stream_fps_var.get())
        self.config["stream"]["quality"]  = int(self.stream_quality_var.get())
        self.config["stream"]["scale"]    = float(self.stream_scale_var.get())

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
        provider = self.ai_provider_var.get()
        if provider == "openai":
            self.gemini_frame.pack_forget()
            self.openai_frame.pack(fill="x", padx=20, pady=5)
        else:
            self.openai_frame.pack_forget()
            self.gemini_frame.pack(fill="x", padx=20, pady=5)

    def _on_tunnel_change(self):
        provider = self.tunnel_provider_var.get()
        if provider == "cloudflare":
            self.cloudflare_frame.pack(fill="x", padx=20, pady=5)
            self.ngrok_frame.pack_forget()
        elif provider == "ngrok":
            self.ngrok_frame.pack(fill="x", padx=20, pady=5)
            self.cloudflare_frame.pack_forget()
        else:
            self.cloudflare_frame.pack_forget()
            self.ngrok_frame.pack_forget()

    def _detect_running_bot(self):
        import subprocess
        try:
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"],
                capture_output=True, text=True, timeout=5, creationflags=0x08000000
            )
            if "python.exe" in result.stdout.lower():
                self.is_running = True
                self.start_btn.configure(text="⏹  إيقاف", fg_color="#c62828", hover_color="#b71c1c")
                self.status_label.configure(text="🟢 يعمل", text_color="#66bb6a")
        except Exception:
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

    def _detect_mac(self):
        try:
            from src.pc_control.wake_on_lan import get_pc_mac_windows
            mac = get_pc_mac_windows()
            if mac:
                self.wol_mac_var.set(mac)
                self.wol_status_label.configure(text=f"✅ تم اكتشاف MAC: {mac}", text_color="#66bb6a")
            else:
                self.wol_status_label.configure(text="❌ تعذر الاكتشاف التلقائي", text_color="#ef5350")
        except Exception as e:
            self.wol_status_label.configure(text=f"❌ {e}", text_color="#ef5350")

    def _test_wol_status(self):
        ip = self.wol_ip_var.get().strip()
        if not ip:
            self.wol_status_label.configure(text="⚠️ أدخل IP الحاسب أولاً", text_color="#ffb300")
            return
        self.wol_status_label.configure(text="🔍 جاري الفحص...", text_color="#aaa")
        self.update()

        def check():
            import socket
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(3)
                result = s.connect_ex((ip, 445))
                s.close()
                if result == 0:
                    self.wol_status_label.configure(text=f"✅ الحاسب يعمل على {ip}", text_color="#66bb6a")
                else:
                    self.wol_status_label.configure(text=f"❌ الحاسب مطفأ أو غير متاح ({ip})", text_color="#ef5350")
            except Exception as e:
                self.wol_status_label.configure(text=f"❌ {e}", text_color="#ef5350")

        threading.Thread(target=check, daemon=True).start()

    def _test_wol_send(self):
        mac = self.wol_mac_var.get().strip()
        broadcast = self.wol_broadcast_var.get().strip() or "255.255.255.255"
        if not mac:
            self.wol_status_label.configure(text="⚠️ أدخل MAC Address أولاً", text_color="#ffb300")
            return

        def send():
            try:
                from src.pc_control.wake_on_lan import send_magic_packet, validate_mac
                if not validate_mac(mac):
                    self.wol_status_label.configure(text="❌ MAC Address غير صالح", text_color="#ef5350")
                    return
                self.wol_status_label.configure(text="📡 جاري الإرسال...", text_color="#aaa")
                success = send_magic_packet(mac, broadcast)
                if success:
                    self.wol_status_label.configure(
                        text="✅ تم إرسال Magic Packet بنجاح!", text_color="#66bb6a"
                    )
                else:
                    self.wol_status_label.configure(text="❌ فشل الإرسال", text_color="#ef5350")
            except Exception as e:
                self.wol_status_label.configure(text=f"❌ {e}", text_color="#ef5350")

        threading.Thread(target=send, daemon=True).start()

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
