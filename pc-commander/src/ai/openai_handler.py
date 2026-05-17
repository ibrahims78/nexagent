import os
import io
from openai import OpenAI

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
- open_file [مسار]: فتح ملف
- read_word [مسار]: قراءة ملف Word
- edit_word [مسار] [نص]: إضافة نص لملف Word
- create_word [مسار] [عنوان] [محتوى]: إنشاء ملف Word
- system_status: حالة الحاسب
- anydesk_start: تشغيل AnyDesk
- anydesk_stop: إغلاق AnyDesk
- volume [0-100]: ضبط الصوت
- cancel_shutdown: إلغاء إيقاف التشغيل

رد بتنسيق JSON فقط:
{"command": "اسم_الأمر", "args": [], "response": "رسالة للمستخدم"}

إذا كان الطلب غير واضح أو محادثة عادية، استخدم:
{"command": "chat", "args": [], "response": "ردك هنا"}"""


class OpenAIHandler:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def process_command(self, user_message: str, context: list = None) -> dict:
        messages = [{"role": "system", "content": SYSTEM_PROMPT_AR}]
        if context:
            messages.extend(context[-6:])
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=500
            )
            import json
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            return {"command": "chat", "args": [], "response": f"❌ خطأ في الذكاء الاصطناعي: {e}"}

    def transcribe_audio(self, audio_data: bytes, language: str = "ar") -> str:
        try:
            audio_file = io.BytesIO(audio_data)
            audio_file.name = "audio.ogg"
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language
            )
            return transcript.text
        except Exception as e:
            return f"❌ فشل تحويل الصوت: {e}"

    def text_to_speech(self, text: str) -> bytes:
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            return response.content
        except Exception as e:
            return None

    def verify_key(self) -> bool:
        try:
            self.client.models.list()
            return True
        except Exception:
            return False
