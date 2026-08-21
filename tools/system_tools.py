import os
import platform
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    psutil = None
    HAS_PSUTIL = False

from typing import Dict, Any
from .base import BaseTool

class SystemStatsTool(BaseTool):
    @property
    def name(self) -> str:
        return "get_system_stats"

    @property
    def description(self) -> str:
        return "Retrieves real-time CPU, RAM, OS details, and disk usage stats of the host device."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "detailed": {
                    "type": "boolean",
                    "description": "Whether to return detailed system statistics."
                }
            },
            "required": []
        }

    def execute(self, detailed: bool = False) -> Dict[str, Any]:
        if HAS_PSUTIL:
            mem = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent(interval=0.5)
            disk = psutil.disk_usage(os.getcwd() if os.path.exists(os.getcwd()) else "/")

            # Battery status collection
            battery_info = None
            try:
                battery = psutil.sensors_battery()
                if battery:
                    battery_info = {
                        "percent": battery.percent,
                        "power_plugged": battery.power_plugged,
                        "secs_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else "unlimited"
                    }
            except Exception:
                battery_info = "Not available"

            stats = {
                "os": f"{platform.system()} {platform.release()}",
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_gb": round(mem.total / (1024**3), 2),
                    "used_gb": round(mem.used / (1024**3), 2),
                    "free_mb": round(mem.available / (1024**2), 2),
                    "percent": mem.percent
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "percent": disk.percent
                },
                "battery": battery_info
            }

            if detailed:
                try:
                    stats["cpu_count"] = psutil.cpu_count(logical=True)
                    stats["cpu_freq_mhz"] = psutil.cpu_freq().current if psutil.cpu_freq() else None
                except Exception:
                    pass

            return stats
        else:
            return {
                "os": f"{platform.system()} {platform.release()} ({platform.architecture()[0]})",
                "processor": platform.processor(),
                "status": "psutil not installed (running in standard library mode)"
            }


class FileSystemTool(BaseTool):
    @property
    def name(self) -> str:
        return "list_directory"

    @property
    def description(self) -> str:
        return "Lists files and subdirectories inside a specified folder."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "directory_path": {
                    "type": "string",
                    "description": "Target folder absolute or relative path."
                }
            },
            "required": ["directory_path"]
        }

    def execute(self, directory_path: str) -> Dict[str, Any]:
        if not os.path.exists(directory_path):
            return {"error": f"Path '{directory_path}' does not exist."}

        try:
            items = os.listdir(directory_path)
            return {"directory": directory_path, "items": items[:30], "count": len(items)}
        except Exception as e:
            return {"error": str(e)}

from enum import Enum
import subprocess

class AllowedApplication(str, Enum):
    NOTEPAD = "notepad"
    CALCULATOR = "calculator"
    EXPLORER = "explorer"
    CMD = "cmd"
    CAMERA = "camera"
    BROWSER = "browser"
    CHROME = "chrome"
    EDGE = "edge"
    FIREFOX = "firefox"
    BRAVE = "brave"

APP_COMMAND_MAP = {
    AllowedApplication.NOTEPAD: "notepad.exe",
    AllowedApplication.CALCULATOR: "calc.exe",
    AllowedApplication.EXPLORER: "explorer.exe",
    AllowedApplication.CMD: "cmd.exe",
    AllowedApplication.CAMERA: "microsoft.windows.camera:",
    AllowedApplication.BROWSER: "browser",
    AllowedApplication.CHROME: "chrome",
    AllowedApplication.EDGE: "msedge",
    AllowedApplication.FIREFOX: "firefox",
    AllowedApplication.BRAVE: "brave",
}

