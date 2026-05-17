"""
NexAgent - Command Whitelist Layer
Validates commands and arguments before execution.
"""
from src.utils.logger import get_logger

logger = get_logger()

COMMAND_REGISTRY: dict = {
    "screenshot":        {"min_args": 0, "max_args": 0},
    "open_app":          {"min_args": 1, "max_args": 5},
    "close_app":         {"min_args": 1, "max_args": 1},
    "list_processes":    {"min_args": 0, "max_args": 0},
    "run_cmd":           {"min_args": 1, "max_args": 50},
    "shutdown":          {"min_args": 0, "max_args": 1, "arg_types": [int]},
    "restart":           {"min_args": 0, "max_args": 1, "arg_types": [int]},
    "cancel_shutdown":   {"min_args": 0, "max_args": 0},
    "lock":              {"min_args": 0, "max_args": 0},
    "volume":            {"min_args": 0, "max_args": 1, "arg_types": [int]},
    "list_files":        {"min_args": 0, "max_args": 1},
    "delete_file":       {"min_args": 1, "max_args": 1},
    "open_file":         {"min_args": 1, "max_args": 1},
    "search_files":      {"min_args": 0, "max_args": 2},
    "copy_file":         {"min_args": 2, "max_args": 2},
    "move_file":         {"min_args": 2, "max_args": 2},
    "read_word":         {"min_args": 1, "max_args": 1},
    "edit_word":         {"min_args": 2, "max_args": 50},
    "create_word":       {"min_args": 1, "max_args": 50},
    "system_status":     {"min_args": 0, "max_args": 0},
    "daily_report":      {"min_args": 0, "max_args": 0},
    "anydesk_start":     {"min_args": 0, "max_args": 0},
    "anydesk_stop":      {"min_args": 0, "max_args": 0},
    "anydesk_id":        {"min_args": 0, "max_args": 0},
    "wol_start":         {"min_args": 0, "max_args": 0},
    "wol_notify":        {"min_args": 0, "max_args": 0},
    "wol_status":        {"min_args": 0, "max_args": 0},
    "vision_do":         {"min_args": 0, "max_args": 50},
    "vision_describe":   {"min_args": 0, "max_args": 0},
    "vision_find_click": {"min_args": 1, "max_args": 1},
    "vision_task":       {"min_args": 0, "max_args": 50},
    "autologon_enable":  {"min_args": 1, "max_args": 2},
    "autologon_disable": {"min_args": 0, "max_args": 0},
    "autologon_status":  {"min_args": 0, "max_args": 0},
    "pre_login_status":  {"min_args": 0, "max_args": 0},
    "stream_start":      {"min_args": 0, "max_args": 0},
    "stream_stop":       {"min_args": 0, "max_args": 0},
    "stream_status":     {"min_args": 0, "max_args": 0},
    "security_report":   {"min_args": 0, "max_args": 0},
    "security_block":    {"min_args": 1, "max_args": 1, "arg_types": [str]},
    "security_unblock":  {"min_args": 1, "max_args": 1, "arg_types": [str]},
    "watchdog_status":   {"min_args": 0, "max_args": 0},
    "logout":            {"min_args": 0, "max_args": 1},
    "chat":              {"min_args": 0, "max_args": 100},
    "ssh_exec":          {"min_args": 1, "max_args": 50},
    "ssh_status":        {"min_args": 0, "max_args": 0},
    "ssh_list":          {"min_args": 0, "max_args": 1},
    "sftp_get":          {"min_args": 1, "max_args": 1},
    "sftp_put":          {"min_args": 2, "max_args": 2},
    "ssh_bore_port":     {"min_args": 0, "max_args": 0},
}


def validate_command(command: str, args: list) -> tuple[bool, str]:
    """
    Validate a command and its arguments against the registry.

    Returns:
        (True, "OK") if valid
        (False, reason) if invalid — reason is safe to log
    """
    spec = COMMAND_REGISTRY.get(command)
    if spec is None:
        logger.warning(f"[WHITELIST] Rejected unknown command: '{command}'")
        return False, f"Unknown command: '{command}'"

    n = len(args)
    min_a = spec.get("min_args", 0)
    max_a = spec.get("max_args", 100)

    if n < min_a:
        logger.warning(
            f"[WHITELIST] Command '{command}' needs at least {min_a} arg(s), got {n}"
        )
        return False, f"Command '{command}' requires at least {min_a} argument(s)"

    if n > max_a:
        logger.warning(
            f"[WHITELIST] Command '{command}' accepts at most {max_a} arg(s), got {n}"
        )
        return False, f"Command '{command}' accepts at most {max_a} argument(s)"

    arg_types = spec.get("arg_types")
    if arg_types:
        for i, (arg, expected_type) in enumerate(zip(args, arg_types)):
            if expected_type is int:
                try:
                    int(arg)
                except (ValueError, TypeError):
                    logger.warning(
                        f"[WHITELIST] Command '{command}' arg[{i}] expected int, got {arg!r}"
                    )
                    return False, f"Argument {i + 1} for command '{command}' must be a number"

    return True, "OK"
