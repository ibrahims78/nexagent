import asyncio
import json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from src.utils.config import get_config_dir
from src.utils.logger import get_logger

logger = get_logger()


class TaskScheduler:
    def __init__(self, bot=None, config: dict = None):
        self.config = config or {}
        tz = self.config.get("general", {}).get("timezone", "Asia/Riyadh")
        self.scheduler = BackgroundScheduler(timezone=tz)
        self.bot = bot
        self._tasks_file = get_config_dir() / "scheduled_tasks.json"
        self.tasks = self._load_tasks()

    def start(self):
        self._setup_default_jobs()
        self._restore_saved_tasks()
        self.scheduler.start()
        logger.info("✅ المجدول يعمل")

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def _setup_default_jobs(self):
        general = self.config.get("general", {})
        if general.get("daily_report_enabled", True):
            report_time = general.get("daily_report_time", "08:00")
            hour, minute = map(int, report_time.split(":"))
            self.scheduler.add_job(
                self._send_daily_report,
                CronTrigger(hour=hour, minute=minute),
                id="daily_report",
                replace_existing=True
            )

        self.scheduler.add_job(
            self._check_alerts,
            IntervalTrigger(minutes=5),
            id="alert_check",
            replace_existing=True
        )

    def _send_daily_report(self):
        from src.pc_control.system_monitor import get_daily_report
        try:
            report = get_daily_report()
            if self.bot:
                try:
                    asyncio.run(self.bot.send_notification(report))
                except RuntimeError:
                    pass
        except Exception as e:
            logger.error(f"خطأ في التقرير اليومي: {e}")

    def _check_alerts(self):
        from src.pc_control.system_monitor import check_alerts
        try:
            alerts = check_alerts(self.config)
            if alerts and self.bot:
                message = "⚠️ **تنبيهات النظام:**\n" + "\n".join(alerts)
                try:
                    asyncio.run(self.bot.send_notification(message))
                except RuntimeError:
                    pass
        except Exception as e:
            logger.error(f"خطأ في فحص التنبيهات: {e}")

    def add_task(self, name: str, command: str, cron_expr: str) -> str:
        try:
            hour, minute = map(int, cron_expr.split(":"))
            self.scheduler.add_job(
                lambda: self._execute_scheduled(command),
                CronTrigger(hour=hour, minute=minute),
                id=f"task_{name}",
                replace_existing=True
            )
            self.tasks[name] = {"command": command, "time": cron_expr}
            self._save_tasks()
            return f"✅ تم جدولة: {name} في {cron_expr}"
        except Exception as e:
            return f"❌ فشل الجدولة: {e}"

    def remove_task(self, name: str) -> str:
        try:
            self.scheduler.remove_job(f"task_{name}")
            self.tasks.pop(name, None)
            self._save_tasks()
            return f"✅ تم إلغاء: {name}"
        except Exception as e:
            return f"❌ فشل الإلغاء: {e}"

    def list_tasks(self) -> str:
        if not self.tasks:
            return "📭 لا توجد مهام مجدولة"
        result = "📋 **المهام المجدولة:**\n"
        for name, data in self.tasks.items():
            result += f"• {name}: `{data['command']}` في {data['time']}\n"
        return result

    def _execute_scheduled(self, command: str):
        from src.bot.commands import execute_command
        try:
            result_text, _ = execute_command(command, [], self.config)
            if self.bot:
                try:
                    asyncio.run(self.bot.send_notification(
                        f"⏰ **مهمة مجدولة:**\n{result_text}"
                    ))
                except RuntimeError:
                    pass
        except Exception as e:
            logger.error(f"خطأ في تنفيذ المهمة المجدولة: {e}")

    def _load_tasks(self) -> dict:
        try:
            if self._tasks_file.exists():
                with open(self._tasks_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _save_tasks(self):
        try:
            with open(self._tasks_file, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _restore_saved_tasks(self):
        for name, data in self.tasks.items():
            try:
                hour, minute = map(int, data["time"].split(":"))
                self.scheduler.add_job(
                    lambda c=data["command"]: self._execute_scheduled(c),
                    CronTrigger(hour=hour, minute=minute),
                    id=f"task_{name}",
                    replace_existing=True
                )
            except Exception:
                pass
