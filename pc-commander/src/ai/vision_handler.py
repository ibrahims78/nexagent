import base64
import sys
import json
from src.utils.logger import get_logger

logger = get_logger()
IS_WINDOWS = sys.platform == "win32"

VISION_SYSTEM_PROMPT = """أنت مساعد ذكاء اصطناعي بصري متخصص في التحكم بحاسب ويندوز.
سيتم إرسال لقطة شاشة إليك مع أمر من المستخدم.

مهمتك:
1. تحليل محتوى الشاشة بدقة
2. تحديد الإجراء المطلوب لتنفيذ الأمر
3. إرجاع الخطوات بتنسيق JSON

أنواع الإجراءات المتاحة:
- click: الضغط على إحداثيات محددة {x, y}
- double_click: نقر مزدوج على {x, y}
- right_click: نقر بالزر الأيمن على {x, y}
- type: كتابة نص {"text": "..."}
- key: ضغط مفتاح {"key": "enter/tab/escape/..."}
- scroll: التمرير {"x": x, "y": y, "direction": "up/down", "amount": 3}
- hotkey: اختصار لوحة مفاتيح {"keys": ["ctrl", "c"]}
- describe: وصف ما على الشاشة فقط بدون إجراء

رد بتنسيق JSON فقط:
{
  "screen_description": "وصف مختصر لما تراه على الشاشة",
  "understanding": "ماذا يريد المستخدم",
  "actions": [
    {"type": "click", "x": 100, "y": 200, "description": "الضغط على زر كذا"},
    {"type": "type", "text": "النص المطلوب", "description": "كتابة النص"}
  ],
  "response": "ما الذي ستفعله للمستخدم بالعربي"
}

ملاحظة: الإحداثيات يجب أن تكون دقيقة بناءً على ما تراه في الصورة."""


class VisionHandler:
    def __init__(self, ai_handler=None, api_key: str = "", model: str = "gpt-4o"):
        """
        Accept either an existing OpenAIHandler instance (preferred),
        or a raw api_key string for backward compatibility.
        """
        if ai_handler is not None:
            if hasattr(ai_handler, "client"):
                self.client = ai_handler.client
                self.model = getattr(ai_handler, "model", model)
            else:
                raise TypeError(f"Unsupported ai_handler type: {type(ai_handler)}")
        else:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = model

    def analyze_screen(self, screenshot_bytes: bytes, user_command: str) -> dict:
        try:
            b64_image = base64.b64encode(screenshot_bytes).decode("utf-8")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": VISION_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64_image}",
                                    "detail": "high"
                                }
                            },
                            {
                                "type": "text",
                                "text": f"الأمر: {user_command}"
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=1000
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Vision analysis error: {e}")
            return {"response": f"❌ خطأ في التحليل البصري: {e}", "actions": []}

    def describe_screen(self, screenshot_bytes: bytes) -> str:
        try:
            b64_image = base64.b64encode(screenshot_bytes).decode("utf-8")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64_image}",
                                    "detail": "high"
                                }
                            },
                            {
                                "type": "text",
                                "text": "صف بالتفصيل ما تراه على هذه الشاشة بالعربي. اذكر كل النوافذ المفتوحة والعناصر المرئية والنصوص الظاهرة."
                            }
                        ]
                    }
                ],
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"❌ فشل وصف الشاشة: {e}"

    def find_element(self, screenshot_bytes: bytes, element_description: str) -> dict:
        try:
            b64_image = base64.b64encode(screenshot_bytes).decode("utf-8")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64_image}",
                                    "detail": "high"
                                }
                            },
                            {
                                "type": "text",
                                "text": f"ابحث عن العنصر التالي في الصورة وأعطني إحداثياته بالضبط: {element_description}\n\nرد بـ JSON فقط: {{\"found\": true/false, \"x\": 0, \"y\": 0, \"description\": \"وصف\"}}"
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                max_tokens=200
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            return {"found": False, "description": f"خطأ: {e}"}