APP_ALIAS_MAP = {
    "notepad": AllowedApplication.NOTEPAD,
    "notepad app": AllowedApplication.NOTEPAD,
    "notepad application": AllowedApplication.NOTEPAD,
    "text editor": AllowedApplication.NOTEPAD,
    "notes": AllowedApplication.NOTEPAD,

    "calculator": AllowedApplication.CALCULATOR,
    "calculator app": AllowedApplication.CALCULATOR,
    "calculator application": AllowedApplication.CALCULATOR,
    "calc": AllowedApplication.CALCULATOR,

    "explorer": AllowedApplication.EXPLORER,
    "file manager": AllowedApplication.EXPLORER,
    "file_manager": AllowedApplication.EXPLORER,
    "file explorer": AllowedApplication.EXPLORER,
    "files": AllowedApplication.EXPLORER,
    "my files": AllowedApplication.EXPLORER,
    "my computer": AllowedApplication.EXPLORER,
    "this pc": AllowedApplication.EXPLORER,
    "folders": AllowedApplication.EXPLORER,

    "cmd": AllowedApplication.CMD,
    "command prompt": AllowedApplication.CMD,
    "terminal": AllowedApplication.CMD,

    "camera": AllowedApplication.CAMERA,
    "camera app": AllowedApplication.CAMERA,
    "camera application": AllowedApplication.CAMERA,
    "cam": AllowedApplication.CAMERA,
    "webcam": AllowedApplication.CAMERA,

    "chrome": AllowedApplication.CHROME,
    "google chrome": AllowedApplication.CHROME,
    "chrome browser": AllowedApplication.CHROME,
    "google chrome browser": AllowedApplication.CHROME,

    "edge": AllowedApplication.EDGE,
    "msedge": AllowedApplication.EDGE,
    "microsoft edge": AllowedApplication.EDGE,

    "firefox": AllowedApplication.FIREFOX,
    "mozilla firefox": AllowedApplication.FIREFOX,

    "brave": AllowedApplication.BRAVE,
    "brave browser": AllowedApplication.BRAVE,

    "browser": AllowedApplication.BROWSER,
    "web browser": AllowedApplication.BROWSER,
    "internet browser": AllowedApplication.BROWSER,
    "internet": AllowedApplication.BROWSER,
}

class OpenApplicationTool(BaseTool):
    @property
    def name(self) -> str:
        return "open_application"

    @property
    def description(self) -> str:
        return "Safely opens a whitelisted application on the system (e.g. camera, explorer/file manager, notepad, calculator, chrome, edge, firefox, brave, browser)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Name or alias of the application to launch (e.g., 'camera', 'file manager', 'notepad', 'calculator', 'chrome', 'edge', 'browser')."
                }
            },
            "required": ["app_name"]
        }

    def execute(self, app_name: str) -> Dict[str, Any]:
        key = app_name.strip().lower()
        allowed_app = APP_ALIAS_MAP.get(key)

        if not allowed_app:
            # Fallback substring match
            for alias, mapped_app in APP_ALIAS_MAP.items():
                if alias in key or key in alias:
                    allowed_app = mapped_app
                    break

        if not allowed_app:
            try:
                allowed_app = AllowedApplication(key)
            except ValueError:
                return {
                    "error": f"Application '{app_name}' is not in the allowed whitelist."
                }

        if allowed_app == AllowedApplication.CHROME:
            try:
                os.system("start chrome")
                return {"status": "success", "message": "Successfully launched Google Chrome"}
            except Exception as e:
                return {"error": f"Failed to launch Google Chrome: {e}"}

        if allowed_app == AllowedApplication.EDGE:
            try:
                os.system("start msedge")
                return {"status": "success", "message": "Successfully launched Microsoft Edge"}
            except Exception as e:
                return {"error": f"Failed to launch Microsoft Edge: {e}"}

        if allowed_app == AllowedApplication.FIREFOX:
            try:
                os.system("start firefox")
                return {"status": "success", "message": "Successfully launched Mozilla Firefox"}
            except Exception as e:
                return {"error": f"Failed to launch Firefox: {e}"}

        if allowed_app == AllowedApplication.BRAVE:
            try:
                os.system("start brave")
                return {"status": "success", "message": "Successfully launched Brave Browser"}
            except Exception as e:
                return {"error": f"Failed to launch Brave: {e}"}

        if allowed_app == AllowedApplication.BROWSER:
            return OpenBrowserTool().execute("https://www.google.com")

        cmd = APP_COMMAND_MAP[allowed_app]
        try:
            if cmd.startswith("microsoft.windows.") or cmd.endswith(":"):
                os.system(f"start {cmd}")
                return {
                    "status": "success",
                    "message": f"Successfully launched {allowed_app.value}"
                }
            elif allowed_app == AllowedApplication.EXPLORER:
                os.system("start explorer")
                return {
                    "status": "success",
                    "message": "Successfully launched File Explorer"
                }
            else:
                proc = subprocess.Popen([cmd], shell=False)
                return {
                    "status": "success",
                    "message": f"Successfully launched {allowed_app.value}",
                    "pid": proc.pid
                }
        except Exception as e:
            return {"error": f"Failed to launch application '{allowed_app.value}': {str(e)}"}

