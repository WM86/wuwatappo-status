#!/usr/bin/env python3
"""Wuwa Tappo (鸣潮桌宠) 官方 API status probe.

被 .github/workflows/probe.yml 每 5 分钟叫一次, 结果并进 data/history.json。
只用标准库, 不需要装依赖。
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

HOST = "api-mc-wuwatappo.kurogames-global.com"
BASE = "https://" + HOST
TIMEOUT = 15
KEEP_RUNS = 1000

CHECKS = [
    {"id": "common", "name": "公共接口", "path": "/api/common/activity-config", "kind": "json-code"},
    {"id": "atlas", "name": "图鉴接口", "path": "/api/common/atlas", "kind": "json-code"},
    {"id": "socket", "name": "联机握手", "path": "/socket.io/?EIO=4&transport=polling", "kind": "socketio"},
    {"id": "auth", "name": "账号接口", "path": "/api/frontend/user/me", "kind": "http-any"},
]

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


def probe_one(check: dict) -> dict:
    url = BASE + check["path"]
    started = time.time()
    out = {"ok": False, "ms": None, "code": None, "detail": ""}
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "wuwatappo-status/1.0 (+github actions)", "Accept": "*/*"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=CTX) as resp:
            body = resp.read(2048)
            out["code"] = resp.status
            out["ms"] = int((time.time() - started) * 1000)
            out["ok"] = _judge(check["kind"], resp.status, body, out)
    except urllib.error.HTTPError as exc:
        out["code"] = exc.code
        out["ms"] = int((time.time() - started) * 1000)
        try:
            body = exc.read(2048)
        except Exception:
            body = b""
        out["ok"] = _judge(check["kind"], exc.code, body, out)
    except Exception as exc:  # 超时 / DNS / TLS
        out["ms"] = int((time.time() - started) * 1000)
        out["detail"] = f"{type(exc).__name__}: {str(exc)[:90]}"
        out["ok"] = False
    return out


def _judge(kind: str, status: int, body: bytes, out: dict) -> bool:
    if status >= 500:
        out["detail"] = f"HTTP {status}"
        return False
    if kind == "json-code":
        # 响应可能很大(atlas 几百 KB), 只按开头判业务码, 不整体解析
        head = body[:400].decode("utf-8", "replace").replace(" ", "")
        if '"code":0' in head:
            return True
        out["detail"] = "业务码异常"
        return False
    if kind == "socketio":
        text = body.decode("utf-8", "replace")
        if '"sid"' in text:
            return True
        out["detail"] = "握手无 sid"
        return False
    # http-any: 只要服务端给了正常业务响应（含 401 未鉴权）就算在线
    return status in (200, 401, 403)


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    checks = {}
    for check in CHECKS:
        result = probe_one(check)
        result["name"] = check["name"]
        result["path"] = check["path"]
        checks[check["id"]] = result
        print(f"[{check['id']}] ok={result['ok']} code={result['code']} "
              f"ms={result['ms']} {result['detail']}", file=sys.stderr)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(root, "data")
    os.makedirs(data_dir, exist_ok=True)
    path = os.path.join(data_dir, "history.json")

    doc = {"host": HOST, "updated": now, "checks": checks, "runs": []}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                old = json.load(fh)
            if isinstance(old.get("runs"), list):
                doc["runs"] = old["runs"]
        except Exception as exc:
            print(f"旧数据读不动, 重开: {exc}", file=sys.stderr)

    doc["runs"].append({
        "t": now,
        "ok": {k: bool(v["ok"]) for k, v in checks.items()},
        "ms": {k: v["ms"] for k, v in checks.items()},
    })
    doc["runs"] = doc["runs"][-KEEP_RUNS:]

    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, ensure_ascii=False, separators=(",", ":"))
        fh.write("\n")

    down = [k for k, v in checks.items() if not v["ok"]]
    print(f"{'ALL OK' if not down else 'DOWN: ' + ','.join(down)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
