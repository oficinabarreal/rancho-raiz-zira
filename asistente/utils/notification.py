"""
Notification utilities for Android via termux-notification.
"""
import subprocess
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def send_notification(title: str, content: str, action: str = None) -> bool:
    """
    Send a notification using termux-notification.
    :param title: Notification title
    :param content: Notification body text
    :param action: Command to execute when notification is clicked.
                   If None, defaults to opening Termux at project root.
    :return: True if successful, False otherwise.
    """
    if action is None:
        # Default: open a new Termux session in the project directory
        action = f"termux-exec bash -c 'cd {PROJECT_ROOT} && exec bash'"
    try:
        subprocess.run(
            [
                "termux-notification",
                "--title", title,
                "--content", content,
                "--action", action,
            ],
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"Failed to send notification: {e}")
        return False


def notify_task_reminder(task: str, project: str = "hola-3") -> None:
    """
    Send a reminder notification for a pending task.
    """
    send_notification(
        title=f"Recordatorio: {project}",
        content=f"Tarea pendiente: {task}",
    )


def notify_api_available(api_name: str) -> None:
    """
    Notify that an API token is now available (no rate limit).
    """
    send_notification(
        title="API Disponible",
        content=f"El token para {api_name} ya está disponible sin límite de tasa.",
    )


def notify_process_status(process_name: str, status: str) -> None:
    """
    Notify about the status of a background process.
    """
    send_notification(
        title=f"Estado del proceso: {process_name}",
        content=status,
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python notification.py <title> <content> [action]")
        sys.exit(1)
    title = sys.argv[1]
    content = sys.argv[2] if len(sys.argv) > 2 else ""
    action = sys.argv[3] if len(sys.argv) > 3 else None
    send_notification(title, content, action)