import shutil

class OrganizeFolderTool(BaseTool):
    def __init__(self, base_sandbox_dir: str = None):
        if base_sandbox_dir:
            self.base_sandbox_dir = os.path.abspath(base_sandbox_dir)
        else:
            self.base_sandbox_dir = os.path.abspath(os.getcwd())

    @property
    def name(self) -> str:
        return "organize_folder"

    @property
    def description(self) -> str:
        return "Organizes files in a target directory into extension-based subfolders (e.g. Documents, Images). Protected by path-traversal guards."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "folder_path": {
                    "type": "string",
                    "description": "Target directory path relative or absolute inside the sandboxed workspace."
                }
            },
            "required": ["folder_path"]
        }

    def _is_safe_path(self, target_path: str) -> bool:
        """Enforces path-traversal guard to keep file operations strictly within the sandboxed base directory."""
        resolved_base = os.path.realpath(self.base_sandbox_dir)
        resolved_target = os.path.realpath(target_path)
        return os.path.commonpath([resolved_base]) == os.path.commonpath([resolved_base, resolved_target])

    def execute(self, folder_path: str) -> Dict[str, Any]:
        target_abs = os.path.abspath(os.path.join(self.base_sandbox_dir, folder_path)) if not os.path.isabs(folder_path) else os.path.abspath(folder_path)

        # Path-traversal security check
        if not self._is_safe_path(target_abs):
            return {
                "error": f"Security Exception: Path '{folder_path}' attempts path-traversal outside base sandbox directory '{self.base_sandbox_dir}'."
            }

        if not os.path.exists(target_abs) or not os.path.isdir(target_abs):
            return {"error": f"Target path '{folder_path}' does not exist or is not a directory."}

        CATEGORY_MAP = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
            "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".csv", ".md"],
            "Archives": [".zip", ".tar", ".gz", ".7z", ".rar"],
            "Audio": [".mp3", ".wav", ".flac", ".m4a"],
            "Video": [".mp4", ".mkv", ".mov", ".avi"],
            "Code": [".py", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".yml"]
        }

        moved_count = 0
        details = []

        try:
            for item in os.listdir(target_abs):
                item_path = os.path.join(target_abs, item)

                if os.path.isdir(item_path):
                    continue

                _, ext = os.path.splitext(item)
                ext = ext.lower()

                if not ext:
                    dest_folder_name = "Others"
                else:
                    dest_folder_name = "Others"
                    for category, extensions in CATEGORY_MAP.items():
                        if ext in extensions:
                            dest_folder_name = category
                            break

                dest_dir = os.path.join(target_abs, dest_folder_name)
                os.makedirs(dest_dir, exist_ok=True)

                dest_path = os.path.join(dest_dir, item)
                shutil.move(item_path, dest_path)
                moved_count += 1
                details.append({"file": item, "destination": dest_folder_name})

            return {
                "status": "success",
                "target_directory": target_abs,
                "files_organized": moved_count,
                "details": details
            }
        except Exception as e:
            return {"error": f"Failed to organize folder: {str(e)}"}

from pathlib import Path

