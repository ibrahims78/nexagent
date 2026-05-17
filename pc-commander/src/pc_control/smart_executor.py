import sys
import time
from src.utils.logger import get_logger

logger = get_logger()


class SmartExecutor:
    """
    منفذ ذكي: يأخذ لقطة شاشة → يحللها بـ GPT-4 Vision → ينفذ الإجراءات تلقائياً
    """

    def __init__(self, vision_handler):
        self.vision = vision_handler

    def execute_smart_command(self, user_command: str) -> dict:
        from src.pc_control.screenshot import take_screenshot
        from src.pc_control.visual_control import execute_visual_actions, take_annotated_screenshot

        logger.info(f"🧠 تنفيذ أمر ذكي: {user_command}")

        screenshot_data = take_screenshot()

        analysis = self.vision.analyze_screen(screenshot_data, user_command)
        actions = analysis.get("actions", [])
        response = analysis.get("response", "")
        description = analysis.get("screen_description", "")

        annotated = None
        if actions and any(a.get("type") not in ["describe"] for a in actions):
            annotated = take_annotated_screenshot(actions)

        results = execute_visual_actions(actions)

        if any(a.get("type") == "type" for a in actions):
            time.sleep(0.5)

        return {
            "response": response,
            "screen_description": description,
            "actions_taken": results,
            "annotated_screenshot": annotated,
            "actions_count": len([a for a in actions if a.get("type") != "describe"])
        }

    def describe_current_screen(self) -> str:
        from src.pc_control.screenshot import take_screenshot
        screenshot_data = take_screenshot()
        return self.vision.describe_screen(screenshot_data)

    def find_and_click(self, element_description: str) -> str:
        from src.pc_control.screenshot import take_screenshot
        from src.pc_control.visual_control import _click

        screenshot_data = take_screenshot()
        result = self.vision.find_element(screenshot_data, element_description)

        if result.get("found") and "x" in result and "y" in result:
            _click(result["x"], result["y"])
            return f"✅ تم العثور على '{element_description}' والضغط عليه في ({result['x']}, {result['y']})"
        return f"❌ لم يتم العثور على: {element_description}"

    def smart_type_in_field(self, field_description: str, text: str) -> str:
        from src.pc_control.screenshot import take_screenshot
        from src.pc_control.visual_control import _click, _type_text

        screenshot_data = take_screenshot()
        result = self.vision.find_element(screenshot_data, field_description)

        if result.get("found"):
            _click(result["x"], result["y"])
            time.sleep(0.3)
            _type_text(text)
            return f"✅ تم الكتابة في '{field_description}': {text[:50]}"
        return f"❌ لم يتم العثور على الحقل: {field_description}"

    def wait_for_element(self, element_description: str, timeout: int = 10) -> bool:
        from src.pc_control.screenshot import take_screenshot
        import time as t

        start = t.time()
        while t.time() - start < timeout:
            screenshot_data = take_screenshot()
            result = self.vision.find_element(screenshot_data, element_description)
            if result.get("found"):
                return True
            t.sleep(1)
        return False

    def multi_step_task(self, task_description: str, max_steps: int = 5) -> list:
        from src.pc_control.screenshot import take_screenshot

        logger.info(f"🔄 مهمة متعددة الخطوات: {task_description}")
        results = []

        for step in range(max_steps):
            screenshot_data = take_screenshot()
            prompt = (
                f"المهمة الأصلية: {task_description}\n"
                f"الخطوة الحالية: {step + 1}/{max_steps}\n"
                f"الخطوات المنجزة: {results}\n\n"
                "انظر للشاشة الحالية وحدد الخطوة التالية لإنجاز المهمة. "
                "إذا اكتملت المهمة، أرجع إجراء واحد فقط من نوع describe مع وصف للنتيجة."
            )
            analysis = self.vision.analyze_screen(screenshot_data, prompt)
            actions = analysis.get("actions", [])

            if not actions or (len(actions) == 1 and actions[0].get("type") == "describe"):
                results.append(f"✅ اكتملت المهمة: {analysis.get('response', '')}")
                break

            from src.pc_control.visual_control import execute_visual_actions
            step_results = execute_visual_actions(actions)
            results.extend(step_results)
            time.sleep(0.8)

        return results
