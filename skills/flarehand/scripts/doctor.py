#!/usr/bin/env python3
"""doctor.py - look at this machine and this harness, and report what is here.

Every setup path branches off this, and the grounding step reads its capability
report to know which tools it can use. It reads only. It installs nothing,
changes nothing, and never asks you a question. It makes no network call unless
you ask for one with --check web, and then it sends one HEAD request to a neutral
host and nothing else.

Usage
  python3 scripts/doctor.py
  python3 scripts/doctor.py --capabilities
  python3 scripts/doctor.py --capabilities --check web
  python3 scripts/doctor.py --json
  python3 scripts/doctor.py --check mcp --check kb

What --capabilities reports
  OS, Python (path and version), which agent harness seems to be running, the shell,
  git, web reach (only with --check web), MCP servers configured (names only), the
  knowledge base's health, the playbooks found from this folder, and what kb.py detect
  reads: a name from git config, time zone, locale and date format.

The harness is read from environment variable NAMES, never their values. When no
known name is set, it says "unknown" rather than guess.

Exit codes: 0 everything needed is present, 1 something is missing, 2 error.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# What this skill runs on. 3.9 is the floor because macOS ships it. 3.9 stopped getting
# security fixes in October 2025, so anything under this line works but is unsupported upstream.
PYTHON_MINIMUM = (3, 9)
PYTHON_SECURITY_FLOOR = (3, 10)
TIMEOUT = 4
# A host that exists to be reached and says nothing about who reached it.
WEB_PROBE_URL = "https://example.com/"

# Environment variable names each harness sets for the commands it runs. A name counts only
# when it shows the harness is running, so keys and tokens a person exports never do.
HARNESS_SIGNS = (
    ("claude-code", ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_PLUGIN_ROOT", "CLAUDE_PROJECT_DIR"), ()),
    ("codex", ("CODEX_THREAD_ID", "CODEX_SANDBOX", "CODEX_SANDBOX_NETWORK_DISABLED", "CODEX_MANAGED_BY_NPM"),
     ("CODEX_",)),
    ("copilot", ("COPILOT_AGENT_ID", "COPILOT_CLI"), ("COPILOT_",)),
    ("cursor", ("CURSOR_AGENT", "CURSOR_TRACE_ID"), ("CURSOR_",)),
    ("gemini", ("GEMINI_CLI",), ("GEMINI_CLI_",)),
)
# Set by the person, not by a running harness.
NOT_A_SIGN = ("CODEX_HOME", "COPILOT_HOME", "GEMINI_API_KEY", "GEMINI_MODEL", "CURSOR_HOME")
SECRET_WORDS = ("KEY", "TOKEN", "SECRET", "PASSWORD")

# What each harness usually offers. "usually" because a person or an admin can turn any of
# these off, so the agent still confirms a tool exists before it relies on it.
HARNESS_USUALLY = {
    "claude-code": {"subagents": "usually", "web_search": "usually", "web_fetch": "usually", "hooks": "yes"},
    "codex": {"subagents": "unknown", "web_search": "if enabled in config", "web_fetch": "unknown",
              "hooks": "yes"},
    "copilot": {"subagents": "usually", "web_search": "unknown", "web_fetch": "usually", "hooks": "yes"},
    "cursor": {"subagents": "unknown", "web_search": "usually", "web_fetch": "unknown", "hooks": "yes"},
    "gemini": {"subagents": "unknown", "web_search": "usually", "web_fetch": "usually", "hooks": "yes"},
}


def run(cmd: list[str]) -> str | None:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=8)
        out = (r.stdout or r.stderr).strip()
        return out.split("\n")[0] if out else None
    except (OSError, subprocess.SubprocessError):
        return None


def which(name: str) -> str | None:
    return shutil.which(name)


def probe_os() -> dict:
    system = platform.system()
    info = {
        "system": system,
        "release": platform.release(),
        "version": platform.platform(),
        "arch": platform.machine(),
        "is_windows": system == "Windows",
        "is_macos": system == "Darwin",
        "is_linux": system == "Linux",
        "home": str(Path.home()),
    }
    if system == "Darwin":
        info["pretty"] = f"macOS {platform.mac_ver()[0] or platform.release()}"
    elif system == "Windows":
        info["pretty"] = f"Windows {platform.release()}"
    else:
        info["pretty"] = f"{system} {platform.release()}"
    return info


def probe_shell() -> dict:
    """The shell this was started from. On Windows, PowerShell sets PSModulePath and cmd sets COMSPEC."""
    shell = os.environ.get("SHELL", "")
    if shell:
        return {"name": Path(shell).name, "path": shell}
    if platform.system() == "Windows":
        if os.environ.get("PSModulePath") and not os.environ.get("PROMPT"):
            return {"name": "powershell", "path": which("pwsh") or which("powershell") or ""}
        return {"name": "cmd", "path": os.environ.get("COMSPEC", "")}
    return {"name": "unknown", "path": ""}


def probe_python() -> dict:
    """Find a usable interpreter. The name differs by platform, so never assume python3."""
    candidates = ["python3", "python", "py"]
    found = []
    for name in candidates:
        path = which(name)
        if not path:
            continue
        cmd = [path, "-3"] if name == "py" else [path]
        ver = run(cmd + ["-c", "import sys;print('.'.join(map(str,sys.version_info[:3])))"])
        if ver and ver[0].isdigit():
            found.append({"name": "py -3" if name == "py" else name, "path": path, "version": ver})
    running = {
        "name": Path(sys.executable).name,
        "path": sys.executable,
        "version": ".".join(str(v) for v in sys.version_info[:3]),
    }
    ok = sys.version_info >= PYTHON_MINIMUM
    windows = platform.system() == "Windows"
    return {
        "running": running,
        "found": found,
        "recommended_command": "py -3" if windows and any(f["name"] == "py -3" for f in found) else running["path"],
        "meets_minimum": ok,
        "minimum": ".".join(map(str, PYTHON_MINIMUM)),
        "gets_security_fixes": sys.version_info >= PYTHON_SECURITY_FLOOR,
        "security_floor": ".".join(map(str, PYTHON_SECURITY_FLOOR)),
    }


def probe_tools() -> dict:
    tools = {}
    for name, args in [
        ("git", ["--version"]),
        ("gh", ["--version"]),
        ("rg", ["--version"]),
        ("node", ["--version"]),
        ("claude", ["--version"]),
        ("codex", ["--version"]),
        ("copilot", ["--version"]),
        ("gemini", ["--version"]),
        ("cursor-agent", ["--version"]),
    ]:
        path = which(name)
        tools[name] = {"present": bool(path), "path": path,
                       "version": run([path] + args) if path else None}
    return tools


def probe_git(cwd: Path | None = None) -> dict:
    cwd = cwd or Path.cwd()
    path = which("git")
    info = {"present": bool(path), "version": run([path, "--version"]) if path else None,
            "in_repository": False, "top": None}
    if path:
        try:
            r = subprocess.run([path, "-C", str(cwd), "rev-parse", "--show-toplevel"],
                               capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                info["in_repository"], info["top"] = True, r.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
    return info


def detect_harness(env: dict | None = None) -> dict:
    """Which agent harness seems to be running this, from the variable names it sets.

    Conservative on purpose. One harness with a clear sign is named. Several are reported
    as several. None is "unknown". Values are never read, so nothing secret is printed."""
    env = os.environ if env is None else env
    names = [n for n in env if n not in NOT_A_SIGN and not any(w in n.upper() for w in SECRET_WORDS)]
    found = {}
    for harness, exact, prefixes in HARNESS_SIGNS:
        hits = sorted(n for n in names if n in exact or any(n.startswith(p) for p in prefixes))
        if hits:
            found[harness] = hits
    if len(found) == 1:
        name = next(iter(found))
    elif found:
        name = "several: " + ", ".join(sorted(found))
    else:
        name = "unknown"
    usually = HARNESS_USUALLY.get(name, {"subagents": "unknown", "web_search": "unknown",
                                         "web_fetch": "unknown", "hooks": "unknown"})
    return {"name": name, "evidence": found, "usually": usually}


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").expanduser()


def codex_sandbox() -> dict:
    """Whether this runs inside Codex, and what its sandbox allows. Codex sets these itself.
    Its default sandbox writes only inside the workspace and temp, and turns the network off,
    so a failure here can be the sandbox rather than the network or the knowledge base."""
    return {"codex": bool(os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SANDBOX")),
            "sandbox": os.environ.get("CODEX_SANDBOX", ""),
            "network_off": os.environ.get("CODEX_SANDBOX_NETWORK_DISABLED") == "1"}


def _toml_servers(text: str) -> dict:
    """`[mcp_servers.<name>]` tables from a Codex config.toml. tomllib when Python has it,
    otherwise just the table names and their `url` lines, which is all this check reads."""
    try:
        import tomllib
        data = tomllib.loads(text)
        servers = data.get("mcp_servers")
        return servers if isinstance(servers, dict) else {}
    except ImportError:
        pass
    except ValueError:
        return {}
    import re
    servers: dict = {}
    current = None
    for line in text.splitlines():
        head = re.match(r"^\s*\[mcp_servers\.([^\].]+)\]\s*$", line)
        if head:
            current = servers.setdefault(head.group(1).strip('"'), {})
            continue
        if line.strip().startswith("["):
            current = None
            continue
        url = re.match(r'^\s*url\s*=\s*"([^"]+)"', line)
        if current is not None and url:
            current["url"] = url.group(1)
    return servers


def _server_blocks(data: dict, cwd: Path | None = None):
    """MCP servers sit under different keys depending on the tool. Claude Code keeps a
    project's own servers under projects[<folder>], so only this folder's block is read."""
    if not isinstance(data, dict):
        return
    for key in ("mcpServers", "servers"):
        if isinstance(data.get(key), dict):
            yield data[key]
    projects = data.get("projects")
    if isinstance(projects, dict):
        for folder, project in projects.items():
            if cwd is not None and Path(str(folder)).expanduser() != cwd:
                continue
            if isinstance(project, dict) and isinstance(project.get("mcpServers"), dict):
                yield project["mcpServers"]


def mcp_config_paths(cwd: Path | None = None) -> dict[str, Path]:
    """Where each client keeps MCP servers.

    Claude Code keeps user and local scope servers in ~/.claude.json, and project scope in
    .mcp.json in the working folder. ~/.claude/settings.json holds settings, not servers.
    VS Code's user folder differs by platform, and a non-default profile keeps its own mcp.json
    under User/profiles/<id>/."""
    home = Path.home()
    cwd = cwd or Path.cwd()
    system = platform.system()
    if system == "Darwin":
        app_support = home / "Library" / "Application Support"
    elif system == "Windows":
        app_support = Path(os.environ.get("APPDATA") or home / "AppData" / "Roaming")
    else:
        app_support = Path(os.environ.get("XDG_CONFIG_HOME") or home / ".config")
    paths = {
        "claude_code": home / ".claude.json",
        "claude_code_project": cwd / ".mcp.json",
        "claude_desktop": app_support / "Claude" / "claude_desktop_config.json",
        "copilot": home / ".copilot" / "mcp-config.json",
        "codex": codex_home() / "config.toml",
        "cursor": home / ".cursor" / "mcp.json",
        "cursor_project": cwd / ".cursor" / "mcp.json",
        "gemini": home / ".gemini" / "settings.json",
        "gemini_project": cwd / ".gemini" / "settings.json",
        "vscode_project": cwd / ".vscode" / "mcp.json",
    }
    for label, folder in (("vscode", "Code"), ("vscode_insiders", "Code - Insiders")):
        paths[label] = app_support / folder / "User" / "mcp.json"
        profiles = app_support / folder / "User" / "profiles"
        if profiles.is_dir():
            for profile in sorted(profiles.iterdir()):
                if (profile / "mcp.json").is_file():
                    paths[f"{label}_profile_{profile.name}"] = profile / "mcp.json"
    return paths


def probe_mcp(cwd: Path | None = None) -> dict:
    """Server names per config file. Names only: a config can hold URLs with tokens in them."""
    cwd = (cwd or Path.cwd()).resolve()
    out = {}
    for label, path in mcp_config_paths(cwd).items():
        entry = {"path": str(path), "exists": path.is_file(), "servers": []}
        if entry["exists"]:
            try:
                text = path.read_text(encoding="utf-8-sig")
                blocks = ([_toml_servers(text)] if path.suffix == ".toml"
                          else list(_server_blocks(json.loads(text), cwd)))
                names = []
                for block in blocks:
                    names += [str(n) for n in block if str(n) not in names]
                entry["servers"] = sorted(set(names))
            except (OSError, ValueError) as e:
                entry["error"] = type(e).__name__
        out[label] = entry
    return out


def mcp_server_names(cwd: Path | None = None) -> list[str]:
    """Every MCP server name configured for this folder, in any client, once each."""
    names: list[str] = []
    for entry in probe_mcp(cwd).values():
        for n in entry["servers"]:
            if n not in names:
                names.append(n)
    return sorted(names)


def probe_web(url: str = WEB_PROBE_URL) -> dict:
    """One HEAD request. Says whether a raw fetch from this shell can reach the web at all,
    which is a different question from whether the harness has a web search tool."""
    result = {"url": url, "reachable": False, "status": None, "cause": "", "detail": ""}
    if codex_sandbox()["network_off"]:
        result["cause"] = "sandbox"
        result["detail"] = ("Codex's sandbox has the network off, so a raw fetch from the shell cannot work. "
                            "A web tool the harness provides may still work.")
        return result
    try:
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "flarehand-doctor"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            result["status"] = resp.status
    except urllib.error.HTTPError as e:
        result["status"] = e.code  # any answer proves the network path works
    except (urllib.error.URLError, OSError) as e:
        result["cause"] = "no-route"
        result["detail"] = f"no answer: {getattr(e, 'reason', e)}. A proxy, a firewall or no network."
        return result
    result["reachable"] = True
    result["detail"] = "answered"
    return result


def probe_kb() -> dict:
    root = Path.home() / ".flareware" / "flarehand"
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from kb import resolve_root
        root = resolve_root(None)
    except Exception:
        pass
    cfg = root / "config.json"
    info = {"path": str(root), "exists": root.is_dir(), "configured": cfg.is_file(), "notes": 0,
            "git_backed": (root / ".git").is_dir(), "problems": []}
    if cfg.is_file():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("config is not a JSON object")
            info["root"] = str(root)
            info["name"] = data.get("name", "")
            info["notes"] = len(list((root / "notes").rglob("*.md"))) if (root / "notes").is_dir() else 0
            info["answers"] = len(list((root / "answers").glob("*.md"))) if (root / "answers").is_dir() else 0
            info["evidence"] = len(list((root / "evidence").glob("*.txt"))) if (root / "evidence").is_dir() else 0
        except (OSError, ValueError) as e:
            info["problems"].append(f"config.json cannot be read: {e}")
        if not info["git_backed"]:
            info["problems"].append("no git history, so a write cannot be undone")
        if (root / ".index" / ".lock").is_file():
            info["problems"].append("a lock file is present. A command may be running, or one stopped part way")
    return info


def probe_detected() -> dict:
    """Name from git, time zone, locale, date format and OS, from kb.py's own detect, so first run
    step 1 is one command. Read only. An employer is never guessed from an email or a remote."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from kb import detect_profile
        return detect_profile()
    except Exception as e:  # kb.py missing or changed: say so rather than fail the whole report
        return {"error": f"could not read it: {type(e).__name__}"}