class MoveFileTool(BaseTool):
    def __init__(self, base_sandbox_dir: str = None):
        if base_sandbox_dir:
            self.base_sandbox_dir = Path(base_sandbox_dir).resolve()
        else:
            self.base_sandbox_dir = Path.cwd().resolve()

    @property
    def name(self) -> str:
        return "move_file"

    @property
    def description(self) -> str:
        return "Safely moves a file from source_path to destination_path within the sandboxed base directory."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "source_path": {
                    "type": "string",
                    "description": "Source file path to move."
                },
                "destination_path": {
                    "type": "string",
                    "description": "Destination file or folder path."
                }
            },
            "required": ["source_path", "destination_path"]
        }

    def _is_relative_to_sandbox(self, target_path: Path) -> bool:
        """Enforces pathlib.Path.is_relative_to check to ensure paths stay within the sandboxed workspace."""
        try:
            resolved_target = target_path.resolve()
            return resolved_target.is_relative_to(self.base_sandbox_dir)
        except (ValueError, Exception):
            return False

    def execute(self, source_path: str, destination_path: str) -> Dict[str, Any]:
        src = Path(source_path)
        if not src.is_absolute():
            src = self.base_sandbox_dir / src

        dst = Path(destination_path)
        if not dst.is_absolute():
            dst = self.base_sandbox_dir / dst

        # Path-traversal security check using pathlib is_relative_to()
        if not self._is_relative_to_sandbox(src):
            return {
                "error": f"Security Exception: Source path '{source_path}' is outside sandboxed directory '{self.base_sandbox_dir}'."
            }

        if not self._is_relative_to_sandbox(dst):
            return {
                "error": f"Security Exception: Destination path '{destination_path}' is outside sandboxed directory '{self.base_sandbox_dir}'."
            }

        if not src.exists():
            return {"error": f"Source file '{source_path}' does not exist."}

        try:
            if dst.is_dir():
                os.makedirs(dst, exist_ok=True)
                final_dst = dst / src.name
            else:
                os.makedirs(dst.parent, exist_ok=True)
                final_dst = dst

            moved_path = shutil.move(str(src), str(final_dst))
            return {
                "status": "success",
                "source": str(src),
                "destination": str(moved_path)
            }
        except Exception as e:
            return {"error": f"Failed to move file: {str(e)}"}

from pathlib import Path
import threading
import time

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    Observer = None
    FileSystemEventHandler = object
    HAS_WATCHDOG = False

TARGET_EXTENSIONS = {".exe", ".msi", ".zip", ".tar", ".gz", ".7z", ".rar"}

