#!/usr/bin/env python3
"""Story Lab 只读 Web 查看器。

用法:
    webview.py [--host 0.0.0.0] [--port 8765] [--slug urban-counterattack]

- 只读：不修改 bible/structure/episodes 等事实源，也不产生快照文件。
- 复用 status.py 的 build_dataset() 与 continuity.py 的巡检逻辑。
- 前端为 web/ 下的零依赖原生 HTML/CSS/JS，无需 npm/构建。

API:
    GET /api/health
    GET /api/projects
    GET /api/project/<slug>/overview
    GET /api/project/<slug>/episodes
    GET /api/project/<slug>/episode/<n>
    GET /api/project/<slug>/bible
    GET /api/project/<slug>/structure
    GET /api/project/<slug>/continuity
    GET /api/project/<slug>/decisions

退出码: 0 = 正常退出；1 = 启动错误。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import threading
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

HERE = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
WEB_DIR = HERE.parent / "web"
sys.path.insert(0, str(HERE))

import continuity as ct  # noqa: E402
import status as st  # noqa: E402

CT_LOCK = threading.Lock()
SLUG_RE = re.compile(r"^[A-Za-z0-9_-]+$")


# ---------------------------------------------------------------- 工具
def json_safe(value):
    """把 YAML 解析出的 date/Path 等转成 JSON 可序列化对象。"""
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [json_safe(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def project_dir(slug: str) -> Path | None:
    if not SLUG_RE.match(slug or ""):
        return None
    proj = (ROOT / "projects" / slug).resolve()
    try:
        proj.relative_to((ROOT / "projects").resolve())
    except ValueError:
        return None
    return proj if proj.is_dir() else None


def project_slugs() -> list[str]:
    base = ROOT / "projects"
    if not base.is_dir():
        return []
    return sorted(p.name for p in base.iterdir()
                  if p.is_dir() and (p / "project.yaml").exists())


def protagonist_id(data: dict) -> str:
    for c in data.get("chars") or []:
        if isinstance(c, dict) and c.get("role") == "protagonist":
            return str(c.get("id") or "")
    chars = data.get("chars") or []
    return str(chars[0].get("id") or "") if chars and isinstance(chars[0], dict) else ""


def ep_summary(e: dict, hooks_by_ep: dict) -> dict:
    h = hooks_by_ep.get(e["ep"]) or {}
    return {
        "ep": e["ep"],
        "status": st.STATUS_TEXT.get(e["status"], e["status"]),
        "raw_status": e["status"],
        "scenes": e.get("scenes", 0),
        "card_seconds": e.get("card_seconds", 0),
        "script_seconds": round(e.get("script_seconds", 0.0), 1),
        "review_total": e.get("review_total"),
        "review_threshold": e.get("review_threshold"),
        "review_verdict": e.get("review_verdict"),
        "review_round": e.get("review_round"),
        "reviewer": e.get("reviewer", ""),
        "warnings": len(e.get("warnings") or []),
        "blockers": len(e.get("blockers") or []),
        "notes": e.get("notes") or [],
        "hook": h.get("question_left_open", ""),
        "cliffhanger": h.get("cliffhanger_type", ""),
        "value_before": h.get("value_before", ""),
        "value_after": h.get("value_after", ""),
        "pinned": bool(h.get("pinned")),
    }


def movement_rows(data: dict) -> list[dict]:
    rows = []
    passed = {e["ep"] for e in data["episodes"] if e["status"] == "通过"}
    for m in data.get("movements") or []:
        if not isinstance(m, dict):
            continue
        rng = m.get("episodes") or []
        try:
            start, end = int(rng[0]), int(rng[1])
        except (TypeError, ValueError, IndexError):
            continue
        total = max(end - start + 1, 1)
        done = sum(1 for ep in range(start, end + 1) if ep in passed)
        rows.append({
            "id": m.get("id"),
            "name": m.get("name", ""),
            "goal": m.get("goal", ""),
            "start": start,
            "end": end,
            "done": done,
            "total": total,
            "percent": round(done * 100 / total, 1),
        })
    return rows


def overview_payload(proj: Path, data: dict) -> dict:
    eps = data["episodes"]
    hooks = data.get("hooks_by_ep") or {}
    passed = [e for e in eps if e["status"] == "通过"]
    written = [e for e in eps if e.get("script")]
    current = next((e["ep"] for e in eps if e["status"] != "通过"), data["n_eps"])
    last = max((e["ep"] for e in passed), default=0)
    last_ep = eps[last - 1] if last else None
    last_state = (last_ep or {}).get("state") or {}
    pid = protagonist_id(data)
    char_state = ((last_state.get("characters") or {}).get(pid) or {}) if pid else {}
    last_hook = hooks.get(last) or {}
    movement_done = sum(r["done"] for r in movement_rows(data))
    warnings = sum(len(e.get("warnings") or []) for e in eps)
    blockers = sum(len(e.get("blockers") or []) for e in eps)
    data_issues = list(dict.fromkeys(list(data.get("errors") or []) + st.health_checks(data)))

    return {
        "project": json_safe(data.get("cfg") or {}),
        "logline": st.extract_logline(data.get("premise") or ""),
        "progress": {
            "passed": len(passed),
            "written": len(written),
            "total": data["n_eps"],
            "percent": round(len(passed) * 100 / data["n_eps"], 1) if data["n_eps"] else 0,
            "movement_passed": movement_done,
            "current_ep": current,
        },
        "movements": movement_rows(data),
        "pinned": [
            {"episode": st.as_int(p.get("episode")), "kind": p.get("kind", ""), "note": p.get("note", "")}
            for p in (data.get("pinned_eps") or {}).values() if isinstance(p, dict)
        ],
        "next": [ep_summary(eps[ep - 1], hooks)
                 for ep in range(current, min(current + 3, data["n_eps"] + 1)) if 1 <= ep <= data["n_eps"]],
        "story": {
            "last_ep": last,
            "last_value": last_hook.get("value_after", ""),
            "question": last_hook.get("question_left_open", ""),
            "open_threads": last_state.get("open_threads") or [],
            "protagonist": {
                "id": pid,
                "name": char_state.get("name") or next(
                    (c.get("name", pid) for c in data.get("chars") or []
                     if isinstance(c, dict) and str(c.get("id")) == pid), pid),
                "knows": char_state.get("knows") or [],
                "believes": char_state.get("believes") or [],
                "suspects": char_state.get("suspects") or [],
            },
            "decisions": data.get("decisions", 0),
        },
        "recent": [ep_summary(e, hooks) for e in sorted(passed, key=lambda x: x["ep"], reverse=True)[:5]],
        "quality": {
            "warnings": warnings,
            "blockers": blockers,
            "data_issues": data_issues,
        },
        "threads": json_safe(st.thread_rows(data)),
        "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def episodes_payload(proj: Path, data: dict) -> dict:
    hooks = data.get("hooks_by_ep") or {}
    return {
        "project": json_safe(data.get("cfg") or {}),
        "episodes": [ep_summary(e, hooks) for e in data["episodes"]],
    }


def episode_payload(proj: Path, data: dict, n: int) -> dict | None:
    if n < 1 or n > data["n_eps"]:
        return None
    e = data["episodes"][n - 1]
    hooks = data.get("hooks_by_ep") or {}
    script_path = proj / f"episodes/e{n:02d}/script.md"
    return {
        "project": json_safe(data.get("cfg") or {}),
        "summary": ep_summary(e, hooks),
        "hook": json_safe(hooks.get(n) or {}),
        "cards": json_safe(e.get("cards") or []),
        "script": script_path.read_text(encoding="utf-8") if script_path.exists() else "",
        "state": json_safe(e.get("state") or {}),
        "review": json_safe(e.get("review") or {}),
        "character_names": {
            str(c.get("id")): c.get("name") or str(c.get("id"))
            for c in (data.get("chars") or []) if isinstance(c, dict)
        },
    }


def bible_payload(proj: Path, data: dict) -> dict:
    return {
        "project": json_safe(data.get("cfg") or {}),
        "premise": data.get("premise") or "",
        "world": st.read_text(proj / "bible/world.md"),
        "voice": st.read_text(proj / "bible/voice.md"),
        "characters": json_safe(data.get("chars") or []),
        "relations": json_safe(data.get("relations") or []),
    }


def structure_payload(proj: Path, data: dict) -> dict:
    return {
        "project": json_safe(data.get("cfg") or {}),
        "movements": movement_rows(data),
        "pinned": [
            {"episode": st.as_int(p.get("episode")), "kind": p.get("kind", ""), "note": p.get("note", "")}
            for p in (data.get("pinned_eps") or {}).values() if isinstance(p, dict)
        ],
        "hooks": json_safe(data.get("hooks") or []),
        "threads": json_safe(st.thread_rows(data)),
    }


def continuity_payload(proj: Path, data: dict) -> dict:
    with CT_LOCK:
        ct.issues.clear()
        cdata = ct.collect(proj)
        ct.check_value_chain(cdata)
        ct.check_episodes(cdata)
        issues = list(ct.issues)
        latest = cdata.get("latest", 0)
    eps = []
    for e in data["episodes"]:
        if not e.get("script"):
            continue
        state = e.get("state") or {}
        chars = state.get("characters") or {}
        eps.append({
            "ep": e["ep"],
            "script_seconds": round(e.get("script_seconds", 0.0), 1),
            "review_total": e.get("review_total"),
            "review_threshold": e.get("review_threshold"),
            "review_verdict": e.get("review_verdict"),
            "locations": [{"id": cid, "location": (c or {}).get("location", "—")}
                          for cid, c in chars.items() if isinstance(c, dict)],
            "props": len(state.get("props") or {}),
            "open_threads": state.get("open_threads") or [],
        })
    return {
        "project": json_safe(data.get("cfg") or {}),
        "latest": latest,
        "blockers": [i for i in issues if i.get("level") == "BLOCKER"],
        "warnings": [i for i in issues if i.get("level") == "WARN"],
        "issues": issues,
        "episodes": eps,
    }


def decisions_payload(proj: Path) -> dict:
    path = proj / "decisions.jsonl"
    rows = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                rows.append({"raw": line})
    rows.reverse()
    return {"total": len(rows), "decisions": json_safe(rows)}


# ---------------------------------------------------------------- HTTP
class Handler(BaseHTTPRequestHandler):
    server_version = "StoryLabWeb/1.0"

    def log_message(self, fmt, *args):  # noqa: A003
        sys.stderr.write("[web] %s - %s\n" % (self.address_string(), fmt % args))

    def send_json(self, obj, status: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path, content_type: str) -> None:
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        try:
            if path.startswith("/api/"):
                self.handle_api(path)
                return
            self.handle_static(path)
        except BrokenPipeError:
            pass
        except Exception as exc:  # noqa: BLE001
            self.send_json({"error": str(exc)}, 500)

    def handle_api(self, path: str) -> None:
        parts = [p for p in path.split("/") if p]
        # ['api', ...]
        if path == "/api/health":
            self.send_json({"ok": True, "root": str(ROOT),
                            "projects": project_slugs(),
                            "time": datetime.now().isoformat(timespec="seconds")})
            return
        if path == "/api/projects":
            items = []
            for slug in project_slugs():
                proj = project_dir(slug)
                if not proj:
                    continue
                errs: list[str] = []
                cfg = st.read_yaml(proj / "project.yaml", errs) or {}
                items.append({
                    "slug": slug,
                    "title": cfg.get("title") or slug,
                    "genre": cfg.get("genre") or "",
                    "episodes": st.as_int(cfg.get("episodes")),
                    "seconds_per_episode": st.as_int(cfg.get("seconds_per_episode")),
                    "errors": errs,
                })
            self.send_json({"projects": items})
            return
        if len(parts) >= 4 and parts[1] == "project":
            slug, action = parts[2], parts[3]
            proj = project_dir(slug)
            if not proj:
                self.send_json({"error": f"项目不存在: {slug}"}, 404)
                return
            data = st.build_dataset(proj)
            if action == "overview":
                self.send_json(overview_payload(proj, data))
            elif action == "episodes":
                self.send_json(episodes_payload(proj, data))
            elif action == "episode":
                n = st.as_int(parts[4]) if len(parts) >= 5 else 0
                payload = episode_payload(proj, data, n)
                if payload is None:
                    self.send_json({"error": f"集号超出范围: {n}"}, 404)
                else:
                    self.send_json(payload)
            elif action == "bible":
                self.send_json(bible_payload(proj, data))
            elif action == "structure":
                self.send_json(structure_payload(proj, data))
            elif action == "continuity":
                self.send_json(continuity_payload(proj, data))
            elif action == "decisions":
                self.send_json(decisions_payload(proj))
            else:
                self.send_json({"error": f"未知接口: {action}"}, 404)
            return
        self.send_json({"error": "未知接口"}, 404)

    def handle_static(self, path: str) -> None:
        rel = path.lstrip("/") or "index.html"
        target = (WEB_DIR / rel).resolve()
        try:
            target.relative_to(WEB_DIR.resolve())
        except ValueError:
            self.send_json({"error": "非法路径"}, 403)
            return
        if not target.is_file():
            target = WEB_DIR / "index.html"
        ext = target.suffix.lower()
        ctypes = {
            ".html": "text/html; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".ico": "image/x-icon",
            ".json": "application/json; charset=utf-8",
        }
        self.send_file(target, ctypes.get(ext, "application/octet-stream"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Story Lab 只读 Web 查看器")
    ap.add_argument("--host", default="0.0.0.0", help="监听地址（默认 0.0.0.0）")
    ap.add_argument("--port", type=int, default=8765, help="监听端口（默认 8765）")
    ap.add_argument("--slug", default="", help="默认打开的项目 slug（可选）")
    args = ap.parse_args()

    if not WEB_DIR.is_dir():
        print(f"前端目录不存在: {WEB_DIR}", file=sys.stderr)
        return 1
    if not project_slugs():
        print(f"未找到项目: {ROOT / 'projects'}", file=sys.stderr)
        return 1

    srv = ThreadingHTTPServer((args.host, args.port), Handler)
    print("Story Lab Web Viewer")
    print(f"  项目根: {ROOT}")
    print(f"  前端:   {WEB_DIR}")
    print(f"  监听:   http://{args.host}:{args.port}")
    if args.slug:
        print(f"  默认:   {args.slug}")
    print("  Ctrl+C 退出")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n已停止")
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