def probe_playbooks(cwd: Path | None = None) -> dict:
    cwd = (cwd or Path.cwd()).resolve()
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import layers
        found = [{"name": p.name, "path": str(p.path), "origin": p.origin, "parent": p.parent}
                 for p in layers.playbooks(cwd)]
        return {"found": found, "how": "layers.py"}
    except Exception:
        pass
    # Without layers.py, the repository's own .flarehand folder is still worth naming.
    found = []
    for folder in [cwd, *cwd.parents]:
        if (folder / ".flarehand").is_dir():
            found.append({"name": folder.name, "path": str(folder / ".flarehand"), "origin": "repo", "parent": None})
            break
        if (folder / ".git").exists():
            break
    return {"found": found, "how": "folder scan"}


def probe_skills() -> dict:
    home = Path.home()
    return {
        "claude_personal": {"path": str(home / ".claude" / "skills"), "exists": (home / ".claude" / "skills").is_dir()},
        "copilot_personal": {"path": str(home / ".copilot" / "skills"), "exists": (home / ".copilot" / "skills").is_dir()},
        "agents_personal": {"path": str(home / ".agents" / "skills"), "exists": (home / ".agents" / "skills").is_dir()},
        "codex_personal": {"path": str(codex_home() / "skills"), "exists": (codex_home() / "skills").is_dir()},
        "claude_project": {"path": ".claude/skills", "exists": Path(".claude/skills").is_dir()},
        "github_project": {"path": ".github/skills", "exists": Path(".github/skills").is_dir()},
        "agents_project": {"path": ".agents/skills", "exists": Path(".agents/skills").is_dir()},
    }