class DownloadsWatchdogHandler(FileSystemEventHandler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def on_created(self, event):
        if not event.is_directory:
            ext = Path(event.src_path).suffix.lower()
            if ext in TARGET_EXTENSIONS:
                self.callback(event.src_path, "created")

    def on_moved(self, event):
        if not event.is_directory:
            ext = Path(event.dest_path).suffix.lower()
            if ext in TARGET_EXTENSIONS:
                self.callback(event.dest_path, "download_completed")

class DownloadsFolderMonitor:
    def __init__(self, folder_path: str = None, callback=None):
        if folder_path:
            self.folder_path = Path(folder_path).resolve()
        else:
            self.folder_path = Path.home() / "Downloads"

        self.callback = callback or self._default_event_logger
        self.running = False
        self.observer = None
        self._thread = None
        self._seen_files = set()

    def _default_event_logger(self, file_path: str, event_type: str):
        print(f" 🚨 [Downloads Monitor Event] Detected new file ({event_type}): {file_path}")

    def start(self):
        if self.running:
            return

        self.running = True
        if not self.folder_path.exists():
            self.folder_path.mkdir(parents=True, exist_ok=True)

        if HAS_WATCHDOG:
            handler = DownloadsWatchdogHandler(self.callback)
            self.observer = Observer()
            self.observer.schedule(handler, str(self.folder_path), recursive=False)
            self.observer.start()
            print(f" 📡 [Downloads Watchdog] Active watchdog monitoring on: {self.folder_path}")
        else:
            # Polling fallback mode
            self._seen_files = self._scan_existing_target_files()
            self._thread = threading.Thread(target=self._polling_loop, daemon=True)
            self._thread.start()
            print(f" 📡 [Downloads Monitor] Active polling monitoring fallback on: {self.folder_path}")

    def _scan_existing_target_files(self) -> set:
        files = set()
        if self.folder_path.exists():
            for p in self.folder_path.iterdir():
                if p.is_file() and p.suffix.lower() in TARGET_EXTENSIONS:
                    files.add(str(p.resolve()))
        return files

    def _polling_loop(self):
        while self.running:
            time.sleep(2)
            current_files = self._scan_existing_target_files()
            new_files = current_files - self._seen_files
            for nf in new_files:
                self.callback(nf, "created_polling")
            self._seen_files = current_files

    def stop(self):
        self.running = False
        if HAS_WATCHDOG and self.observer:
            self.observer.stop()
            self.observer.join()
            print(" 🛑 [Downloads Watchdog] Watchdog stopped.")
        elif self._thread:
            print(" 🛑 [Downloads Monitor] Polling monitor stopped.")

import hashlib

class InspectDownloadedFileTool(BaseTool):
    def __init__(self, base_sandbox_dir: str = None):
        if base_sandbox_dir:
            self.base_sandbox_dir = Path(base_sandbox_dir).resolve()
        else:
            self.base_sandbox_dir = Path.cwd().resolve()

    @property
    def name(self) -> str:
        return "inspect_downloaded_file"

    @property
    def description(self) -> str:
        return "Inspects a downloaded file by calculating cryptographic hashes (SHA-256, MD5), inspecting file type/extension, and checking digital signatures without executing the file."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Target downloaded file path to inspect."
                }
            },
            "required": ["file_path"]
        }

    def _calculate_hashes(self, target_path: Path) -> Dict[str, str]:
        sha256 = hashlib.sha256()
        md5 = hashlib.md5()
        with open(target_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
                md5.update(chunk)
        return {
            "sha256": sha256.hexdigest(),
            "md5": md5.hexdigest()
        }

    def _check_windows_signature(self, target_path: Path) -> Dict[str, Any]:
        """Inspects digital signature of Windows binaries using PowerShell Get-AuthenticodeSignature without executing the binary."""
        if platform.system() != "Windows":
            return {"status": "Unsupported platform for Authenticode signature check"}

        try:
            ps_command = f"Get-AuthenticodeSignature '{target_path}' | Select-Object Status, StatusMessage, @{{Name='SignerCertificate';Expression={{$_.SignerCertificate.Subject}}}} | ConvertTo-Json"
            proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_command], capture_output=True, text=True, timeout=10)
            if proc.returncode == 0 and proc.stdout.strip():
                sig_info = json.loads(proc.stdout)
                return {
                    "signature_status": sig_info.get("Status"),
                    "status_message": sig_info.get("StatusMessage"),
                    "signer_certificate": sig_info.get("SignerCertificate")
                }
            else:
                return {"signature_status": "Unsigned or error reading signature", "details": proc.stderr.strip()}
        except Exception as e:
            return {"signature_status": "Error checking signature", "error": str(e)}

    def execute(self, file_path: str) -> Dict[str, Any]:
        target = Path(file_path)
        if not target.is_absolute():
            target = self.base_sandbox_dir / target

        target = target.resolve()

        if not target.exists() or not target.is_file():
            return {"error": f"File '{file_path}' does not exist or is not a valid file."}

        file_size_bytes = target.stat().st_size
        hashes = self._calculate_hashes(target)
        sig_info = self._check_windows_signature(target)

        return {
            "status": "success",
            "file_name": target.name,
            "absolute_path": str(target),
            "size_bytes": file_size_bytes,
            "extension": target.suffix.lower(),
            "hashes": hashes,
            "digital_signature": sig_info,
            "auto_execution_prevented": True,
            "safety_note": "Inspection completed safely. File was NOT executed."
        }

class OpenFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "open_file"

    @property
    def description(self) -> str:
        return "Opens a specified file or document on the host system using default associated app."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path of the file to open."
                }
            },
            "required": ["file_path"]
        }

    def execute(self, file_path: str) -> Dict[str, Any]:
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            return {"error": f"File '{file_path}' does not exist."}
        try:
            if platform.system() == "Windows":
                os.startfile(abs_path)
            else:
                subprocess.Popen(["xdg-open", abs_path])
            return {"status": "success", "message": f"Opened file '{abs_path}'"}
        except Exception as e:
            return {"error": f"Could not open file: {e}"}


class CreateFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "create_file"

    @property
    def description(self) -> str:
        return "Creates a new file with optional content."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path of the file to create."
                },
                "content": {
                    "type": "string",
                    "description": "Initial text content for the file."
                }
            },
            "required": ["file_path"]
        }

    def execute(self, file_path: str, content: str = "") -> Dict[str, Any]:
        abs_path = os.path.abspath(file_path)
        try:
            parent = os.path.dirname(abs_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "success", "message": f"Created file '{abs_path}' successfully."}
        except Exception as e:
            return {"error": f"Could not create file: {e}"}


class DeleteFileTool(BaseTool):
    @property
    def name(self) -> str:
        return "delete_file"

    @property
    def description(self) -> str:
        return "Deletes a specified file from the filesystem."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path of the file to delete."
                }
            },
            "required": ["file_path"]
        }

    def execute(self, file_path: str) -> Dict[str, Any]:
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            return {"error": f"File '{file_path}' does not exist."}
        try:
            os.remove(abs_path)
            return {"status": "success", "message": f"Deleted file '{abs_path}' successfully."}
        except Exception as e:
            return {"error": f"Could not delete file: {e}"}

class CloseApplicationTool(BaseTool):
    """Closes/kills a running application by name."""
    @property
    def name(self) -> str:
        return "close_application"

    @property
    def description(self) -> str:
        return "Closes a running application by its process name."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Name of the application to close (e.g. 'camera', 'notepad', 'chrome', 'edge')."
                }
            },
            "required": ["app_name"]
        }

    PROCESS_NAME_MAP = {
        "camera": "WindowsCamera",
        "camera app": "WindowsCamera",
        "camera application": "WindowsCamera",
        "webcam": "WindowsCamera",
        "cam": "WindowsCamera",
        "notepad": "notepad",
        "notepad app": "notepad",
        "text editor": "notepad",
        "notes": "notepad",
        "calculator": "CalculatorApp",
        "calculator app": "CalculatorApp",
        "calc": "CalculatorApp",
        "explorer": "explorer",
        "file manager": "explorer",
        "file explorer": "explorer",
        "files": "explorer",
        "chrome": "chrome",
        "edge": "msedge",
        "msedge": "msedge",
        "firefox": "firefox",
        "brave": "brave",
        "browser": "msedge",
        "web browser": "msedge",
    }

    def execute(self, app_name: str) -> Dict[str, Any]:
        key = app_name.strip().lower()
        if key in ["browser", "web browser", "internet browser"]:
            # Close common browsers
            if platform.system() == "Windows":
                creationflags = 0x08000000
                for b in ["msedge", "chrome", "firefox", "brave"]:
                    subprocess.run(["taskkill", "/IM", f"{b}.exe", "/F"], capture_output=True, creationflags=creationflags, timeout=3)
            return {"status": "success", "message": "Closed browser."}

        proc_name = self.PROCESS_NAME_MAP.get(key, key)
        try:
            if platform.system() == "Windows":
                creationflags = 0x08000000
                subprocess.run(
                    ["taskkill", "/IM", f"{proc_name}*", "/F"],
                    capture_output=True, creationflags=creationflags, timeout=5
                )
                subprocess.run(
                    ["taskkill", "/IM", f"{proc_name}.exe", "/F"],
                    capture_output=True, creationflags=creationflags, timeout=5
                )
            return {"status": "success", "message": f"Closed application '{app_name}'."}
        except Exception as e:
            return {"error": f"Could not close '{app_name}': {e}"}


import webbrowser
import urllib.parse

