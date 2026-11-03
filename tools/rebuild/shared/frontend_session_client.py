"""网站登录会话图片协议；独立于旧 API key 客户端，不自动重发 POST。

工程外配置：{"base_url":"https://l0veyou.com","model":"gpt-image-2-5-full",
"session_dpapi_path":"C:/outside-project/frontend-session.dpapi"}。
DPAPI 文件为当前 Windows 用户 ConvertFrom-SecureString 的十六进制输出；
解密明文为 {"headers":{"Authorization":"Bearer <网页 JWT>","Cookie":"..."}}。
不在命令行传会话，不保存响应正文/会话头/带签名的下载 URL。
参考图协议来自实际前端：images=[原文件 DataURL]，最多四张、每张不超过 8 MiB。
"""
from __future__ import annotations

import argparse
import base64
import ctypes
import hashlib
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCHEMA = "ufeneo.frontend-image-task.v1"
TASK_ID = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
JWT = re.compile(r"Bearer [A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\Z")
STATUSES = {"pending", "queued", "processing", "running", "completed", "failed", "error", "cancelled", "canceled"}
FAILED = {"failed", "error", "cancelled", "canceled"}


class FrontendError(RuntimeError):
    """固定错误码；禁止拼接服务器消息、URL、会话或底层异常。"""

    def __init__(self, code: str, http_status: int | None = None):
        self.code = code
        self.http_status = http_status
        self.task_status: str | None = None
        super().__init__(code + (f" (HTTP {http_status})" if http_status is not None else ""))