ALL_CHECKS = ["os", "python", "shell", "harness", "tools", "git", "mcp", "kb", "playbooks", "skills", "detect"]
CAPABILITY_CHECKS = ["os", "python", "shell", "harness", "git", "mcp", "kb", "playbooks", "detect"]


def collect(checks: list[str]) -> dict:
    """The web probe runs only when "web" is in checks, which only --check web puts there."""
    report: dict = {}
    if "os" in checks:
        report["os"] = probe_os()
    if "python" in checks:
        report["python"] = probe_python()
    if "shell" in checks:
        report["shell"] = probe_shell()
    if "harness" in checks:
        report["harness"] = detect_harness()
    if "tools" in checks:
        report["tools"] = probe_tools()
    if "git" in checks:
        report["git"] = probe_git()
    sandbox = codex_sandbox()
    if sandbox["codex"]:
        report["codex_sandbox"] = sandbox
    if "mcp" in checks:
        report["mcp"] = probe_mcp()
    if "web" in checks:
        report["web"] = probe_web()
    if "kb" in checks:
        report["knowledge_base"] = probe_kb()
    if "playbooks" in checks:
        report["playbooks"] = probe_playbooks()
    if "skills" in checks:
        report["skill_folders"] = probe_skills()
    if "detect" in checks:
        report["detected"] = probe_detected()
    return report