class OpenBrowserTool(BaseTool):
    """Opens a web browser, optionally to a specific URL."""
    @property
    def name(self) -> str:
        return "open_browser"

    @property
    def description(self) -> str:
        return "Opens the default web browser, optionally navigating to a given URL."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to open. Defaults to google.com if not provided."
                }
            },
            "required": []
        }

    def execute(self, url: str = "") -> Dict[str, Any]:
        target = url.strip() if url else "https://www.google.com"
        if target == "about:blank":
            target = "https://www.google.com"
        if not target.startswith(("http://", "https://")):
            target = "https://" + target
        try:
            if platform.system() == "Windows":
                os.system(f'start "" "{target}"')
            else:
                webbrowser.open(target, new=2)
            return {"status": "success", "message": f"Opened browser to '{target}'."}
        except Exception as e:
            return {"error": f"Could not open browser: {e}"}


class WebSearchTool(BaseTool):
    """Searches the web using the default browser."""
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Opens a web search in the default browser for the given query."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up."
                }
            },
            "required": ["query"]
        }

    def execute(self, query: str) -> Dict[str, Any]:
        encoded = urllib.parse.quote_plus(query.strip())
        search_url = f"https://www.google.com/search?q={encoded}"
        try:
            webbrowser.open(search_url, new=2)
            return {"status": "success", "message": f"Searched for '{query}' in browser."}
        except Exception as e:
            return {"error": f"Could not perform web search: {e}"}


class TakeScreenshotTool(BaseTool):
    """Takes a screenshot of the current screen."""
    @property
    def name(self) -> str:
        return "take_screenshot"

    @property
    def description(self) -> str:
        return "Captures a screenshot of the current screen and saves it to a file."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "save_path": {
                    "type": "string",
                    "description": "File path to save the screenshot. Defaults to 'screenshot.png'."
                }
            },
            "required": []
        }

    def execute(self, save_path: str = "screenshot.png") -> Dict[str, Any]:
        if not save_path:
            save_path = "screenshot.png"
        abs_path = os.path.abspath(save_path)
        try:
            from PIL import ImageGrab
            img = ImageGrab.grab()
            img.save(abs_path)
            return {"status": "success", "message": f"Screenshot saved to '{abs_path}'."}
        except ImportError:
            return {"error": "PIL/Pillow is required for screenshots. Install with: pip install Pillow"}
        except Exception as e:
            return {"error": f"Could not take screenshot: {e}"}


class OpenBrowserTabTool(BaseTool):
    """Opens a new tab in the default browser to a URL."""
    @property
    def name(self) -> str:
        return "open_new_tab"

    @property
    def description(self) -> str:
        return "Opens a new browser tab to the specified URL."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to open in a new tab."
                }
            },
            "required": ["url"]
        }

    def execute(self, url: str) -> Dict[str, Any]:
        target = url.strip()
        if not target.startswith(("http://", "https://")):
            target = "https://" + target
        try:
            webbrowser.open_new_tab(target)
            return {"status": "success", "message": f"Opened new tab to '{target}'."}
        except Exception as e:
            return {"error": f"Could not open new tab: {e}"}


class GetScreenContextTool(BaseTool):
    """Retrieves active screen context, application info, and UI text elements instantly without capturing image files (Option 2 - Ultra-Fast & Safe)."""
    @property
    def name(self) -> str:
        return "get_screen_context"

    @property
    def description(self) -> str:
        return "Retrieves structured text information about the active window, focused application, and UI text elements instantly without taking image files."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    def execute(self) -> Dict[str, Any]:
        context = {
            "active_window_title": "Unknown",
            "process_name": "Unknown",
            "pid": None,
            "focused_element": None
        }

        if platform.system() == "Windows":
            try:
                import win32gui
                import win32process

                hwnd = win32gui.GetForegroundWindow()
                if hwnd:
                    window_title = win32gui.GetWindowText(hwnd)
                    context["active_window_title"] = window_title or "Desktop / Background"
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    context["pid"] = pid
                    if pid and HAS_PSUTIL:
                        proc = psutil.Process(pid)
                        context["process_name"] = proc.name()
            except Exception:
                try:
                    import ctypes
                    hwnd = ctypes.windll.user32.GetForegroundWindow()
                    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                    buf = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                    context["active_window_title"] = buf.value or "Active Window"
                except Exception:
                    pass

            try:
                import uiautomation as auto
                focused = auto.GetFocusedControl()
                if focused:
                    context["focused_element"] = focused.Name or focused.ControlTypeName
            except Exception:
                pass

        return {
            "status": "success",
            "message": f"Active Application: {context['process_name']} | Window Title: '{context['active_window_title']}'",
            "details": context,
            "privacy_guarantee": "0 images captured. Text-only OS metadata inspection."
        }