def _json_bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _url(value):
    try:
        if not isinstance(value, str) or any(ord(c) < 33 for c in value):
            raise ValueError
        parsed = urllib.parse.urlsplit(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
            raise ValueError
        return parsed, ("https", parsed.hostname.lower(), parsed.port or 443)
    except (ValueError, TypeError):
        raise FrontendError("https_url_required") from None


def _read_json(path, code):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError
        return value
    except (OSError, ValueError, UnicodeError):
        raise FrontendError(code) from None


def _write_json(path, value):
    """原子更新，不删除旧证据，不把会话带入临时文件。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    with temporary.open("xb") as stream:
        stream.write(_json_bytes(value) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def decrypt_session(path):
    """只解独立 DPAPI 文件；从不回落到环境变量或旧 image 凭据。"""
    if os.name != "nt":
        raise FrontendError("dpapi_requires_windows")
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [("length", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    try:
        raw = bytes.fromhex(Path(path).read_text(encoding="ascii").strip())
        buffer = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
        source, result = Blob(len(raw), buffer), Blob()
        crypt, kernel = ctypes.WinDLL("crypt32", use_last_error=True), ctypes.WinDLL("kernel32", use_last_error=True)
        crypt.CryptUnprotectData.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                                            ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
        crypt.CryptUnprotectData.restype = wintypes.BOOL
        kernel.LocalFree.argtypes, kernel.LocalFree.restype = [ctypes.c_void_p], ctypes.c_void_p
        if not crypt.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(result)):
            raise ValueError
        try:
            return ctypes.string_at(result.data, result.length).decode("utf-16-le").strip()
        finally:
            kernel.LocalFree(result.data)
    except (OSError, ValueError, UnicodeError):
        raise FrontendError("session_decryption_failed") from None


@dataclass(repr=False)
class HttpResponse:
    status: int
    headers: dict
    body: bytes = field(repr=False)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HttpsTransport:
    """无 Cookie jar、无隐式跳转、无自动重试；不打印或转抛底层错误。"""

    def __init__(self):
        self.opener = urllib.request.build_opener(_NoRedirect())

    def request(self, method, url, headers, body, timeout, limit):
        _url(url)
        try:
            request = urllib.request.Request(url, data=body, headers=headers, method=method)
            with self.opener.open(request, timeout=timeout) as response:
                data = response.read(limit + 1)
                if len(data) > limit:
                    raise FrontendError("response_too_large")
                return HttpResponse(response.status, dict(response.headers.items()), data)
        except urllib.error.HTTPError as exc:
            # 错误正文可能回显 JWT/Cookie，既不读取也不落盘。
            try:
                return HttpResponse(exc.code, {"Location": exc.headers.get("Location", "")}, b"")
            finally:
                exc.close()
        except (OSError, ValueError):
            raise FrontendError("network_failed") from None


class FrontendSessionClient:
    def __init__(self, config_path, *, transport=None, decrypt=None, workspace_root=PROJECT_ROOT):
        config_path = Path(config_path).resolve()
        workspace_root = Path(workspace_root).resolve()
        if config_path.is_relative_to(workspace_root):
            raise FrontendError("config_must_be_outside_project")
        config = _read_json(config_path, "invalid_frontend_config")
        if set(config) - {"base_url", "model", "session_dpapi_path", "timeout_seconds", "generation_parameters",
                          "one_shot_unresolved_authorization_path", "serial_retained_unknown_authorization_path"}:
            raise FrontendError("unknown_frontend_config_field")
        parsed, self.origin = _url(config.get("base_url"))
        if parsed.path.rstrip("/") not in ("", "/api/v1") or parsed.query:
            raise FrontendError("base_url_must_be_frontend_api")
        self.origin_url = urllib.parse.urlunsplit(("https", parsed.netloc, "", "", ""))
        self.base_url = self.origin_url + "/api/v1"
        self.model = config.get("model")
        if not isinstance(self.model, str) or not re.fullmatch(r"gpt-image-[A-Za-z0-9_.-]+", self.model):
            raise FrontendError("unsupported_image_model")
        parameters = config.get("generation_parameters", {})
        allowed_parameters = {"background": "transparent", "quality": "high", "output_format": "png"}
        if (not isinstance(parameters, dict)
                or any(key not in allowed_parameters or value != allowed_parameters[key]
                       for key, value in parameters.items())):
            raise FrontendError("unsupported_generation_parameters")
        # 仅供有记录的能力探测；参数已发送不代表服务端实际支持。
        self.generation_parameters = dict(parameters)
        value = config.get("session_dpapi_path")
        if not isinstance(value, str) or not value:
            raise FrontendError("independent_session_file_required")
        session_path = (config_path.parent / value).resolve()
        if session_path.is_relative_to(workspace_root) or session_path == config_path:
            raise FrontendError("session_file_must_be_outside_project")
        self.timeout = config.get("timeout_seconds", 60)
        if type(self.timeout) not in (int, float) or not 0 < self.timeout <= 300:
            raise FrontendError("invalid_timeout")
        try:
            session = json.loads((decrypt or decrypt_session)(session_path))
            headers = session["headers"]
            if not isinstance(headers, dict):
                raise ValueError
            self._headers = self._validate_headers(headers)
        except (ValueError, KeyError, TypeError):
            raise FrontendError("invalid_session_headers") from None
        self.transport = transport or HttpsTransport()
        self.inflight_path = config_path.with_name("ufeneo-frontend-inflight-" + _sha(self.origin_url.encode())[:16] + ".json")
        authorization = config.get("one_shot_unresolved_authorization_path")
        if authorization is not None and (not isinstance(authorization, str) or not authorization):
            raise FrontendError("invalid_unresolved_authorization_path")
        self.one_shot_authorization = (config_path.parent / authorization).resolve() if authorization else None
        serial = config.get("serial_retained_unknown_authorization_path")
        if serial is not None and (not isinstance(serial, str) or not serial):
            raise FrontendError("invalid_serial_authorization_path")
        self.serial_authorization = (config_path.parent / serial).resolve() if serial else None

    def _claim_inflight(self, state_path, request_sha256):
        """在项目全局槽锁内登记远端未决任务；进程退出不等于远端终止。"""
        target = str(Path(state_path).resolve())
        unresolved = []
        if self.inflight_path.exists():
            previous = _read_json(self.inflight_path, "invalid_inflight_journal")
            if (previous.get("schema") != "ufeneo.frontend-inflight.v1"
                    or previous.get("source_origin") != self.origin_url
                    or not isinstance(previous.get("state_path"), str)):
                raise FrontendError("invalid_inflight_journal")
            retained = previous.get("retained_unresolved_state_paths", [])
            if not isinstance(retained, list) or any(not isinstance(p, str) for p in retained):
                raise FrontendError("invalid_inflight_journal")
            for old_path in dict.fromkeys([*retained, previous["state_path"]]):
                if old_path == target:
                    continue
                try:
                    state = self._state(old_path)
                except FrontendError:
                    raise FrontendError("unresolved_remote_task_blocks_new_submission") from None
                if state.get("status") not in FAILED | {"completed"}:
                    unresolved.append((old_path, state))
        if unresolved:
            if self.serial_authorization is not None:
                self._validate_serial_retained_unknown(unresolved)
            else:
                self._consume_one_shot_authorization(unresolved, target, request_sha256)
        claim = {"schema": "ufeneo.frontend-inflight.v1", "source_origin": self.origin_url,
                 "state_path": target, "claimed_at_utc": _now()}
        if unresolved:
            claim["retained_unresolved_state_paths"] = [p for p, _ in unresolved]
            key = "serial_authorization_path" if self.serial_authorization is not None else "one_shot_authorization_path"
            claim[key] = str(self.serial_authorization or self.one_shot_authorization)
        _write_json(self.inflight_path, claim)

    def _validate_serial_retained_unknown(self, unresolved):
        """用户允许保留一张指定未知旧单；任何新单未决时仍不追加。"""
        error = "unresolved_remote_task_blocks_new_submission"
        if len(unresolved) != 1:
            raise FrontendError(error)
        old_path, old_state = unresolved[0]
        authorization = _read_json(self.serial_authorization, error)
        expected = {"schema": "ufeneo.frontend-retained-unknown-serial.v1", "source_origin": self.origin_url,
                    "unresolved_state_path": old_path, "unresolved_task_id": old_state.get("task_id"),
                    "unresolved_state_sha256": _sha(Path(old_path).read_bytes()),
                    "enabled": True, "max_new_inflight": 1, "manual_review_required": True}
        if (any(authorization.get(k) != v for k, v in expected.items())
                or authorization.get("enabled") is not True
                or authorization.get("manual_review_required") is not True
                or type(authorization.get("max_new_inflight")) is not int
                or "request_count_limit" not in authorization
                or authorization["request_count_limit"] is not None
                or not isinstance(authorization.get("user_approval"), str)
                or not authorization["user_approval"].strip()):
            raise FrontendError(error)

    def _consume_one_shot_authorization(self, unresolved, target, request_sha256):
        """仅放行用户明确批准的一张；旧未知单继续登记，后续请求仍被拦。"""
        error = "unresolved_remote_task_blocks_new_submission"
        if len(unresolved) != 1 or self.one_shot_authorization is None:
            raise FrontendError(error)
        old_path, old_state = unresolved[0]
        authorization = _read_json(self.one_shot_authorization, error)
        expected = {"schema": "ufeneo.frontend-one-extra-authorization.v1", "source_origin": self.origin_url,
                    "unresolved_state_path": old_path, "unresolved_task_id": old_state.get("task_id"),
                    "unresolved_state_sha256": _sha(Path(old_path).read_bytes()),
                    "target_state_path": target, "request_sha256": request_sha256,
                    "max_extra_submissions": 1, "consumed": False}
        if (any(authorization.get(k) != v for k, v in expected.items())
                or type(authorization.get("max_extra_submissions")) is not int
                or authorization.get("consumed") is not False
                or not isinstance(authorization.get("user_approval"), str)
                or not authorization["user_approval"].strip()):
            raise FrontendError(error)
        # 必须在POST之前持久化。之后即便断网/崩溃也不能再次用此授权发单。
        authorization.update(consumed=True, consumed_at_utc=_now())
        _write_json(self.one_shot_authorization, authorization)

    def _validate_headers(self, headers):
        allowed = {"authorization", "cookie", "origin", "referer", "user-agent", "accept", "x-csrf-token", "x-xsrf-token", "x-requested-with"}
        result = {}
        for name, value in headers.items():
            if not isinstance(name, str) or name.lower() not in allowed or not isinstance(value, str) or any(ord(c) < 32 or ord(c) == 127 for c in value):
                raise FrontendError("invalid_session_header")
            key = name.lower()
            if key in result:
                raise FrontendError("duplicate_session_header")
            if key in {"origin", "referer"} and _url(value)[1] != self.origin:
                raise FrontendError("cross_origin_session_header")
            result[key] = value
        if not JWT.fullmatch(result.get("authorization", "")):
            raise FrontendError("website_bearer_jwt_required_no_api_key")
        return result

    def _request(self, method, url, *, payload=None, authenticated=False, limit=8 * 1024 * 1024):
        if authenticated and _url(url)[1] != self.origin:
            raise FrontendError("cross_origin_auth_blocked")
        _url(url)
        headers = {"accept": "application/json" if authenticated else "image/*"}
        if authenticated:
            headers.update(self._headers)
        elif self._headers.get("user-agent"):
            # 图片 CDN 拒绝 Python 默认 UA；只沿用已登录浏览器的公开 UA，
            # 不把 Authorization、Cookie、CSRF 或其它会话头发往图片域名。
            headers["user-agent"] = self._headers["user-agent"]
        body = _json_bytes(payload) if payload is not None else None
        if body is not None:
            headers["content-type"] = "application/json"
        try:
            return self.transport.request(method, url, headers, body, self.timeout, limit)
        except FrontendError:
            raise
        except Exception:
            raise FrontendError("transport_failed") from None

    def _api(self, method, path, payload=None, *, allow_list=False):
        response = self._request(method, self.base_url + path, payload=payload, authenticated=True)
        if 300 <= response.status < 400:
            # POST 跳转可能重复计费；任何 API 跳转一律停止，不把认证转发。
            raise FrontendError("api_redirect_blocked", response.status)
        if not 200 <= response.status < 300:
            raise FrontendError("frontend_http_error", response.status)
        try:
            value = json.loads(response.body)
            if type(value.get("code")) is not int or value["code"] != 0 or not (isinstance(value.get("data"), dict)
                    or (allow_list and isinstance(value.get("data"), list))):
                raise ValueError
            return value["data"]
        except (ValueError, AttributeError, UnicodeError):
            raise FrontendError("frontend_response_rejected") from None

    def _state(self, path):
        state = _read_json(path, "invalid_task_state")
        if state.get("schema") != SCHEMA or state.get("source_origin") != self.origin_url or state.get("api_base_url") != self.base_url:
            raise FrontendError("task_state_origin_mismatch")
        if _sha(_json_bytes(state.get("request"))) != state.get("request_sha256"):
            raise FrontendError("task_request_hash_mismatch")
        return state

    @staticmethod
    def _task(data):
        task_id = str(data.get("id", ""))
        status = data.get("status")
        if not TASK_ID.fullmatch(task_id) or not isinstance(status, str) or status not in STATUSES:
            raise FrontendError("invalid_task_response")
        return task_id, status

    def _references(self, paths):
        images, records = [], []
        paths = list(paths or ())
        if len(paths) > 4:
            raise FrontendError("reference_count_exceeds_four")
        if paths and not self.model.startswith("gpt-image-2-5-"):
            raise FrontendError("reference_images_unsupported_by_model")
        for path in paths:
            path = Path(path).resolve()
            try:
                if path.stat().st_size > 8 * 1024 * 1024:
                    raise FrontendError("reference_exceeds_8_mib")
                raw = path.read_bytes()
                if len(raw) > 8 * 1024 * 1024:
                    raise FrontendError("reference_exceeds_8_mib")
            except OSError:
                raise FrontendError("reference_unreadable") from None
            if raw.startswith(b"\x89PNG\r\n\x1a\n"):
                mime = "image/png"
            elif raw.startswith(b"\xff\xd8\xff"):
                mime = "image/jpeg"
            elif raw.startswith((b"GIF87a", b"GIF89a")):
                mime = "image/gif"
            elif raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
                mime = "image/webp"
            else:
                raise FrontendError("unsupported_reference_image_type")
            images.append("data:" + mime + ";base64," + base64.b64encode(raw).decode("ascii"))
            records.append({"path": str(path), "sha256": _sha(raw), "mime_type": mime, "size_bytes": len(raw)})
        return images, records

    def submit(self, prompt, state_path, *, aspect_ratio="1:1", references=None):
        if not isinstance(prompt, str) or not prompt.strip() or not isinstance(aspect_ratio, str) or not re.fullmatch(r"[1-9][0-9]*:[1-9][0-9]*", aspect_ratio):
            raise FrontendError("invalid_generation_request")
        payload = {"prompt": prompt, "model": self.model, "aspect_ratio": aspect_ratio,
                   **self.generation_parameters}
        images, reference_records = self._references(references)
        if images:
            payload["images"] = images
        if Path(state_path).exists():
            raise FrontendError("task_state_exists_use_resume_no_repost")
        self._claim_inflight(state_path, _sha(_json_bytes(payload)))
        state = {"schema": SCHEMA, "source_kind": "website_frontend_session", "source_origin": self.origin_url, "api_base_url": self.base_url,
                 "request": payload, "request_sha256": _sha(_json_bytes(payload)), "created_at_utc": _now(),
                 "references": reference_records, "reference_count_limit_verified": True, "reference_count_limit": 4,
                 "status": "submission_started", "submission_outcome": "unknown_until_acknowledged", "post_attempts": 1}
        path = Path(state_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as stream:
                stream.write(_json_bytes(state) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            raise FrontendError("task_state_exists_use_resume_no_repost") from None
        try:
            data = self._api("POST", "/images/generate", payload)
            task_id, status = self._task(data)
        except FrontendError as exc:
            state.update(status="submission_unknown", error_code=exc.code, http_status=exc.http_status)
            _write_json(path, state)
            raise
        state.update(task_id=task_id, status=status, submission_outcome="acknowledged", updated_at_utc=_now(),
                     submission_response_diagnostic=self._poll_diagnostic(data))
        _write_json(path, state)  # 任务 ID 在任何轮询之前持久化。
        return state

    def adopt(self, task_id, state_path):
        """登记已存在的网页任务；不 POST、不伪造其原始请求或实际型号。"""
        if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
            raise FrontendError("invalid_existing_task_id")
        path = Path(state_path)
        if path.exists():
            state = self._state(path)
            if state.get("task_id") != task_id:
                raise FrontendError("existing_task_state_id_mismatch")
            return state
        state = {"schema": SCHEMA, "source_kind": "website_frontend_session", "source_origin": self.origin_url,
                 "api_base_url": self.base_url, "task_id": task_id, "status": "existing_task_unpolled",
                 "request": None, "request_sha256": _sha(_json_bytes(None)), "references": [],
                 "post_attempts": 0, "submission_outcome": "existing_task_not_submitted_here", "created_at_utc": _now()}
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("xb") as stream:
                stream.write(_json_bytes(state) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
        except FileExistsError:
            raise FrontendError("task_state_exists_use_resume_no_repost") from None
        return state

    @staticmethod
    def _poll_diagnostic(data):
        """在身份判定前保全小型白名单；异常字段只记散列，不记原正文。"""
        record = {"observed_at_utc": _now(), "id_present": "id" in data}
        for key in ("id", "status", "created_at", "updated_at", "aspect_ratio"):
            value = data.get(key)
            valid = False
            if key == "id":
                valid = type(value) in (str, int) and bool(TASK_ID.fullmatch(str(value)))
            elif key == "status":
                valid = isinstance(value, str) and value in STATUSES
            elif key == "aspect_ratio":
                valid = isinstance(value, str) and bool(re.fullmatch(r"[1-9][0-9]{0,3}:[1-9][0-9]{0,3}", value))
            elif type(value) in (int, float):
                valid = 0 <= value <= 10 ** 15
            elif isinstance(value, str) and len(value) <= 64:
                try:
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
                    valid = True
                except ValueError:
                    pass
            if valid:
                record[key] = value
            elif value is not None:
                record[key + "_invalid_sha256"] = _sha(_json_bytes(value))
        prompt = data.get("prompt")
        record["prompt_present"] = "prompt" in data
        if isinstance(prompt, str):
            record["prompt_sha256"] = _sha(prompt.encode("utf-8", errors="surrogatepass"))
        return record

    def _bound_record(self, state, data):
        """编号变化仅按已确认的原提示词、画幅和服务端创建时间绑定。"""
        request = state.get("request") or {}
        if not isinstance(request.get("prompt"), str) or data.get("prompt") != request["prompt"]:
            return False
        if data.get("aspect_ratio") != request.get("aspect_ratio"):
            return False
        expected = _sha(request["prompt"].encode("utf-8"))
        records = [state.get("submission_response_diagnostic") or {}] + state.get("poll_response_diagnostics", [])
        for record in records:
            if (record.get("id") != state["task_id"] or record.get("prompt_sha256") != expected
                    or record.get("aspect_ratio") != request.get("aspect_ratio") or not record.get("created_at")):
                continue
            try:
                before = datetime.fromisoformat(str(record["created_at"]).replace("Z", "+00:00"))
                after = datetime.fromisoformat(str(data.get("created_at", "")).replace("Z", "+00:00"))
                if before == after:
                    return True
            except ValueError:
                continue
        return False

    def _find_bound_record(self, state):
        request = state.get("request") or {}
        if not isinstance(request.get("prompt"), str):
            return None
        expected = _sha(request["prompt"].encode("utf-8"))
        records = [state.get("submission_response_diagnostic") or {}] + state.get("poll_response_diagnostics", [])
        if not any(r.get("id") == state["task_id"] and r.get("created_at")
                   and r.get("prompt_sha256") == expected for r in records):
            return None
        rows = self._api("GET", "/images/tasks", allow_list=True)
        if not isinstance(rows, list):
            return None
        matches = [row for row in rows if isinstance(row, dict) and self._bound_record(state, row)]
        return matches[0] if len(matches) == 1 else None

    def resume(self, state_path, *, out=None, max_polls=1, interval=5, sleep=time.sleep):
        if type(max_polls) is not int or not 1 <= max_polls <= 10000 or type(interval) not in (int, float) or not 0 <= interval <= 300:
            raise FrontendError("invalid_poll_limits")
        path = Path(state_path)
        state = self._state(path)
        task_id = state.get("task_id", "")
        if not isinstance(task_id, str) or not TASK_ID.fullmatch(task_id):
            raise FrontendError("submission_unknown_do_not_repost")
        if out is not None and self._recover_download(Path(out), path, state):
            return state
        for attempt in range(max_polls):
            try:
                try:
                    data = self._api("GET", "/images/tasks/" + task_id)
                except FrontendError as exc:
                    if exc.http_status != 404:
                        raise
                    recovered = self._find_bound_record(state)
                    if recovered is None:
                        raise
                    data = recovered
                state.setdefault("poll_response_diagnostics", []).append(self._poll_diagnostic(data))
                _write_json(path, state)  # 即使下方 ID 不匹配，实际协议证据也已保全。
                # 已观察提交返回 id；查询接口若省略 id，仍绑定本次请求的 ID。
                returned_id, status = self._task({"id": task_id, **data})
                if returned_id != task_id:
                    if not self._bound_record(state, data):
                        raise FrontendError("task_id_mismatch")
                    state.setdefault("verified_task_aliases", []).append({"requested_id": task_id,
                        "returned_id": returned_id, "binding": "exact_prompt_aspect_and_server_created_at"})
                    task_id = returned_id
                    state["task_id"] = returned_id
                state.update(status=status, updated_at_utc=_now())
                urls = data.get("image_urls", [])
                if not isinstance(urls, list) or not all(isinstance(u, str) for u in urls):
                    raise FrontendError("invalid_image_urls")
                state["result_count"] = len(urls)
                _write_json(path, state)
                if status in FAILED:
                    return state
                if status == "completed":
                    if out is not None:
                        if not urls:
                            raise FrontendError("completed_without_image")
                        self._download(urls[0], Path(out), path, state)
                    return state
            except FrontendError as exc:
                # 下载失败前可能已确认 completed；让调用方使用本次状态而非旧 pending。
                exc.task_status = state.get("status")
                state.update(last_poll_error=exc.code, last_poll_http_status=exc.http_status)
                _write_json(path, state)
                raise
            if attempt + 1 < max_polls:
                sleep(interval)
        return state

    def _trusted_download_metadata(self, out, state):
        path = out.with_suffix(out.suffix + ".metadata.json")
        if not path.exists():
            return None
        metadata = _read_json(path, "invalid_download_metadata")
        download = metadata.get("download")
        if (metadata.get("schema") != "ufeneo.frontend-image-download.v1"
                or metadata.get("source_origin") != self.origin_url or metadata.get("task_id") != state["task_id"]
                or metadata.get("request_sha256") != state["request_sha256"] or not isinstance(download, dict)
                or download.get("path") != str(out.resolve()) or download.get("session_headers_sent") is not False
                or not isinstance(download.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", download["sha256"])
                or type(download.get("size_bytes")) is not int or download["size_bytes"] <= 0):
            raise FrontendError("download_metadata_task_binding_mismatch")
        return metadata

    @staticmethod
    def _matches_download(path, download):
        try:
            if path.stat().st_size != download.get("size_bytes"):
                return False
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            return digest.hexdigest() == download.get("sha256")
        except OSError:
            raise FrontendError("download_recovery_file_unreadable") from None

    @staticmethod
    def _publish_download(staged, out):
        try:
            # 同目录硬链接是原子且不覆盖的发布；元数据先于这一步持久化。
            os.link(staged, out)
        except FileExistsError:
            raise FrontendError("output_exists_not_overwritten") from None
        except OSError:
            raise FrontendError("atomic_download_publish_failed") from None
        staged.unlink()  # 只清本次临时硬链接，原字节仍完整保留在正式候选。

    def _recover_download(self, out, state_path, state):
        existing = state.get("download")
        if out.exists() and isinstance(existing, dict) and existing.get("path") == str(out.resolve()) and self._matches_download(out, existing):
            return True
        metadata = self._trusted_download_metadata(out, state)
        if out.exists():
            if metadata is None or not self._matches_download(out, metadata["download"]):
                raise FrontendError("output_exists_not_overwritten")
        elif metadata is not None:
            name = metadata.get("pending_file", "")
            if not isinstance(name, str) or not name.startswith(out.name + ".download-") or not name.endswith(".part") or "/" in name or "\\" in name:
                raise FrontendError("invalid_download_journal_path")
            staged = out.parent / name
            if staged.resolve().parent != out.parent.resolve():
                raise FrontendError("invalid_download_journal_path")
            if not staged.exists():
                return False  # 可用同一任务 GET 重取，但后续必须匹配已留 SHA。
            if not self._matches_download(staged, metadata["download"]):
                return False  # 中断的临时文件保留；重取须与可信 sidecar 的 SHA 一致。
            self._publish_download(staged, out)
        else:
            return False
        state.update(download=metadata["download"], status="completed")
        _write_json(state_path, state)
        return True

    def _download(self, url, out, state_path, state):
        if self._recover_download(out, state_path, state):
            return
        prior_metadata = self._trusted_download_metadata(out, state)
        original_origin = _url(url)[1]
        for _ in range(6):
            response = self._request("GET", url, authenticated=False, limit=64 * 1024 * 1024)
            if 300 <= response.status < 400:
                location = next((v for k, v in response.headers.items() if k.lower() == "location"), "")
                if not location:
                    raise FrontendError("download_redirect_without_location")
                url = urllib.parse.urljoin(url, location)
                _url(url)  # CDN 跳转仍须 HTTPS，始终不带会话头或 Cookie。
                continue
            if not 200 <= response.status < 300:
                raise FrontendError("download_http_error", response.status)
            if not response.body:
                raise FrontendError("download_empty")
            if prior_metadata and (_sha(response.body) != prior_metadata["download"]["sha256"] or len(response.body) != prior_metadata["download"]["size_bytes"]):
                raise FrontendError("download_recovery_content_mismatch")
            out.parent.mkdir(parents=True, exist_ok=True)
            staged = out.with_name(out.name + ".download-" + uuid.uuid4().hex + ".part")
            download = {"path": str(out.resolve()), "sha256": _sha(response.body), "size_bytes": len(response.body),
                        "source_host": original_origin[1], "downloaded_at_utc": _now(), "session_headers_sent": False}
            metadata = {"schema": "ufeneo.frontend-image-download.v1", "pending_file": staged.name,
                        "source_kind": "website_frontend_session", "source_origin": self.origin_url, "task_id": state["task_id"],
                        "request": {k: v for k, v in state["request"].items() if k != "images"} if state["request"] else None,
                        "request_sha256": state["request_sha256"], "references": state.get("references", []),
                        "actual_model_verified": False, "alpha_checked": False, "runtime_approved": False, "download": download}
            # 先留任务绑定和预期 SHA，再写临时原件；任一点中断都有可信恢复依据。
            _write_json(out.with_suffix(out.suffix + ".metadata.json"), metadata)
            with staged.open("xb") as stream:
                stream.write(response.body)
                stream.flush()
                os.fsync(stream.fileno())
            self._publish_download(staged, out)
            state["download"] = download
            _write_json(state_path, state)
            return
        raise FrontendError("too_many_download_redirects")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    submit = commands.add_parser("submit")
    submit.add_argument("--prompt-file", type=Path, required=True)
    submit.add_argument("--state", type=Path, required=True)
    submit.add_argument("--aspect-ratio", default="1:1")
    submit.add_argument("--reference", type=Path, action="append", default=[])
    resume = commands.add_parser("resume")
    resume.add_argument("--state", type=Path, required=True)
    resume.add_argument("--out", type=Path)
    resume.add_argument("--polls", type=int, default=1)
    resume.add_argument("--interval", type=float, default=5)
    poll = commands.add_parser("poll", help="仅 GET 已存在的网页任务，绝不新 POST")
    poll.add_argument("--task-id", required=True)
    poll.add_argument("--state", type=Path, required=True)
    poll.add_argument("--out", type=Path)
    args = parser.parse_args()
    try:
        client = FrontendSessionClient(args.config)
        if args.command == "submit":
            state = client.submit(args.prompt_file.read_text(encoding="utf-8"), args.state, aspect_ratio=args.aspect_ratio, references=args.reference)
        elif args.command == "poll":
            client.adopt(args.task_id, args.state)
            state = client.resume(args.state, out=args.out)
        else:
            state = client.resume(args.state, out=args.out, max_polls=args.polls, interval=args.interval)
        print(json.dumps({"status": state["status"], "task_id": state.get("task_id"), "state": str(args.state)}, ensure_ascii=False))
    except FrontendError as exc:
        print(json.dumps({"error_code": exc.code, "http_status": exc.http_status}))
        return 1
    except (OSError, ValueError):
        print('{"error_code":"local_file_error"}')
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