def capabilities(report: dict) -> dict:
    """What the grounding step can use, in one place."""
    h = report.get("harness", {})
    usually = h.get("usually", {})
    web = report.get("web")
    git = report.get("git", {})
    servers = sorted({n for e in report.get("mcp", {}).values() for n in e.get("servers", [])})
    return {
        "shell": True,  # this ran, so there is one
        "python": report.get("python", {}).get("recommended_command"),
        "git": bool(git.get("present")),
        "git_repository": git.get("top"),
        "raw_fetch": (web["reachable"] if web else "not checked, run with --check web"),
        "web_search": usually.get("web_search", "unknown"),
        "subagents": usually.get("subagents", "unknown"),
        "mcp_servers": servers,
        "knowledge_base": bool(report.get("knowledge_base", {}).get("configured")),
        "playbooks": [p["name"] for p in report.get("playbooks", {}).get("found", [])],
    }


def blockers(report: dict) -> list[str]:
    out = []
    py = report.get("python")
    if py and not py["meets_minimum"]:
        out.append(f"Python {py['minimum']} or newer is needed. Read references/setup-python.md.")
    kb = report.get("knowledge_base")
    if kb and not kb["configured"]:
        out.append(f"No knowledge base yet. Run: {Path(sys.executable).name} scripts/kb.py init")
    git = report.get("git")
    tools = report.get("tools", {})
    if (git and not git.get("present")) or (tools and not tools.get("git", {}).get("present")):
        out.append("git is not installed. The history moves and the knowledge base's undo need it.")
    return out