class AnalyzeScreenInMemoryTool(BaseTool):
    """Captures a screenshot directly in RAM (memory only, 0 bytes stored on disk) for visual inspection (Option 1)."""
    @property
    def name(self) -> str:
        return "analyze_screen_in_memory"

    @property
    def description(self) -> str:
        return "Captures the current screen directly into RAM memory buffer (0 bytes stored on disk) for in-memory visual inspection."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Question or prompt about the screen content."
                }
            },
            "required": []
        }

    def execute(self, prompt: str = "Describe what is open on the screen") -> Dict[str, Any]:
        try:
            import io
            import base64
            from PIL import ImageGrab

            # Capture directly into RAM buffer - 0 bytes on disk
            buffer = io.BytesIO()
            img = ImageGrab.grab()
            img.save(buffer, format="JPEG", quality=75)
            buffer.seek(0)

            b64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
            buffer.close()
            del img

            return {
                "status": "success",
                "message": "Screen captured in RAM (0 bytes stored on disk).",
                "image_base64_length": len(b64_data),
                "privacy_note": "Image processed entirely in RAM; no file was saved to disk."
            }
        except ImportError:
            return {"error": "PIL/Pillow is required for in-memory screen analysis."}
        except Exception as e:
            return {"error": f"Failed to capture screen in memory: {e}"}


class ToggleHandlessModeTool(BaseTool):
    """Enables or disables Handless Mode (webcam hand-gesture control)."""
    @property
    def name(self) -> str:
        return "toggle_handless_mode"

    @property
    def description(self) -> str:
        return "Enables or disables Handless Mode (camera-based hand gesture cursor & mouse control)."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "enable": {
                    "type": "boolean",
                    "description": "True to start webcam hand gesture control, False to stop and release camera."
                }
            },
            "required": ["enable"]
        }

    def execute(self, enable: bool = True) -> Dict[str, Any]:
        try:
            from Heti.gesture import HandlessGestureController
            controller = HandlessGestureController()
            if enable:
                res = controller.start()
            else:
                res = controller.stop()
            return res
        except Exception as e:
            return {"error": f"Failed to toggle Handless Mode: {e}"}


class GetGestureStatusTool(BaseTool):
    """Retrieves current status of Handless Mode camera tracking."""
    @property
    def name(self) -> str:
        return "get_gesture_status"

    @property
    def description(self) -> str:
        return "Gets current operational status, FPS, and gesture state of Handless Mode."

    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

    def execute(self) -> Dict[str, Any]:
        try:
            from Heti.gesture import HandlessGestureController
            controller = HandlessGestureController()
            return controller.get_status()
        except Exception as e:
            return {"error": f"Failed to get gesture status: {e}"}


def get_default_tools():
    return [
        SystemStatsTool(),
        FileSystemTool(),
        OpenApplicationTool(),
        CloseApplicationTool(),
        OrganizeFolderTool(),
        MoveFileTool(),
        InspectDownloadedFileTool(),
        OpenFileTool(),
        CreateFileTool(),
        DeleteFileTool(),
        OpenBrowserTool(),
        WebSearchTool(),
        TakeScreenshotTool(),
        OpenBrowserTabTool(),
        GetScreenContextTool(),
        AnalyzeScreenInMemoryTool(),
        ToggleHandlessModeTool(),
        GetGestureStatusTool()
    ]








