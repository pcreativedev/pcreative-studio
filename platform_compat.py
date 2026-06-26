"""Cross-platform compatibility helpers.

Pcreative Studio was developed on Linux and has Linux-specific assumptions
(bash, xdg-open, konsole, dolphin, ~/.config/, …) baked into many
places. This module centralises those concerns so the rest of the
codebase can call platform-agnostic helpers.

Supported platforms:
- **Linux** (primary): KDE/Plasma + GNOME + others; falls back through
  a list of common tools (dolphin → nautilus → nemo → thunar → xdg-open).
- **macOS** (in progress): uses `open` for file manager and
  `Terminal.app` for terminal, `zsh -lc` for shell.
- **Windows** (backlog): basic dispatch only.

Each helper returns the spawned `subprocess.Popen` (or None on error)
so callers can chain / await if needed.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

IS_LINUX = sys.platform.startswith("linux")
IS_MACOS = sys.platform == "darwin"
IS_WINDOWS = sys.platform.startswith("win")


def shell_argv(cmd_str: str) -> list[str]:
    """Returns argv to execute `cmd_str` through a login shell.

    - Linux: `bash -lc <cmd>` — bash is the default everywhere.
    - macOS: `zsh -lc <cmd>` — zsh has been the default shell since
      macOS Catalina (10.15, 2019). Most users' PATH and homebrew
      env live in `~/.zshrc` / `~/.zprofile`, not bash dotfiles.
    - Windows: `cmd /c <cmd>` — bash is unavailable by default
      (without WSL); cmd is the universally-present shell.
    """
    if IS_WINDOWS:
        return ["cmd", "/c", cmd_str]
    if IS_MACOS:
        return ["zsh", "-lc", cmd_str]
    return ["bash", "-lc", cmd_str]


def shell_program_and_args(cmd_str: str) -> tuple[str, list[str]]:
    """Same as `shell_argv` but returns (program, args) — matches the
    signature of `QProcess.start(program, args)`."""
    argv = shell_argv(cmd_str)
    return argv[0], argv[1:]


def open_in_file_manager(path: Path | str) -> subprocess.Popen | None:
    """Reveal `path` in the OS native file manager.

    - macOS: `open <path>` (opens in Finder; folders open as windows).
    - Windows: `explorer <path>`.
    - Linux: tries dolphin → nautilus → nemo → thunar → xdg-open.

    Returns the spawned Popen or None if no opener found.
    """
    p = str(path)
    if IS_MACOS:
        return subprocess.Popen(["open", p])
    if IS_WINDOWS:
        return subprocess.Popen(["explorer", p])
    for opener in ("dolphin", "nautilus", "nemo", "thunar", "xdg-open"):
        if shutil.which(opener):
            return subprocess.Popen([opener, p])
    return None


def open_url(url: str) -> None:
    """Open `url` in the default browser. Uses Python's stdlib
    `webbrowser` module which is already cross-platform."""
    import webbrowser
    webbrowser.open(url)


def open_in_terminal(cwd: Path | str, command: str | None = None,
                     hold: bool = True) -> subprocess.Popen | None:
    """Open a new terminal window at `cwd`. If `command` is given,
    runs it (with `hold` keeping the window open after exit).

    - macOS: opens Terminal.app via `open -a Terminal <cwd>`; if a
      command is given, uses osascript to execute it.
    - Windows: opens Windows Terminal if available, falls back to cmd.
    - Linux: tries konsole → gnome-terminal → kitty → alacritty → xterm.

    Returns the spawned Popen or None.
    """
    cwd_s = str(cwd)

    if IS_MACOS:
        if command:
            # osascript needs the command quoted carefully
            escaped = command.replace('"', r'\"')
            script = (
                f'tell application "Terminal" to do script '
                f'"cd {cwd_s}; {escaped}"'
            )
            return subprocess.Popen(["osascript", "-e", script])
        return subprocess.Popen(["open", "-a", "Terminal", cwd_s])

    if IS_WINDOWS:
        if shutil.which("wt"):  # Windows Terminal
            cmd_str = f"cd /d {cwd_s}"
            if command:
                cmd_str += f" && {command}"
                if hold:
                    cmd_str += " && pause"
            return subprocess.Popen(["wt", "cmd", "/k", cmd_str])
        # Fallback: cmd.exe in new window
        full = f"cd /d {cwd_s}"
        if command:
            full += f" && {command}"
        return subprocess.Popen(["start", "cmd", "/k" if hold else "/c", full],
                                shell=True)

    # Linux
    for term in ("konsole", "gnome-terminal", "kitty", "alacritty", "xterm"):
        if not shutil.which(term):
            continue
        if term == "konsole":
            args = [term, "--workdir", cwd_s]
            if hold:
                args.append("--hold")
            if command:
                args += ["-e", "bash", "-c", command]
            return subprocess.Popen(args)
        if term == "gnome-terminal":
            args = [term, "--working-directory", cwd_s]
            if command:
                args += ["--", "bash", "-c",
                         command + ("; exec bash" if hold else "")]
            return subprocess.Popen(args)
        if term in ("kitty", "alacritty"):
            args = [term, "--working-directory", cwd_s]
            if command:
                args += ["bash", "-c",
                         command + ("; exec bash" if hold else "")]
            return subprocess.Popen(args)
        if term == "xterm":
            args = [term]
            if command:
                cmd_full = command + ("; bash" if hold else "")
                args += ["-e", "bash", "-c", cmd_full]
            return subprocess.Popen(args, cwd=cwd_s)
    return None


def vscode_argv(path: Path | str) -> list[str] | None:
    """Returns argv to launch VS Code at `path`. Tries `code` binary
    first; on macOS falls back to `open -a "Visual Studio Code"`.

    Returns None if VS Code isn't installed.
    """
    p = str(path)
    if shutil.which("code"):
        return ["code", p]
    if IS_MACOS:
        # On macOS the `code` CLI requires the user to run "Shell
        # Command: Install 'code' command in PATH" from VS Code. If
        # they haven't, fall back to opening the .app directly.
        if Path("/Applications/Visual Studio Code.app").is_dir():
            return ["open", "-a", "Visual Studio Code", p]
    if IS_WINDOWS:
        # Common default install paths
        candidates = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Microsoft VS Code" / "Code.exe",
            Path("C:/Program Files/Microsoft VS Code/Code.exe"),
        ]
        for c in candidates:
            if c.is_file():
                return [str(c), p]
    return None


def app_config_dir(app_name: str = "themeforge") -> Path:
    """OS-appropriate per-user config directory for the app.

    - Linux: `$XDG_CONFIG_HOME/<app>` or `~/.config/<app>`.
    - macOS: `~/Library/Application Support/<app>`.
    - Windows: `%APPDATA%/<app>` (Roaming).

    Note: until a full migration sweep, most of Pcreative Studio still
    writes to `~/.config/themeforge/` directly. This helper exists
    for new code to do the right thing.
    """
    if IS_MACOS:
        return Path.home() / "Library" / "Application Support" / app_name
    if IS_WINDOWS:
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / app_name
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / app_name


def app_cache_dir(app_name: str = "themeforge") -> Path:
    """OS-appropriate per-user cache directory."""
    if IS_MACOS:
        return Path.home() / "Library" / "Caches" / app_name
    if IS_WINDOWS:
        base = os.environ.get("LOCALAPPDATA") or str(Path.home())
        return Path(base) / app_name / "Cache"
    xdg = os.environ.get("XDG_CACHE_HOME")
    base = Path(xdg) if xdg else Path.home() / ".cache"
    return base / app_name


def platform_label() -> str:
    """Returns a short label for the current platform — useful for
    diagnostics and conditional UI."""
    if IS_MACOS:
        return "macOS"
    if IS_WINDOWS:
        return "Windows"
    return "Linux"


def kill_processes_under_path(path_substr: str) -> int:
    """Best-effort kill of all processes whose command line contains
    `path_substr`. Used to stop a running binary before uninstalling it.

    - Linux/macOS: `pkill -f <substr>` (kills any matching process).
    - Windows: enumerates processes via WMIC/PowerShell and kills any
      whose ExecutablePath or CommandLine contains the substring.

    Returns the exit code (0 if at least one killed, non-zero if none
    matched or the command failed). Never raises.
    """
    try:
        if IS_WINDOWS:
            # PowerShell one-liner: enumerate, filter, stop.
            ps = (
                f"Get-Process | Where-Object {{ $_.Path -and "
                f"$_.Path -like '*{path_substr}*' }} | Stop-Process -Force"
            )
            return subprocess.call(
                ["powershell", "-NoProfile", "-Command", ps],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        return subprocess.call(
            ["pkill", "-f", path_substr],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except Exception:
        return 1


def secure_file_chmod(path: Path | str) -> None:
    """Best-effort `chmod 0600` (user-only read/write) for a sensitive
    file like an API keys store. On Windows this is a no-op — the file
    inherits ACLs from its parent directory (typically %APPDATA% which
    is already user-only). Linux and macOS get the real chmod.
    """
    if IS_WINDOWS:
        return
    try:
        import stat
        os.chmod(str(path), stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass


def secure_dir_chmod(path: Path | str) -> None:
    """Best-effort `chmod 0700` (user-only access) for a sensitive
    directory. No-op on Windows (parent ACLs apply)."""
    if IS_WINDOWS:
        return
    try:
        os.chmod(str(path), 0o700)
    except Exception:
        pass
