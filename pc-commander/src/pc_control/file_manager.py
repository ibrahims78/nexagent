import os
import shutil
import sys
from pathlib import Path
from datetime import datetime

IS_WINDOWS = sys.platform == "win32"

ALLOWED_BASE_PATHS: list = [
    os.path.expanduser("~"),
    os.path.join(os.path.expanduser("~"), "Desktop"),
    os.path.join(os.path.expanduser("~"), "Documents"),
    os.path.join(os.path.expanduser("~"), "Downloads"),
    os.path.join(os.path.expanduser("~"), "Pictures"),
]


def is_safe_path(path: str) -> bool:
    """Return True only if path resolves inside one of ALLOWED_BASE_PATHS."""
    try:
        resolved = Path(path).resolve()
        return any(
            resolved == base or base in resolved.parents
            for base in [Path(p).resolve() for p in ALLOWED_BASE_PATHS]
        )
    except Exception:
        return False


def list_directory(path: str = None) -> str:
    if path is None:
        path = os.path.expanduser("~")
    if not is_safe_path(path):
        return f"❌ الوصول مرفوض: المسار خارج النطاق المسموح به: {path}"
    try:
        p = Path(path)
        if not p.exists():
            return f"❌ المسار غير موجود: {path}"
        items = list(p.iterdir())
        dirs = [f"📁 {i.name}" for i in items if i.is_dir()]
        files = [f"📄 {i.name} ({_human_size(i.stat().st_size)})" for i in items if i.is_file()]
        result = f"📂 **{path}**\n\n"
        if dirs:
            result += "**المجلدات:**\n" + "\n".join(sorted(dirs)[:20]) + "\n\n"
        if files:
            result += "**الملفات:**\n" + "\n".join(sorted(files)[:20])
        return result or "📂 المجلد فارغ"
    except Exception as e:
        return f"❌ خطأ: {e}"


def delete_file(path: str) -> str:
    if not is_safe_path(path):
        return f"❌ الوصول مرفوض: المسار خارج النطاق المسموح به: {path}"
    try:
        p = Path(path)
        if not p.exists():
            return f"❌ الملف غير موجود: {path}"
        if p.is_dir():
            shutil.rmtree(p)
            return f"✅ تم حذف المجلد: {path}"
        p.unlink()
        return f"✅ تم حذف الملف: {path}"
    except Exception as e:
        return f"❌ فشل الحذف: {e}"


def create_folder(path: str) -> str:
    if not is_safe_path(path):
        return f"❌ الوصول مرفوض: المسار خارج النطاق المسموح به: {path}"
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return f"✅ تم إنشاء المجلد: {path}"
    except Exception as e:
        return f"❌ فشل إنشاء المجلد: {e}"


def copy_file(src: str, dst: str) -> str:
    if not is_safe_path(src):
        return f"❌ الوصول مرفوض: المسار المصدر خارج النطاق المسموح به: {src}"
    if not is_safe_path(dst):
        return f"❌ الوصول مرفوض: المسار الهدف خارج النطاق المسموح به: {dst}"
    try:
        shutil.copy2(src, dst)
        return f"✅ تم نسخ: {src} → {dst}"
    except Exception as e:
        return f"❌ فشل النسخ: {e}"


def move_file(src: str, dst: str) -> str:
    if not is_safe_path(src):
        return f"❌ الوصول مرفوض: المسار المصدر خارج النطاق المسموح به: {src}"
    if not is_safe_path(dst):
        return f"❌ الوصول مرفوض: المسار الهدف خارج النطاق المسموح به: {dst}"
    try:
        shutil.move(src, dst)
        return f"✅ تم نقل: {src} → {dst}"
    except Exception as e:
        return f"❌ فشل النقل: {e}"


def get_file_info(path: str) -> str:
    if not is_safe_path(path):
        return f"❌ الوصول مرفوض: المسار خارج النطاق المسموح به: {path}"
    try:
        p = Path(path)
        if not p.exists():
            return "❌ الملف غير موجود"
        stat = p.stat()
        info = "📄 **معلومات الملف:**\n"
        info += f"• الاسم: {p.name}\n"
        info += f"• الحجم: {_human_size(stat.st_size)}\n"
        info += f"• النوع: {'مجلد' if p.is_dir() else p.suffix or 'ملف'}\n"
        info += f"• آخر تعديل: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')}\n"
        info += f"• المسار: {p.parent}"
        return info
    except Exception as e:
        return f"❌ خطأ: {e}"


def search_files(folder: str, pattern: str) -> str:
    if not is_safe_path(folder):
        return f"❌ الوصول مرفوض: المسار خارج النطاق المسموح به: {folder}"
    try:
        p = Path(folder)
        results = list(p.rglob(pattern))[:20]
        if not results:
            return f"❌ لا توجد نتائج للبحث عن: {pattern}"
        return "🔍 **نتائج البحث:**\n" + "\n".join([f"• {r}" for r in results])
    except Exception as e:
        return f"❌ خطأ في البحث: {e}"


def _human_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def open_file(path: str) -> str:
    if not is_safe_path(path):
        return f"❌ الوصول مرفوض: المسار خارج النطاق المسموح به: {path}"
    try:
        if IS_WINDOWS:
            os.startfile(path)
        else:
            import subprocess
            subprocess.Popen(["xdg-open", path])
        return f"✅ تم فتح: {path}"
    except Exception as e:
        return f"❌ فشل الفتح: {e}"