def render(report: dict, caps: bool = False) -> str:
    L = []
    if "os" in report:
        o = report["os"]
        L.append(f"Machine     {o['pretty']}  ({o['arch']})")
    if "python" in report:
        p = report["python"]
        mark = "ok" if p["meets_minimum"] else "too old"
        L.append(f"Python      {p['running']['version']} at {p['running']['path']}  [{mark}, minimum {p['minimum']}]")
        others = ", ".join(f"{f['name']} {f['version']}" for f in p["found"]) or "none on PATH"
        L.append(f"            also on PATH: {others}")
        if p["recommended_command"] == "py -3":
            L.append("            On Windows, run the scripts with: py -3 scripts/<name>.py")
        if p["meets_minimum"] and not p.get("gets_security_fixes", True):
            L.append(f"            This version works, but Python no longer gives it security fixes. "
                     f"Move to {p['security_floor']} or newer when you can.")
    if "shell" in report:
        L.append(f"Shell       {report['shell']['name']}")
    if "harness" in report:
        h = report["harness"]
        why = "; ".join(f"{k}: {', '.join(v)}" for k, v in h["evidence"].items())
        L.append(f"Harness     {h['name']}" + (f"  (from {why})" if why else "  (no known variable is set)"))
    if "tools" in report:
        present = [n for n, t in report["tools"].items() if t["present"]]
        absent = [n for n, t in report["tools"].items() if not t["present"]]
        L.append(f"Installed   {', '.join(present) or 'none'}")
        if absent:
            L.append(f"Not found   {', '.join(absent)}  (optional: only git is required)")
    if "git" in report:
        g = report["git"]
        where = f", inside {g['top']}" if g["in_repository"] else ", not inside a repository here"
        L.append(f"git         {g['version'] or 'not installed'}{where if g['present'] else ''}")
    if "codex_sandbox" in report:
        c = report["codex_sandbox"]
        L.append(f"Codex       running inside Codex{', sandbox ' + c['sandbox'] if c['sandbox'] else ''}"
                 f"{', network off' if c['network_off'] else ''}. The knowledge base is outside the "
                 f"workspace, so writing to it needs approval.")
    if "mcp" in report:
        names = sorted({n for e in report["mcp"].values() for n in e["servers"]})
        L.append(f"MCP         {', '.join(names) if names else 'no server configured in the files read'}")
    if "web" in report:
        w = report["web"]
        state = "reachable" if w["reachable"] else "NOT reachable"
        L.append(f"Web         {state} from this shell ({w['detail']}). One HEAD to {w['url']}, nothing else sent.")
    if "knowledge_base" in report:
        k = report["knowledge_base"]
        if k["configured"]:
            L.append(f"Knowledge base {k.get('root', k['path'])}  ({k['notes']} notes, {k.get('answers', 0)} saved "
                     f"answers, {k.get('evidence', 0)} kept snapshots)")
            for prob in k["problems"]:
                L.append(f"            {prob}")
        else:
            L.append(f"Knowledge base not created yet (would live at {k['path']})")
    if "playbooks" in report:
        found = report["playbooks"]["found"]
        L.append("Playbooks   " + (", ".join(f"{p['name']} ({p['path']})" for p in found) if found else "none found from here"))
    if "detected" in report:
        d = report["detected"]
        if d.get("error"):
            L.append(f"You         {d['error']}")
        else:
            L.append(f"You         {d.get('name') or 'name not found'}"
                     + (f" (from {d['name_from']})" if d.get("name_from") else "")
                     + f", time zone {d.get('timezone') or 'not found'} {d.get('utc_offset', '')}".rstrip()
                     + f", locale {d.get('locale') or 'not found'}, dates {d.get('date_format', '')}")
    if "skill_folders" in report:
        here = [f"{k.replace('_', ' ')}: {v['path']}" for k, v in report["skill_folders"].items() if v["exists"]]
        L.append("Skill folders " + (", ".join(here) if here else "none found"))
    if caps:
        c = capabilities(report)
        L.append("")
        L.append("Can use     " + ", ".join(
            [f"shell ({c['python']})", "git" if c["git"] else "no git",
             f"raw fetch: {c['raw_fetch']}", f"web search: {c['web_search']}", f"subagents: {c['subagents']}",
             f"MCP: {', '.join(c['mcp_servers']) or 'none'}"]))
        L.append("            Confirm a tool exists before relying on it. Without web access, ground in files, "
                 "git and MCP only, and label the rest [ASSUMPTION, verify].")

    b = blockers(report)
    L.append("")
    if b:
        L.append("Before this skill works fully:")
        L += [f"  - {x}" for x in b]
    else:
        L.append("Everything this skill needs is present.")
    L.append("This was read only. Nothing was changed.")
    return "\n".join(L)


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass
    ap = argparse.ArgumentParser(prog="doctor.py", description="Report what this machine and harness can do. Read only.")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--capabilities", action="store_true",
                    help="what the grounding step can use: OS, Python, harness, shell, git, MCP servers, "
                         "knowledge base and playbooks")
    ap.add_argument("--check", action="append", choices=ALL_CHECKS + ["web", "all"],
                    help="limit the probe (repeatable). web is the only one that uses the network, and runs "
                         "only when named")
    ap.add_argument("--no-network", action="store_true", help="kept for older instructions. The network is "
                                                                 "never used unless --check web is given")
    args = ap.parse_args(argv)

    asked = args.check or []
    if args.capabilities:
        checks = CAPABILITY_CHECKS + [c for c in asked if c not in CAPABILITY_CHECKS]
    elif not asked or "all" in asked:
        checks = ALL_CHECKS + [c for c in asked if c == "web"]
    else:
        checks = list(asked)
    if args.no_network:
        checks = [c for c in checks if c != "web"]

    report = collect(checks)
    if args.capabilities:
        report["capabilities"] = capabilities(report)
    print(json.dumps(report, indent=2) if args.json else render(report, caps=args.capabilities))
    return 1 if blockers(report) else 0


if __name__ == "__main__":
    sys.exit(main())
