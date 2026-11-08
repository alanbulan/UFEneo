"""Offline production client for Kits. Never imported by the game.

Only the documented Kits origin receives Authorization. POSTs are never retried;
request reservations survive connection loss so an uncertain job is not rebilled.
"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools").iterdir() if p.is_dir()], *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson

import json; json = _LayoutJson
import os
from pathlib import Path
Path = _LayoutProjectPath
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

API = "https://arpeggi.io/api/kits/v1"
KINDS = {"voice": "voice-conversions", "instrument": "voice-conversions",
         "separate": "vocal-separations", "stems": "stem-splits"}
# 纯文本密钥文件；必须 0600 且只在本机，不复制、不打印、不提交。
PLAIN_SECRET = Path.home() / ".codex/secrets/ufeneo-music.key"
STATE = Path.home() / ".codex/audio/kits"


class KitsError(ValueError):
    pass


def credential():
    token = os.environ.get("UFE_KITS_API_KEY", "").strip()
    if not token and PLAIN_SECRET.is_file():
        # 读取 0600 纯文本密钥；只在本机，不进仓库。
        mode = PLAIN_SECRET.stat().st_mode & 0o777
        if mode & 0o077:
            raise KitsError("Kits 密钥文件权限过宽，应为 0600；未发送请求")
        token = PLAIN_SECRET.read_text(encoding="utf-8").strip()
    if not token:
        raise KitsError("未配置 Kits 凭据；使用纯文本密钥或 UFE_KITS_API_KEY")
    if any(c.isspace() for c in token) or len(token) > 512:
        raise KitsError("Kits 凭据格式无效；未发送请求")
    return token


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def request(method, path, body=None, content_type=None, token=None):
    if not path.startswith("/") or path.startswith("//") or ".." in path:
        raise KitsError("无效 Kits API 路径")
    headers = {"Authorization": "Bearer " + (token if token is not None else credential()),
               "Accept": "application/json"}
    if content_type:
        headers["Content-Type"] = content_type
    req = urllib.request.Request(API + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.build_opener(NoRedirect()).open(req, timeout=30) as response:
            data = response.read(2 * 1024 * 1024 + 1)
        if len(data) > 2 * 1024 * 1024:
            raise KitsError("Kits 响应超过本地上限")
        result = json.loads(data)
        if not isinstance(result, dict):
            raise KitsError("Kits 返回了无效响应")
        return result
    except urllib.error.HTTPError as exc:
        messages = {401: "密钥无效或已失效", 403: "当前密钥无访问权限",
                    402: "账户额度不足", 422: "参数或文件不符合服务要求", 429: "账户调用频率超限"}
        raise KitsError(f"Kits HTTP {exc.code}：{messages.get(exc.code, '请求失败')}；未自动重试") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise KitsError("Kits 连接失败或超时；POST 是否完成未知，未自动重试") from None
    except (UnicodeError, json.JSONDecodeError):
        raise KitsError("Kits 响应无法解析；未自动重试") from None


def models(page=1, per_page=10, mine=False, instruments=False):
    if type(page) is not int or page < 1 or type(per_page) is not int or not 1 <= per_page <= 20:
        raise KitsError("模型列表每页限 1～20 条，页码从 1 开始")
    query = urllib.parse.urlencode({"page": page, "perPage": per_page, "order": "asc",
                                   "myModels": str(mine).lower(), "instruments": str(instruments).lower()})
    response = request("GET", "/voice-models?" + query)
    if not isinstance(response.get("data"), list) or len(response["data"]) > per_page:
        raise KitsError("Kits 模型列表未遵守分页上限")
    return {"models": [{key: item.get(key) for key in ("id", "title", "isUsable", "tags")}
                       for item in response["data"]],
            "page": page, "per_page": per_page,
            "total": response.get("meta", {}).get("total"),
            "last_page": response.get("meta", {}).get("lastPage")}


def multipart(fields, file_field, file):
    boundary = "UfeKits" + uuid.uuid4().hex
    chunks = []
    for key, value in fields.items():
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
    # A fixed filename avoids quoting a user path into multipart headers.
    chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="clip{file.suffix.lower()}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode())
    chunks.extend([file.read_bytes(), b"\r\n", f"--{boundary}--\r\n".encode()])
    return b"".join(chunks), "multipart/form-data; boundary=" + boundary


def reserve_post(state=STATE, now=None):
    """Account-wide local throttle: fail promptly instead of sleeping in the UI."""
    state.mkdir(parents=True, exist_ok=True)
    lock = state / "post.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        raise KitsError("另一项 Kits 提交尚未释放锁；先检查原进程，不能重复提交") from None
    try:
        os.close(fd)
        stamp = state / "last-post.json"
        current = time.time() if now is None else now
        previous = json.loads(stamp.read_text(encoding="utf-8"))["time"] if stamp.exists() else 0
        if current - previous < 60:
            raise KitsError(f"Kits 账户每分钟最多提交一次；还需等待 {max(1, int(61 - current + previous))} 秒")
        temporary = state / (uuid.uuid4().hex + ".tmp")
        temporary.write_text(json.dumps({"time": current}), encoding="utf-8")
        os.replace(temporary, stamp)
    finally:
        lock.unlink()


def remote_job(kind, job_id):
    if kind not in KINDS or type(job_id) is not int or job_id < 1:
        raise KitsError("无效 Kits 任务标识")
    return request("GET", f"/{KINDS[kind]}/{job_id}")


def download(url, target, max_bytes=100 * 1024 * 1024):
    """Result URLs get no API header and never appear in public reports."""
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise KitsError("结果下载地址必须是无内嵌凭据的 HTTPS")
    if target.exists():
        raise KitsError("输出已存在，不能覆盖")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".part")
    owned_temporary = False
    try:
        with temporary.open("xb") as output:
            owned_temporary = True
            with urllib.request.build_opener(NoRedirect()).open(url, timeout=30) as response:
                size = 0
                while chunk := response.read(1024 * 1024):
                    size += len(chunk)
                    if size > max_bytes:
                        raise KitsError("结果下载超过 100MiB 上限")
                    output.write(chunk)
        # Avoid overwriting another writer's output.
        temporary.rename(target)
    except (urllib.error.URLError, TimeoutError, OSError):
        raise KitsError("结果下载失败；签名地址未写入日志") from None
    finally:
        if owned_temporary and temporary.exists():
            temporary.unlink()
