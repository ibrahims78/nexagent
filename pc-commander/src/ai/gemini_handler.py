import google.generativeai as genai
import json
import re
import io

SYSTEM_PROMPT_AR = """أنت مساعد ذكاء اصطناعي متخصص في التحكم بحاسب شخصي يعمل بنظام ويندوز.
مهمتك تحليل طلب المستخدم وتحديد الأمر المناسب لتنفيذه.

الأوامر المتاحة:
- screenshot: أخذ لقطة شاشة
- open_app [اسم_التطبيق]: فتح تطبيق
- close_app [اسم_التطبيق]: إغلاق تطبيق
- list_processes: قائمة البرامج النشطة
- run_cmd [أمر]: تشغيل أمر في سطر الأوامر
- shutdown [دقائق]: إغلاق الحاسب
- restart [دقائق]: إعادة التشغيل
- lock: قفل الشاشة
- list_files [مسار]: عرض محتويات مجلد
- delete_file [مسار]: حذف ملف
- copy_file [مصدر] [هدف]: نسخ ملف
- move_file [مصدر] [هدف]: نقل أو إعادة تسمية ملف
- search_files [مجلد] [نمط]: البحث عن ملفات
- open_file [مسار]: فتح ملف
- read_word [مسار]: قراءة ملف Word
- edit_word [مسار] [نص]: إضافة نص لملف Word
- create_word [مسار] [عنوان] [محتوى]: إنشاء ملف Word
- system_status: حالة الحاسب
- anydesk_start: تشغيل AnyDesk
- anydesk_stop: إغلاق AnyDesk
- volume [0-100]: ضبط الصوت
- cancel_shutdown: إلغاء إيقاف التشغيل

🔌 أوامر إيقاظ الحاسب (Wake-on-LAN):
- wol_start: إرسال إشارة إيقاظ للحاسب
- wol_notify: إشعار الشخص الاحتياطي لتشغيل الحاسب
- wol_status: فحص حالة الحاسب

🧠 أوامر التحكم البصري الذكي:
- vision_do [أمر]: تنفيذ أمر بصري ذكي (يرى الشاشة وينفذ)
- vision_describe: وصف ما على الشاشة الآن
- vision_find_click [وصف]: ابحث عن عنصر واضغط عليه
- vision_task [مهمة]: مهمة متعددة خطوات ذكية

استخدم vision_do عند قول المستخدم: "اضغط على..."، "انقر..."، "أغلق النافذة"

رد بتنسيق JSON فقط بدون أي نص إضافي:
{"command": "اسم_الأمر", "args": [], "response": "رسالة للمستخدم"}

إذا كان الطلب غير واضح أو محادثة عادية، استخدم:
{"command": "chat", "args": [], "response": "ردك هنا"}"""


class GeminiHandler:
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        """Initialize the Gemini handler with the given API key and model."""
        genai.configure(api_key=api_key)
        self.model_name = model
        self.model = genai.GenerativeModel(
            model_name=model,
            system_instruction=SYSTEM_PROMPT_AR
        )

    def process_command(self, user_message: str, context: list = None) -> dict:
        """Send user message to Gemini with conversation history and parse JSON response."""
        try:
            history = []
            if context:
                for msg in context[-6:]:
                    role = "user" if msg.get("role") == "user" else "model"
                    history.append({"role": role, "parts": [msg.get("content", "")]})

            chat = self.model.start_chat(history=history)
            response = chat.send_message(user_message)
            text = response.text.strip()
            match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
            if match:
                text = match.group(1).strip()
            else:
                obj_match = re.search(r'\{.*\}', text, re.DOTALL)
                if obj_match:
                    text = obj_match.group(0)
            return json.loads(text)
        except json.JSONDecodeError:
            return {"command": "chat", "args": [], "response": response.text}
        except Exception as e:
            return {"command": "chat", "args": [], "response": f"❌ Gemini error: {e}"}

    def transcribe_audio(self, audio_data: bytes, language: str = "ar") -> str:
        """Transcribe audio bytes to text using SpeechRecognition (Google)."""
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            audio_io = io.BytesIO(audio_data)
            with sr.AudioFile(audio_io) as source:
                audio = r.record(source)
            return r.recognize_google(audio, language="ar-SA")
        except Exception:
            return "❌ تحويل الصوت غير متاح مع Gemini، استخدم OpenAI للصوت"

    def text_to_speech(self, text: str) -> bytes:
        """Convert text to Arabic speech and return audio bytes."""
        try:
            from gtts import gTTS
            tts = gTTS(text=text, lang="ar", slow=False)
            buf = io.BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            return buf.read()
        except Exception:
            return None

    def verify_key(self) -> bool:
        """Verify that the configured API key is valid by sending a test prompt."""
        try:
            model = genai.GenerativeModel(self.model_name)
            model.generate_content("test")
            return True
        except Exception:
            return False
