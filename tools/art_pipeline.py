"""UFEneo art workbench. Secrets are read at runtime, never written to the project.

Concept generation is separate from production sprite generation. The latter
delegates to the installed sprite-gen component-row pipeline in its own venv.
"""
from __future__ import annotations

# 目录迁移：只解析冻结证据中的旧路径；不复制素材。
import sys as _layout_sys
from pathlib import Path as _LayoutNativePath
_layout_root = next(p for p in _LayoutNativePath(__file__).resolve().parents if (p / "project.godot").is_file())
_layout_sys.path[:0] = [str(_layout_root / "tools/maintenance"), str(_layout_root / "tools"), *[str(p) for p in (_layout_root / "tools/rebuild").iterdir() if p.is_dir()]]
from layout_runtime import ProjectPath as _LayoutProjectPath, json_proxy as _LayoutJson

import argparse
import base64
import hashlib
import http.client
import io
import json; json = _LayoutJson
import os
from pathlib import Path
Path = _LayoutProjectPath
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import tomllib
import urllib.error
import urllib.parse
import urllib.request
import uuid

ROOT = _LayoutProjectPath(_layout_root)
SPRITE_ROOT = Path(os.environ.get("SPRITE_GEN_ROOT", str(Path.home() / ".codex/skills/sprite-gen")))


IMAGE_CONFIG = Path.home() / ".codex/secrets/ufeneo-image.json"
IMAGE_SECRET = Path.home() / ".codex/secrets/ufeneo-image.dpapi"


def local_image_config():
    """Machine-local image endpoint chosen by the user (base_url, model). Never holds the key."""
    if not IMAGE_CONFIG.is_file():
        return {}
    return json.loads(IMAGE_CONFIG.read_text(encoding="utf-8"))


def dpapi_text(path):
    """Decrypt a ConvertFrom-SecureString hex blob for the current Windows user."""
    import ctypes
    from ctypes import wintypes

    class Blob(ctypes.Structure):
        _fields_ = [("length", wintypes.DWORD), ("data", ctypes.POINTER(ctypes.c_ubyte))]

    raw = bytes.fromhex(path.read_text(encoding="ascii").strip())
    buffer = (ctypes.c_ubyte * len(raw)).from_buffer_copy(raw)
    source, result = Blob(len(raw), buffer), Blob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    crypt.CryptUnprotectData.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                                         ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(Blob)]
    crypt.CryptUnprotectData.restype = wintypes.BOOL
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    if not crypt.CryptUnprotectData(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(result)):
        raise ValueError("Image credential cannot be decrypted by this Windows user")
    try:
        return ctypes.string_at(result.data, result.length).decode("utf-16-le").strip()
    finally:
        kernel.LocalFree(result.data)


def credentials():
    """UFE_IMAGE_* env, then the machine-local image config, then OpenAI env / active Codex provider.
    No auth data in output."""
    local = local_image_config()
    if image_route(local) == "frontend_session":
        raise ValueError("Frontend session route forbids API key credentials")
    token = os.environ.get("UFE_IMAGE_API_KEY")
    url = os.environ.get("UFE_IMAGE_BASE_URL") or local.get("base_url")
    if not token and os.name == "nt" and IMAGE_SECRET.is_file():
        token = dpapi_text(IMAGE_SECRET)
    token = token or os.environ.get("OPENAI_API_KEY")
    url = url or os.environ.get("OPENAI_BASE_URL")
    config = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "config.toml"
    if config.exists() and (not token or not url):
        data = tomllib.loads(config.read_text(encoding="utf-8"))
        provider = data.get("model_providers", {}).get(data.get("model_provider", "custom"), {})
        url = url or provider.get("base_url")
        token = token or os.environ.get(provider.get("env_key", "")) or provider.get("experimental_bearer_token")
    return (url or "https://api.openai.com/v1").rstrip("/"), token


def endpoint_model(requested):
    """The model actually sent. The user's endpoint serves one GPT Image model under its own name."""
    configured = os.environ.get("UFE_IMAGE_MODEL") or local_image_config().get("model")
    return configured or requested


def image_route(local=None):
    local = local_image_config() if local is None else local
    configured = local.get("route", "api")
    override = os.environ.get("UFE_IMAGE_ROUTE")
    if configured not in {"api", "frontend_session"} or (override and override not in {"api", "frontend_session"}):
        raise ValueError("UFE_IMAGE_ROUTE must be api or frontend_session")
    if configured == "frontend_session" and override and override != "frontend_session":
        raise ValueError("Local frontend session route forbids API key fallback")
    return override or configured


def frontend_profile_path():
    return Path(os.environ.get("UFE_WEB_SESSION_CONFIG") or
                local_image_config().get("frontend_session_config") or
                str(Path.home() / ".codex/secrets/ufeneo-web-session.json"))


def frontend_image_result(args, fields):
    """复用网页真实协议；已提交任务只恢复 GET，不重复 POST。"""
    from frontend_session_client import FrontendError, FrontendSessionClient

    client = FrontendSessionClient(frontend_profile_path())
    width, height = map(int, fields["size"].split("x"))
    from math import gcd
    divisor = gcd(width, height)
    aspect = f"{width // divisor}:{height // divisor}"
    state_path = args.out.with_suffix(".frontend-task.json")
    provider_path = args.out.with_suffix(".frontend-original.png")
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
        request = state.get("request") or {}
        references = [{"path": str(p.resolve()), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                      for p in args.reference]
        recorded = [{"path": r["path"], "sha256": r["sha256"]} for r in state.get("references", [])]
        if (request.get("prompt") != fields["prompt"] or request.get("model") != client.model
                or request.get("aspect_ratio") != aspect or recorded != references
                or {key: request[key] for key in ("background", "quality", "output_format") if key in request}
                    != client.generation_parameters):
            raise ValueError("Existing frontend task belongs to a different request; not resubmitted")
    else:
        state = client.submit(fields["prompt"], state_path, aspect_ratio=aspect, references=args.reference)
    deadline = time.monotonic() + image_request_timeout()
    transient_get_errors = 0
    while True:
        try:
            state = client.resume(state_path, out=provider_path, max_polls=1)
        except FrontendError as exc:
            # 已确认在途的任务偶尔暂时404；和错号一样只在原时限内查原任务。
            # 未确认/已终态任务的404不自动重试，不采用错号或重发生成。
            latest_status = exc.task_status or state.get("status")
            pending_not_found = (exc.code == "frontend_http_error" and exc.http_status == 404
                                 and latest_status in {"pending", "queued", "processing", "running"})
            transient = exc.http_status in {408, 429, 500, 502, 503, 504} or exc.code in {
                "network_failed", "transport_failed", "task_id_mismatch"} or pending_not_found
            if not transient or time.monotonic() >= deadline:
                raise
            transient_get_errors += 1
            time.sleep(min(15, 3 * transient_get_errors))
            continue
        if state["status"] == "completed":
            break
        if state["status"] in {"failed", "error", "cancelled", "canceled"}:
            raise ValueError("Frontend image task failed; state preserved, no automatic resubmission")
        if time.monotonic() >= deadline:
            raise ValueError("Frontend image task still pending; rerun the same output to resume without POST")
        time.sleep(3)
    raw = provider_path.read_bytes()
    receipt = {"source_kind": "website_frontend_session", "task_id": state["task_id"],
               "task_state": str(state_path), "provider_original": str(provider_path),
               "request_sha256": state["request_sha256"], "api_base_url": client.base_url,
               "post_attempts": state["post_attempts"], "actual_model_verified": False,
               "verified_task_aliases": state.get("verified_task_aliases", []),
               "quality_parameter_sent": "quality" in client.generation_parameters,
               "background_parameter_sent": "background" in client.generation_parameters,
               "output_format_parameter_sent": "output_format" in client.generation_parameters,
               "generation_parameters_sent": client.generation_parameters,
               "generation_parameters_support_verified": False,
               "transparency_requested_in_prompt": fields["background"] == "transparent"}
    return {"data": [{"b64_json": base64.b64encode(raw).decode("ascii")}]}, receipt


def api_transport():
    selected = os.environ.get("UFE_IMAGE_TRANSPORT", "").strip().lower()
    if selected and selected not in {"curl", "urllib"}:
        raise ValueError("UFE_IMAGE_TRANSPORT must be curl or urllib")
    return selected or ("curl" if os.name == "nt" and shutil.which("curl.exe") else "urllib")


def curl_quote(value):
    # Credentials/config stay on stdin, never in argv, a shell, or a config file.
    if any(char in value for char in "\r\n\0"):
        raise ValueError("Image API configuration cannot contain line breaks")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def image_request_timeout():
    """大幅群像可显式延长等待；默认不变，不自动重发未知完成状态的请求。"""
    try:
        seconds = int(os.environ.get("UFE_IMAGE_TIMEOUT", "240"))
    except ValueError:
        raise ValueError("UFE_IMAGE_TIMEOUT must be an integer from 30 to 900") from None
    if not 30 <= seconds <= 900:
        raise ValueError("UFE_IMAGE_TIMEOUT must be an integer from 30 to 900")
    return seconds


def request_curl(url, token, endpoint, data, content_type):
    executable = shutil.which("curl.exe" if os.name == "nt" else "curl")
    if not executable:
        raise ValueError("Configured curl transport is unavailable; no fallback request sent")
    timeout_seconds = image_request_timeout()
    with tempfile.TemporaryDirectory(prefix="ufe-image-") as folder:
        options = ["silent", "show-error", "fail-with-body", "retry = 0",
                   f"max-time = {timeout_seconds}", "connect-timeout = 30", 'proto = "=https"',
                   "url = " + curl_quote(url + endpoint),
                   "header = " + curl_quote("Authorization: Bearer " + token),
                   "header = " + curl_quote("Content-Type: " + content_type),
                   'write-out = "\\nUFE_HTTP_STATUS:%{http_code}"']
        if data is not None:
            payload = Path(folder) / "payload.bin"
            payload.write_bytes(data)
            options.extend(['request = "POST"', "data-binary = " + curl_quote("@" + payload.as_posix())])
        try:
            response = subprocess.run([executable, "--disable", "--config", "-"],
                                      input=("\n".join(options) + "\n").encode("utf-8"),
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout_seconds + 10,
                                      creationflags=0x08000000 if os.name == "nt" else 0)
        except (OSError, subprocess.TimeoutExpired):
            raise ValueError("Image API transport interrupted; remote completion/billing unknown; no automatic retry") from None
    body, marker, status = response.stdout.rpartition(b"\nUFE_HTTP_STATUS:")
    if marker and status.isdigit() and int(status) >= 400:
        raise ValueError(f"Image API HTTP {int(status)}; no automatic retry; response body withheld")
    if response.returncode or not marker or not status.isdigit() or not 200 <= int(status) < 300:
        raise ValueError("Image API transport failed; remote completion/billing unknown; no automatic retry")
    try:
        return json.loads(body)
    except (ValueError, UnicodeError):
        raise ValueError("Image response was interrupted or invalid; no automatic retry; response body withheld") from None


def request_api(url, token, endpoint, data=None, content_type="application/json"):
    if not token:
        raise ValueError("No image credential. Set UFE_IMAGE_API_KEY or configure the active Codex provider.")
    if urllib.parse.urlsplit(url).scheme != "https":
        raise ValueError("Image API base URL must use HTTPS.")
    if api_transport() == "curl":
        return request_curl(url, token, endpoint, data, content_type)
    headers = {"Authorization": "Bearer " + token, "Content-Type": content_type}
    req = urllib.request.Request(url + endpoint, data=data, headers=headers)
    try:
        # Do not retry automatically: generation requests may be billable.
        with urllib.request.urlopen(req, timeout=image_request_timeout()) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise ValueError(f"Image API HTTP {exc.code}; no automatic retry. Check provider endpoint/model support.") from None
    except urllib.error.URLError:
        raise ValueError("Image API connection failed; credentials and response body withheld.") from None
    except (http.client.IncompleteRead, TimeoutError, ssl.SSLError, json.JSONDecodeError):
        raise ValueError("Image response was interrupted. Request may have completed remotely; no automatic retry.") from None


def multipart(fields, images, mask=None):
    boundary = "UFEneo" + uuid.uuid4().hex
    chunks = []
    for name, value in fields.items():
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    for index, path in enumerate(images):
        mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="image[]"; filename="reference-{index}{path.suffix}"\r\nContent-Type: {mime}\r\n\r\n'.encode())
        chunks.extend([path.read_bytes(), b"\r\n"])
    if mask:
        chunks.append(f'--{boundary}\r\nContent-Disposition: form-data; name="mask"; filename="mask.png"\r\nContent-Type: image/png\r\n\r\n'.encode())
        chunks.extend([mask.read_bytes(), b"\r\n"])
    chunks.append(f"--{boundary}--\r\n".encode())
    return b"".join(chunks), "multipart/form-data; boundary=" + boundary


def concept(args):
    brief = json.loads(args.brief.read_text(encoding="utf-8"))
    generate_image(args, brief, "concept candidate, NOT approved runtime animation")


def alpha_report(image):
    """Measure visible content and actual clear pixels, not merely the RGBA mode."""
    rgba = image.convert("RGBA")
    histogram = rgba.getchannel("A").histogram()
    total = image.width * image.height
    # Ignore faint alpha specks when finding the subject/matte. A nearly clear
    # pixel outside a solid rectangle must not make that rectangle look valid.
    bounds = rgba.getchannel("A").point(lambda a: 255 if a >= 128 else 0).getbbox()
    matte = False
    if bounds:
        x0, y0, x1, y1 = bounds
        corners = [rgba.getpixel(p) for p in [(x0, y0), (x1 - 1, y0), (x0, y1 - 1), (x1 - 1, y1 - 1)]]
        matte = all(p[3] >= 200 for p in corners) and all(max(p[c] for p in corners) - min(p[c] for p in corners) < 6 for c in range(3))
    return {"transparent_fraction": histogram[0] / total,
            "visible_fraction": sum(histogram[128:]) / total,
            "nonzero_fraction": sum(histogram[1:]) / total,
            "opaque_fraction": histogram[255] / total,
            "has_alpha_channel": "A" in image.getbands() or "transparency" in image.info,
            "rectangular_matte": matte,
            "clear_corners": all(rgba.getpixel(p)[3] == 0 for p in
                                 [(0, 0), (image.width-1, 0), (0, image.height-1), (image.width-1, image.height-1)])}


def alpha_accepted(report):
    return report["has_alpha_channel"] and report["clear_corners"] and not report.get("rectangular_matte", False) and report["transparent_fraction"] >= 0.05 and report["visible_fraction"] >= 0.01


def require_transparency(image):
    report = alpha_report(image)
    if not alpha_accepted(report):
        raise ValueError("Character image requires real transparency and visible content; opaque/empty output rejected.")
    return report


def clear_hidden_rgb(image):
    """Normalize invisible RGB without touching alpha or any visible/AA pixel."""
    rgba = image.convert("RGBA")
    clear = rgba.getchannel("A").point(lambda alpha: 255 if alpha == 0 else 0)
    rgba.paste((0, 0, 0, 0), mask=clear)
    return rgba


def image_fields(brief, model=None):
    background = "opaque" if brief.get("asset_kind") == "background" else "transparent"
    prompt = brief["prompt"]
    if background == "transparent":
        prompt += "\n透明背景，真正的 PNG Alpha 透明通道。角色之外完全透明；不要红底、品红底、白底、棋盘格、地面、投影或背景。Transparent background, real alpha, isolated subject."
    size = brief.get("size", "1024x1024")
    if size != "auto":
        match = re.fullmatch(r"([1-9][0-9]*)x([1-9][0-9]*)", str(size))
        if not match:
            raise ValueError("Image size must be auto or WIDTHxHEIGHT")
        width, height = map(int, match.groups())
        if width % 16 or height % 16 or max(width, height) > 3840 or max(width, height) > 3 * min(width, height) or not 655360 <= width * height <= 8294400:
            raise ValueError("Image dimensions require multiples of 16, ratio within 3:1, edges <=3840 and 655360..8294400 total pixels")
    return {"model": endpoint_model(model or brief.get("model", "gpt-image-2.5-sunburst")),
            "prompt": prompt, "size": size,
            "quality": brief.get("quality", "low"), "n": 1,
            "background": background, "output_format": "png"}


SLOT_DIR = Path(tempfile.gettempdir()) / "ufeneo-image-slots"


class image_slot:
    """跨进程锁由操作系统持有，退出或进程崩溃时释放；不按时间删除活锁。"""

    _MARKER = b"ufeneo-os-image-slot-v1\n"

    @staticmethod
    def _try_lock(handle):
        import errno
        try:
            if os.name == "nt":
                import msvcrt
                os.lseek(handle, 0, os.SEEK_SET)
                msvcrt.locking(handle, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True
        except OSError as exc:
            if exc.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK) or getattr(exc, "winerror", None) in (33, 36, 158):
                return False
            raise

    @staticmethod
    def _unlock(handle):
        if os.name == "nt":
            import msvcrt
            os.lseek(handle, 0, os.SEEK_SET)
            msvcrt.locking(handle, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle, fcntl.LOCK_UN)

    def __enter__(self):
        local = local_image_config()
        route = image_route(local)
        count = max(1, int(os.environ.get("UFE_IMAGE_SLOTS") or local.get("slots", 2)))
        if "max_slots" in local:
            maximum = int(local["max_slots"])
            if maximum < 1:
                raise ValueError("max_slots must be positive")
            count = min(count, maximum)
        if route == "frontend_session":
            count = 1  # 用户对网页会话明确只允许一个生成任务。
        SLOT_DIR.mkdir(parents=True, exist_ok=True)
        announced = False
        while True:
            for index in range(count):
                path = SLOT_DIR / f"slot-{index}.lock"
                try:
                    handle = os.open(path, os.O_CREAT | os.O_EXCL | os.O_RDWR | getattr(os, "O_BINARY", 0), 0o600)
                    try:
                        if os.write(handle, self._MARKER) != len(self._MARKER):
                            raise OSError("Incomplete image slot marker")
                        os.fsync(handle)
                    except BaseException:
                        os.close(handle)
                        raise
                except FileExistsError:
                    try:
                        handle = os.open(path, os.O_RDWR | getattr(os, "O_BINARY", 0))
                    except FileNotFoundError:
                        continue
                try:
                    if not self._try_lock(handle):
                        os.close(handle)
                        continue
                    os.lseek(handle, 0, os.SEEK_SET)
                    if os.read(handle, len(self._MARKER) + 1) != self._MARKER:
                        # 不接管也不删除旧版/未知锁；其持有者可能仍在运行。
                        self._unlock(handle)
                        os.close(handle)
                        continue
                    self.handle, self.path = handle, path
                    return self
                except BaseException:
                    os.close(handle)
                    raise
            if not announced:
                print("waiting for a free image request slot", file=sys.stderr)
                announced = True
            time.sleep(2)

    def __exit__(self, *exc):
        handle = self.handle
        self.handle = None
        try:
            self._unlock(handle)
        finally:
            os.close(handle)
        return False


def generate_image(args, brief, purpose):
    from PIL import Image
    from catalogue_identity import require_catalogue_generation
    require_catalogue_generation(args, brief)
    fields = image_fields(brief, args.model)
    route = image_route()
    if route == "frontend_session":
        profile = json.loads(frontend_profile_path().read_text(encoding="utf-8"))
        fields["model"] = profile["model"]
        if fields["size"] == "auto":
            raise ValueError("Frontend image route needs explicit canvas dimensions")
    mask = getattr(args, "mask", None)
    if mask:
        if not args.reference:
            raise ValueError("An edit mask needs its image as the first reference")
        with Image.open(mask) as check, Image.open(args.reference[0]) as first:
            if check.format != "PNG" or first.format != "PNG" or check.size != first.size or "A" not in check.getbands():
                raise ValueError("Edit mask and first image must be same-size PNGs with mask Alpha")
            histogram = check.getchannel("A").histogram()
            if not histogram[0] or not histogram[255]:
                raise ValueError("Edit mask needs both editable and protected pixels")
    if not fields["model"].startswith("gpt-image-"):
        raise ValueError("Art generation is restricted to GPT Image models.")
    endpoint = "/images/edits" if args.reference else "/images/generations"
    if route == "frontend_session":
        if mask:
            raise ValueError("Observed frontend protocol does not expose mask editing; no request sent")
        endpoint = "/images/generate"
    if args.dry_run:
        print(json.dumps({"endpoint": endpoint, "request": fields, "reference_count": len(args.reference),
                          "mask": str(mask) if mask else None, "output": str(args.out)}, ensure_ascii=False, indent=2))
        return
    if args.out.exists() or (args.out.parent / "rejected" / args.out.name).exists():
        raise ValueError("Output exists; choose a new candidate filename.")
    frontend_receipt = None
    official_receipt = None
    if route == "frontend_session":
        with image_slot():
            result, frontend_receipt = frontend_image_result(args, fields)
        url = frontend_receipt["api_base_url"]
    else:
        if args.reference:
            payload, mime = multipart(fields, args.reference, mask)
        else:
            payload, mime = json.dumps(fields).encode(), "application/json"
        url, token = credentials()
        with image_slot():
            budget = None
            local = local_image_config()
            if urllib.parse.urlsplit(url).hostname == "api.openai.com" or local.get("official_budget"):
                from image_budget import OfficialImageBudget
                budget = OfficialImageBudget(local, url, fields, args.reference)
                budget.begin()
            result = request_api(url, token, endpoint, payload, mime)
            if budget:
                official_receipt = budget.complete(result)
    item = result.get("data", [{}])[0]
    if not item.get("b64_json"):
        raise ValueError("Provider returned no inline image. Expected data[0].b64_json.")
    raw = base64.b64decode(item["b64_json"], validate=True)
    if official_receipt:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.with_name(args.out.stem + ".provider.png").write_bytes(raw)
    image = Image.open(io.BytesIO(raw))
    image.load()
    provider_alpha = alpha_report(image)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    provider_size = list(image.size)
    resized = padded = False
    if fields["size"] != "auto":
        want = tuple(map(int, fields["size"].split("x")))
        if (image.size != want and fields["background"] == "transparent"
                and abs(image.size[0] * want[1] - image.size[1] * want[0]) > 0.01 * image.size[0] * want[1]):
            # Text-only requests on the user's endpoint ignore size (e.g. 1145x1374 for 1024x1024).
            # Pad with clear pixels to the requested aspect (centred, bottom kept), never crop or stretch.
            image.save(args.out.with_name(args.out.stem + ".provider.png"), format="PNG")
            w, h = image.size
            cw, ch = max(w, -(-h * want[0] // want[1])), max(h, -(-w * want[1] // want[0]))
            canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
            canvas.paste(image.convert("RGBA"), ((cw - w) // 2, ch - h))
            image, padded = canvas, True
        if image.size != want and abs(image.size[0] * want[1] - image.size[1] * want[0]) <= 0.01 * image.size[0] * want[1]:
            # The user's endpoint returns 1254x1254 for a 1024x1024 request; keep the original and
            # hand the pipeline the requested canvas (same aspect, premultiplied Lanczos).
            if not padded:
                image.save(args.out.with_name(args.out.stem + ".provider.png"), format="PNG")
            image = image.convert("RGBA").resize(want, Image.Resampling.LANCZOS)
            resized = True
        elif image.size != want:
            print(f"warning: provider returned {image.size[0]}x{image.size[1]} for {fields['size']} (aspect differs; not resized)")
    alpha = alpha_report(image)
    accepted = fields["background"] != "transparent" or (alpha_accepted(provider_alpha) and alpha_accepted(alpha))
    if fields["background"] == "transparent":
        # Some previews expose RGB beneath alpha=0. Keep transparent areas clean
        # at the candidate stage too, not only when installing reviewed keyart.
        image = clear_hidden_rgb(image)
    destination = args.out if accepted else args.out.parent / "rejected" / args.out.name
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG")
    metadata = {"purpose": purpose, "model": fields["model"],
                "requested_model": args.model or brief.get("model", "gpt-image-2.5-sunburst"),
                "endpoint_host": urllib.parse.urlsplit(url).hostname,
                "asset_kind": brief.get("asset_kind", "character"),
                "references": [{"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in args.reference],
                "endpoint": endpoint, "prompt_sha256": hashlib.sha256(brief["prompt"].encode()).hexdigest(),
                "request_sha256": hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest(),
                "background_requested": fields["background"], "output_format": "png",
                "requested_size": fields["size"], "requested_quality": fields["quality"],
                "api_transport": api_transport(),
                "request_timeout_seconds": image_request_timeout(),
                "alpha": alpha, "provider_alpha": provider_alpha, "transparency_accepted": accepted,
                "provider_image_sha256": hashlib.sha256(raw).hexdigest(),
                "hidden_rgb_cleanup": "alpha=0 -> RGBA=0; visible and antialiased pixels unchanged" if fields["background"] == "transparent" else None,
                "image_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
                "dimensions": list(image.size), "provider_dimensions": provider_size,
                "resized_to_requested_size": resized, "padded_to_requested_aspect": padded,
                "created_unix": int(time.time())}
    if frontend_receipt:
        metadata.update(frontend_receipt)
        metadata["api_transport"] = "frontend_session_https"
    if official_receipt:
        metadata["official_billing"] = official_receipt
    if getattr(args, "pose_guide", None):
        metadata["pose_guide"] = {"path": str(args.pose_guide),
            "sha256": hashlib.sha256(args.pose_guide.read_bytes()).hexdigest(),
            "role": "abstract_motion_constraints_not_identity_or_runtime_art"}
    if mask:
        metadata["edit_mask"] = {"path": str(mask), "sha256": hashlib.sha256(mask.read_bytes()).hexdigest(),
                                 "role": "generation_constraint_not_a_guarantee_of_preserved_pixels"}
    if getattr(args, "layer_spec", None):
        metadata["partial_layer"] = {"path": str(args.layer_spec),
            "sha256": hashlib.sha256(args.layer_spec.read_bytes()).hexdigest(),
            "role": "declared_partial_body_motion_not_a_complete_fighter"}
    if getattr(args, "parts_spec", None):
        metadata["rig_parts"] = {"path": str(args.parts_spec),
            "sha256": hashlib.sha256(args.parts_spec.read_bytes()).hexdigest(),
            "role": "native_rig_components_not_motion_or_fighter", "production_eligible": False}
    destination.with_suffix(".metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    if not accepted:
        reasons = []
        if not alpha_accepted(provider_alpha):
            reasons.append("provider original is not genuinely transparent")
        if not alpha["has_alpha_channel"]:
            reasons.append("missing Alpha channel")
        if not alpha["clear_corners"]:
            reasons.append("nonclear corner pixels")
        if alpha.get("rectangular_matte"):
            reasons.append("rectangular matte")
        if alpha["transparent_fraction"] < 0.05:
            reasons.append("insufficient fully transparent pixels")
        if alpha["visible_fraction"] < 0.01:
            reasons.append("insufficient visible content")
        raise ValueError("Image Alpha QA failed (" + ", ".join(reasons) + "). Output quarantined in rejected/; no automatic retry.")
    print("GPT Image output saved:", args.out)


def row_paths(run, state):
    """Resolve layout through sprite-gen's SSoT in its own interpreter."""
    script = ("import json,sys; from sprite_gen.spec.layout import prompt_rel,guide_rel,raw_rel; "
              "r=json.load(open(sys.argv[1],encoding='utf-8')); s=sys.argv[2]; "
              "print(json.dumps([prompt_rel(r,s),guide_rel(r,s),raw_rel(r,s)]))")
    result = subprocess.run([str(skill_python()), "-c", script, str(run / "sprite-request.json"), state],
                            cwd=SPRITE_ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
    return [run / path for path in json.loads(result.stdout)]


def take_paths(run, state, label):
    """Use upstream prompt/guide generation and take-path SSoT for a declared take."""
    script = '''import json,sys
from pathlib import Path
Path = _LayoutProjectPath
from sprite_gen.spec.layout import take_raw_rel
from sprite_gen.spec.runio import publish_guard,atomic_write_text
from sprite_gen.gen.prepare import draw_guide,row_prompt
run=Path(sys.argv[1]); state=sys.argv[2]; label=sys.argv[3]
with publish_guard(run):
    request=json.loads((run/'sprite-request.json').read_text(encoding='utf-8'))
    spec=next(t for t in request['states'][state]['takes'] if t['label']==label)
    entry={**request['states'][state],**spec}
    prompt=Path('prompts')/(state+'.takes')/(label+'.txt')
    guide=Path('references/layout-guides')/(state+'.takes')/(label+'.png')
    (run/prompt).parent.mkdir(parents=True,exist_ok=True)
    (run/guide).parent.mkdir(parents=True,exist_ok=True)
    draw_guide(run/guide,state,int(spec['frames']),request['cell'])
    atomic_write_text(run/prompt,row_prompt(request,state,entry).rstrip()+'\\n')
    print(json.dumps([prompt.as_posix(),guide.as_posix(),take_raw_rel(request,state,label)]))
'''
    result = subprocess.run([str(skill_python()), "-c", script, str(run), state, label],
                            cwd=SPRITE_ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
    return [run / path for path in json.loads(result.stdout)]


def row(args, *, generator=None):
    run = args.run.resolve()
    request = json.loads((run / "sprite-request.json").read_text(encoding="utf-8"))
    if args.state not in request["states"] or not re.fullmatch(r"[a-z][a-z0-9_]*", args.state):
        raise ValueError("State must be declared in sprite-request.json.")
    if request.get("directions"):
        raise ValueError("This adapter currently supports the single-facing fighting template; use one run per facing.")
    if getattr(args, "parts_spec", None):
        if args.state == "idle" or any(getattr(args, key, None) for key in ("layer_spec", "anchor_edit", "pose_guide", "take")):
            raise ValueError("Rig parts require accepted idle and cannot combine with motion/edit/take adapters")
        from combat_rig_parts import adapt as adapt_rig_parts, validate as validate_rig_parts
        validate_rig_parts(args.parts_spec, request["cell"], args.state, int(request["states"][args.state]["frames"]))
        purpose_path = run / "component-purpose.json"
        purpose = {"kind": "ufe-rig-component-study", "production_eligible": False,
                   "state": args.state, "spec_sha256": hashlib.sha256(args.parts_spec.read_bytes()).hexdigest()}
        if purpose_path.exists() and json.loads(purpose_path.read_text(encoding="utf-8")) != purpose:
            raise ValueError("Rig component declaration changed; use a new run")
    if getattr(args, "layer_spec", None):
        if args.state == "idle" or getattr(args, "anchor_edit", None):
            raise ValueError("Partial rows require accepted idle and cannot also use a full-body edit canvas")
        from combat_partial_row import adapt as adapt_partial_row, validate as validate_partial_row
        partial_declaration = validate_partial_row(args.layer_spec, request["cell"], args.state)
        if partial_declaration.get("generation_scope") == "full_body_context":
            context_path = run / "component-purpose.json"
            context = {"kind": "ufe-full-body-context-for-upper-layer", "production_eligible": False,
                       "state": args.state, "spec_sha256": hashlib.sha256(args.layer_spec.read_bytes()).hexdigest()}
            if context_path.exists():
                prior = json.loads(context_path.read_text(encoding="utf-8"))
                if any(prior.get(key) != context[key] for key in context):
                    raise ValueError("Full-body context declaration changed; use a new run")
            else:
                context_path.write_text(json.dumps(context, indent=2) + "\n", encoding="utf-8")
    take = getattr(args, "take", None)
    if take and (not re.fullmatch(r"[a-z][a-z0-9_]*", take) or not any(
            t.get("label") == take for t in request["states"][args.state].get("takes", []))):
        raise ValueError("Take must be declared in this state's request.")
    if getattr(args, "pose_guide", None):
        from combat_pose_guide import overlay, validate as validate_pose_guide
        row_spec = request["states"][args.state]
        if take:
            row_spec = next(t for t in row_spec["takes"] if t["label"] == take)
        # Reject invalid constraints before redrawing any existing layout.
        validate_pose_guide(args.pose_guide, request["cell"], int(row_spec["frames"]))
    if getattr(args, "anchor_edit", None):
        if args.state == "idle":
            raise ValueError("Masked action edits require a separately accepted idle")
        from combat_edit_canvas import build as build_edit_canvas, validate as validate_edit_canvas
        edit_spec = request["states"][args.state]
        if take:
            edit_spec = next(t for t in edit_spec["takes"] if t["label"] == take)
        validate_edit_canvas(args.anchor_edit, request["cell"], int(edit_spec["frames"]))
    from motion_evidence import require_row_evidence
    # Declared static rig pieces have no start/contact/recovery motion. Their
    # identity, cutout hashes and non-production status are validated separately.
    motion_record = None if getattr(args, "parts_spec", None) else require_row_evidence(request, args.state)
    motion_visual_mode = getattr(args, "motion_visual_mode", "source_frames")
    if motion_visual_mode not in {"source_frames", "descriptions"}:
        raise ValueError("Unknown motion visual reference mode")
    if motion_visual_mode == "descriptions" and (
            not motion_record or motion_record.get("kind") != "gameplay_clip"):
        raise ValueError("Description-only motion references require reviewed PS2 locomotion evidence")
    primary_paths = row_paths(run, args.state)
    prompt, guide, output = take_paths(run, args.state, take) if take else primary_paths
    if getattr(args, "pose_guide", None):
        # Redraw through the upstream owner so a changed blueprint cannot leave
        # stale bones from a previous dry run on the layout reference.
        script = ("import json,sys; from pathlib import Path; from sprite_gen.gen.prepare import draw_guide; "
                  "r=json.load(open(sys.argv[1],encoding='utf-8')); "
                  "draw_guide(Path(sys.argv[4]),sys.argv[2],int(sys.argv[3]),r['cell'], "
                  "motion_phase_guides=bool(r.get('motion_phase_guides')))")
        subprocess.run([str(skill_python()), "-c", script, str(run / "sprite-request.json"),
                        args.state, str(row_spec["frames"]), str(guide)], cwd=SPRITE_ROOT, check=True)
        overlay(guide, args.pose_guide, request["cell"], int(row_spec["frames"]))
    if args.state == "idle" and not take:
        candidates = list(run.glob("base-source.*"))
        if len(candidates) != 1:
            raise ValueError("Expected one locked base source for idle generation.")
        identity = candidates[0]
    else:
        identity = run / "references/anchors/accepted-idle.png"
        lock = run / "references/anchors/accepted-idle.json"
        if not identity.exists() or not lock.exists():
            raise ValueError("Generate/extract/curate idle, export curated PNGs, then lock-idle before action rows.")
        if json.loads(lock.read_text())["sha256"] != hashlib.sha256(identity.read_bytes()).hexdigest():
            raise ValueError("Idle anchor changed after lock; review it again.")
    args.out = output
    args.reference = [identity, guide]
    if take:
        basis = primary_paths[2]
        metadata = basis.with_suffix(".metadata.json")
        if not basis.exists() or not metadata.exists() or json.loads(metadata.read_text(encoding="utf-8")).get("image_sha256") != hashlib.sha256(basis.read_bytes()).hexdigest():
            raise ValueError("Take requires an unchanged primary row as its motion basis.")
        args.reference.append(basis)
    adapted = transparent_row_prompt(prompt.read_text(encoding="utf-8"))
    if getattr(args, "pose_guide", None):
        adapted += ("\n布局图上的橙色路径是靠镜头的手臂，青色路径是远侧手臂，灰色路径是躯干与腿。"
                    "按每格肩、肘、腕及腿部节点改变姿势，尤其检查第一与最后一格的双臂前后职责。"
                    "这些颜色和骨架线只标注运动约束，人物造型、红银皮套与像素画风仍完全来自唯一身份锚点；"
                    "输出绝不保留骨架线、节点、参考颜色、图框或文字。")
    if request.get("subject") == "effect":
        adapted = effect_row_prompt(adapted)
    if getattr(args, "layer_spec", None):
        adapted, crop = adapt_partial_row(identity, args.layer_spec, request["cell"], args.state,
            adapted, run / "references/partial-rows" / args.state / (take or "primary"))
        args.reference.insert(1, crop)
    if getattr(args, "parts_spec", None):
        adapted, crop, parts_guide = adapt_rig_parts(identity, args.parts_spec, request["cell"], args.state,
            int(request["states"][args.state]["frames"]), adapted, guide,
            run / "references/rig-parts" / args.state)
        args.reference = [identity, crop, parts_guide]
        parts_declaration = json.loads(args.parts_spec.read_text(encoding="utf-8"))
        if parts_declaration.get("edit_from_cutout"):
            from combat_rig_edit import build as build_rig_edit
            canvas, args.mask = build_rig_edit(identity, parts_declaration,
                run / "references/rig-parts" / args.state / "edit")
            args.reference.insert(0, canvas)
            adapted += ("\n局部编辑输入优先：现在第1张是精确排好的独立部件编辑画布，"
                        "第2张是唯一精修idle，第3张是它的放大裁图，第4张是关节引导。"
                        "保持第1张画布的尺寸、格子布局、部件像素密度、位置、角度、长度与颜色。"
                        "蒙版Alpha=0仅允许补画缺失的关节遮挡衣料和整理轮廓，Alpha=255保留原像素。"
                        "补画处沿用原图红银衣料，不画圆盘截面、端盖、护甲或外加关节。"
                        "透明区域仍必须透明，输出真正PNG Alpha。画布是编辑参考，不是已验收部件。")
            if parts_declaration.get("masked_completion_only"):
                from media.materials.part_completion import prompt as completion_prompt
                args.reference = [canvas, identity]
                adapted = completion_prompt(parts_declaration["parts"][0])
                (run / "references/rig-parts" / args.state / "completion-prompt.txt").write_text(adapted+"\n", encoding="utf-8")
        purpose_path.write_text(json.dumps(purpose, indent=2) + "\n", encoding="utf-8")
    if getattr(args, "anchor_edit", None):
        canvas, args.mask = build_edit_canvas(identity, args.anchor_edit, request["cell"],
            int(edit_spec["frames"]), run / "references/action-edits" / args.state / (take or "primary"))
        args.reference.insert(0, canvas)
        adapted += "\n局部编辑：第1张图是由接受的idle精确排成的编辑输入，蒙版Alpha=0区域允许改变，Alpha=255区域保持原像素。仅在可编辑区域完成本段各姿势，不改变画布布局、头盔、身高、双腿、脚位或像素密度；禁止重排、缩放或整体重画。全保护的格子保持原idle。第2张是唯一人物身份锚点，布局骨架只约束运动阶段。输出仍必须是透明背景、真正PNG Alpha；编辑输入的重复idle不是动作成品。"
    # Enlarge the identity reference only. The generated art still goes through
    # measured-grid extraction; this never rescales a generated runtime frame.
    identity_reference = identity
    identity_scale = getattr(args, "identity_scale", 1)
    if type(identity_scale) is not int or not 1 <= identity_scale <= 8:
        raise ValueError("Identity reference scale must be an integer from 1 to 8")
    if identity_scale > 1:
        from PIL import Image
        identity_reference = identity.with_name(identity.stem + f"-x{identity_scale}.png")
        with Image.open(identity) as original:
            original.resize((original.width*identity_scale,original.height*identity_scale), Image.Resampling.NEAREST).save(identity_reference)
        args.reference = [identity_reference if path == identity else path for path in args.reference]
        adapted += f"\n身份参考是同一锁定锚点的{identity_scale}倍整数最近邻显示图，用于清楚展示真实硬像素块；没有新增人物设计。逐块保留参考的硬边和色块，禁止抗锯齿、渐变或插画描边。"
    if motion_record and not getattr(args, "parts_spec", None):
        # Resolve after adapters insert crops/edit canvases, so reference
        # numbers remain correct. Descriptions retain the same evidence gate.
        motion_start = len(args.reference) + 1
        identity_index = args.reference.index(identity_reference) + 1
        source_name = "PS2实机步法" if motion_record.get("kind") == "gameplay_clip" else "原剧动作"
        if motion_visual_mode == "source_frames":
            args.reference.extend(ROOT / pose["file"] for pose in motion_record["key_poses"])
            adapted += (f"\n{source_name}依据：第{motion_start}张起是已核对、按时间排列的来源关键帧，"
                        "仅参考角色的可见姿势、手型和关节方向，不复制摄影、背景、其他角色或写实材质。")
        else:
            adapted += (f"\n{source_name}依据使用已审查的文字观察，原帧不作为图像风格输入；"
                        "这是有来源限制的Neo步法改编，不宣称原版逐帧动作或精确接触时序。"
                        "连续捕获及原帧在任务来源中按哈希绑定。")
            for pose in motion_record["key_poses"]:
                adapted += f"\n来源{pose['phase']}，{pose['time_ms']}毫秒：{pose['observation']}"
        adapted += (
                    f"像素风格、人物比例和身份始终以第{identity_index}张锁定像素锚点为准。"
                    "记录覆盖范围：" + motion_record.get("coverage", "见关键帧观察") + "。"
                    "限制：" + "；".join(motion_record.get("adaptation_limits", [])))
    brief = {"prompt": adapted, "size": args.size, "quality": args.quality,
             "asset_kind": "effect" if request.get("subject") == "effect" else "sprite"}
    purpose_text = ("raw static rig components; requires deterministic extraction and assembly QA; not motion or a fighter"
                    if getattr(args, "parts_spec", None) else
                    "raw component-row intermediate, requires deterministic extraction and motion QA")
    (generator or generate_image)(args, brief, purpose_text)


def transparent_row_prompt(prompt):
    """Override the upstream chroma instructions without altering identity/motion."""
    prompt = re.sub(r"(?m)^- Use a perfectly flat pure .* chroma-key background across the whole image\.$",
                    "- 透明背景，真正的 PNG Alpha；角色之间和画面四周完全透明。", prompt)
    prompt = re.sub(r"(?m)^- Do not use .*chroma-adjacent colors.*(?:\n|$)", "", prompt)
    return prompt


def effect_row_prompt(prompt):
    """Keep the upstream count/layout contract while declaring a standalone FX row."""
    prompt = prompt.replace("game character", "standalone visual effect")
    prompt = prompt.replace("full-body frames", "complete effect frames").replace("full-body pose", "complete effect")
    prompt = prompt.replace(", or impact bursts", "")
    prompt = "\n".join(line for line in prompt.splitlines() if not any(phrase in line for phrase in (
        "This row owns motion only.", "physically touching or overlapping the character silhouette",
        "while animating. Keep face, hair shape", "Preserve side-specific features exactly",
        "When generating a paired left/right row", "For cyclic locomotion,",
        "Preserve the same silhouette, face, proportions, palette, material, and props across every frame.")))
    prompt = prompt.replace("that is not attached to the character", "outside its own frame slot")
    return prompt + ("\n\n独立特效约定：每格只画本行动作声明的一件完整、相连的特效，没有人物或身体。"
                     "idle仅作为效果设计锚点；后续行保持该锚点的颜色、硬像素格、轮廓语言与中心。"
                     "动作阶段严格按本行声明变化，不复制静图冒充动画。中心固定，不画地面或阴影。"
                     "透明背景，真正PNG Alpha。所有可见像素使用硬边色块，不加柔光、模糊或半透明烟雾。")


def lock_idle(args):
    from PIL import Image
    if not args.reviewed:
        raise ValueError("Review identity, pixel grid, full body and pivot before --reviewed.")
    run = args.run.resolve()
    image = args.image.resolve()
    if not image.is_relative_to(run / "curated"):
        raise ValueError("Idle anchor must come from this run's curated PNG export, not raw/pre-curation frames.")
    with Image.open(image) as check:
        require_transparency(check)
    folder = run / "references/anchors"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "accepted-idle.png"
    with Image.open(image) as source:
        source.save(target, format="PNG")
    (folder / "accepted-idle.json").write_text(json.dumps({"source": str(image.relative_to(run)),
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "reviewed": True}, indent=2) + "\n")
    print("Locked curated idle anchor:", target)


def skill_python():
    interpreter = SPRITE_ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not interpreter.exists():
        raise ValueError("sprite-gen venv missing. Run: python tools/art_pipeline.py bootstrap-sprite")
    return interpreter


def skill(script, *args):
    from media.materials.sprite_grid_range import stage
    adapted = stage(script, args, ROOT, SPRITE_ROOT, skill_python())
    if adapted:
        command, environment = adapted
        subprocess.run(command, env=environment, check=True)
    else:
        subprocess.run([str(skill_python()), str(SPRITE_ROOT / "scripts" / script), *map(str, args)], check=True)


def validate_bundle(path):
    from PIL import Image
    path = Path(path).resolve()
    manifest = json.loads(path.read_text(encoding="utf-8"))
    image_rel = Path(manifest["game_input"])
    if image_rel.is_absolute() or ".." in image_rel.parts:
        raise ValueError("game_input must stay inside the bundle.")
    image = Image.open(path.parent / image_rel)
    if image.mode != "RGBA":
        raise ValueError("Runtime atlas must be RGBA with transparent pixels.")
    require_transparency(image)
    layout = manifest["frame_layout"]
    if image.size != (layout["sheetWidth"], layout["sheetHeight"]):
        raise ValueError("Atlas dimensions disagree with frame_layout.")
    rows = layout["rows"]
    timing = manifest["animation"]["rows"]
    if not rows or set(rows) != set(timing):
        raise ValueError("Layout and animation states must match.")
    if manifest.get("degraded_static_fallback") or layout.get("degraded_static_fallback"):
        raise ValueError("Static fallback is not a production sprite animation.")
    count = 0
    for state, rects in rows.items():
        times = timing[state].get("durations_ms", [])
        if not rects or len(rects) != len(times):
            raise ValueError(f"{state}: each frame needs an explicit duration.")
        for index, (rect, duration) in enumerate(zip(rects, times)):
            if not isinstance(duration, (int, float)) or duration <= 0:
                raise ValueError(f"{state}: invalid duration.")
            x, y, w, h = (rect[k] for k in ("x", "y", "w", "h"))
            if any(type(v) is not int for v in (x, y, w, h)) or min(x, y) < 0 or min(w, h) <= 0 or x + w > image.width or y + h > image.height:
                raise ValueError(f"{state}: invalid frame rectangle.")
            # Atlas-wide alpha can hide one opaque/red-matte frame among valid
            # frames. Inspect the exact runtime rectangle for every pose.
            try:
                require_transparency(image.crop((x, y, x + w, y + h)))
            except ValueError as exc:
                raise ValueError(f"{state} frame {index}: {exc}") from exc
            count += 1
    return {"states": sorted(rows), "frames": count, "dimensions": list(image.size)}


def bundle_hash(path):
    manifest = json.loads(path.read_text(encoding="utf-8"))
    return hashlib.sha256(path.read_bytes() + (path.parent / manifest["game_input"]).read_bytes()).hexdigest()


def promote(args):
    if json.loads(args.manifest.read_text(encoding="utf-8")).get("production_eligible") is False:
        raise ValueError("Diagnostic-only content cannot be promoted to runtime")
    purpose_path = args.manifest.parent / "component-purpose.json"
    if purpose_path.exists() and json.loads(purpose_path.read_text(encoding="utf-8")).get("production_eligible") is False:
        raise ValueError("Rig component studies cannot be promoted as fighter animations")
    result = validate_bundle(args.manifest)
    review = json.loads(args.review.read_text(encoding="utf-8"))
    if review.get("bundle_sha256") != bundle_hash(args.manifest):
        raise ValueError("Review does not match these exact atlas + manifest bytes.")
    gates = ["identity", "pixel_grid", "alpha", "pivot", "motion", "timing", "contact_frames"]
    if not review.get("reviewer") or not all(review.get("checks", {}).get(k) is True for k in gates):
        raise ValueError("Review needs a reviewer and every QA gate true.")
    from motion_evidence import require_row_evidence
    request_path = args.manifest.parent / "sprite-request.json"
    if not request_path.exists():
        raise ValueError("Fighter promotion requires the source request and on-screen motion references")
    source_request = json.loads(request_path.read_text(encoding="utf-8"))
    if source_request.get("subject") == "effect" or source_request.get("purpose") == "static_pixel_portrait":
        raise ValueError("Effects and static portraits cannot be promoted as fighters")
    for state in json.loads(args.manifest.read_text(encoding="utf-8"))["animation"]["rows"]:
        require_row_evidence(source_request, state)
    if not re.fullmatch(r"[a-z][a-z0-9_]{1,63}", args.character):
        raise ValueError("Character ID must be lowercase letters, digits and underscores.")
    destination = ROOT / "assets/fighters" / args.character
    if destination.exists():
        raise ValueError("Runtime bundle already exists; use a new content revision ID.")
    destination.mkdir(parents=True)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    atlas = args.manifest.parent / manifest["game_input"]
    shutil.copy2(atlas, destination / "sprite-sheet-alpha.png")
    manifest["game_input"] = "sprite-sheet-alpha.png"
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    shutil.copy2(args.review, destination / "review.json")
    print("Approved runtime bundle:", destination, result)


def doctor(args):
    route = image_route()
    if route == "frontend_session":
        status = {"image_route": route, "image_session": "website_bearer_session",
                  "image_model": "frontend profile; not checked",
                  "sprite_gen_skill": (SPRITE_ROOT / "SKILL.md").exists(),
                  "sprite_gen_venv": (SPRITE_ROOT / ".venv/Scripts/python.exe").exists(),
                  "art_generation": "GPT Image only", "postprocessing": "local open-source tools only",
                  "api_transport": "frontend_session_https"}
        if args.check_api:
            from frontend_session_client import FrontendError, FrontendSessionClient, TASK_ID
            task_id = os.environ.get("UFE_WEB_DOCTOR_TASK_ID") or "ufeneo-doctor-nonexistent"
            if not TASK_ID.fullmatch(task_id):
                raise ValueError("Invalid frontend doctor task ID")
            try:
                client = FrontendSessionClient(frontend_profile_path())
                status["image_model"] = client.model
                data = client._api("GET", "/images/tasks/" + task_id)
                result = "authenticated" if str(data.get("id", "")) == task_id else "unverified_task_id"
                status["frontend_check"] = {"result": result, "http_status": 200}
            except FrontendError as exc:
                status["frontend_check"] = {"result": "session_rejected" if exc.http_status in (401, 403) else "unverified",
                                            "http_status": exc.http_status, "error_code": exc.code}
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return
    url, token = credentials()
    status = {"image_api": "configured" if token else "missing credential", "image_model": endpoint_model("gpt-image-2.5-sunburst"),
              "sprite_gen_skill": (SPRITE_ROOT / "SKILL.md").exists(),
              "sprite_gen_venv": (SPRITE_ROOT / ".venv/Scripts/python.exe").exists(),
              "art_generation": "GPT Image only", "postprocessing": "local open-source tools only",
              "api_transport": api_transport()}
    if args.check_api:
        models = request_api(url, token, "/models")
        status["image_model_available"] = any(x.get("id") == status["image_model"] for x in models.get("data", []))
    print(json.dumps(status, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("doctor"); p.add_argument("--check-api", action="store_true")
    p = commands.add_parser("concept")
    p.add_argument("--brief", type=Path, required=True); p.add_argument("--out", type=Path, required=True)
    p.add_argument("--model"); p.add_argument("--reference", type=Path, action="append", default=[])
    p.add_argument("--mask", type=Path, help="Optional same-size PNG Alpha mask for the first edit reference.")
    p.add_argument("--dry-run", action="store_true")
    p = commands.add_parser("row", help="Generate one raw state row through the same GPT Image API.")
    p.add_argument("--run", type=Path, required=True); p.add_argument("--state", required=True)
    p.add_argument("--take", help="A declared additional segment; uses curated idle plus primary row motion basis.")
    p.add_argument("--parts-spec", type=Path, help="Declared detached rig components; diagnostic only, not motion frames.")
    p.add_argument("--pose-guide", type=Path, help="Abstract joint-path constraints over the upstream layout; never character art.")
    p.add_argument("--anchor-edit", type=Path, help="Masked action-edit specification; uses accepted idle, never raw/final motion fallback.")
    p.add_argument("--layer-spec", type=Path, help="Declared upper-body component row; requires independent seam/motion QA.")
    p.add_argument("--model", default="gpt-image-2.5-sunburst")
    p.add_argument("--identity-scale", type=int, choices=range(1,9), default=1, help="Integer NEAREST display scale for the accepted identity reference only; never runtime output.")
    p.add_argument("--motion-visual-mode", choices=["source_frames", "descriptions"], default="source_frames",
                   help="PS2 locomotion only: retain reviewed source provenance but attach its observations as text instead of photographic style inputs.")
    p.add_argument("--size", default="1536x1024"); p.add_argument("--quality", default="low")
    p.add_argument("--dry-run", action="store_true")
    p = commands.add_parser("lock-idle")
    p.add_argument("--run", type=Path, required=True); p.add_argument("--image", type=Path, required=True)
    p.add_argument("--reviewed", action="store_true")
    commands.add_parser("bootstrap-sprite")
    p = commands.add_parser("prepare")
    p.add_argument("--base", type=Path, required=True); p.add_argument("--character", required=True)
    p.add_argument("--locked", action="store_true", help="Confirm the full-body pixel base passed visual identity/grid review.")
    p.add_argument("--request", type=Path, default=ROOT / "art/shared/specs/sprite-request.template.json")
    p = commands.add_parser("sprite"); p.add_argument("stage", choices=["extract", "preview", "inspect", "compose", "curate", "export"])
    p.add_argument("--run", type=Path, required=True)
    for name in ["validate", "review-hash"]:
        p = commands.add_parser(name); p.add_argument("manifest", type=Path)
    p = commands.add_parser("promote")
    p.add_argument("--manifest", type=Path, required=True); p.add_argument("--review", type=Path, required=True)
    p.add_argument("--character", required=True)
    args, extra = parser.parse_known_args()
    if args.command != "sprite" and extra:
        parser.error("unrecognized arguments: " + " ".join(extra))
    if args.command == "doctor": doctor(args)
    elif args.command == "concept": concept(args)
    elif args.command == "row": row(args)
    elif args.command == "lock-idle": lock_idle(args)
    elif args.command == "bootstrap-sprite":
        if not (SPRITE_ROOT / "pyproject.toml").exists(): raise ValueError("Install the sprite-gen skill first.")
        env = SPRITE_ROOT / ".venv"
        if not env.exists(): subprocess.run([sys.executable, "-m", "venv", str(env)], check=True)
        subprocess.run([str(skill_python()), "-m", "pip", "install", "-e", str(SPRITE_ROOT)], check=True)
    elif args.command == "prepare":
        if not args.locked: raise ValueError("Base lock required: review full body, identity, hard pixel grid and real alpha before --locked.")
        from PIL import Image
        with Image.open(args.base) as base:
            require_transparency(base)
        if not re.fullmatch(r"[a-z][a-z0-9_]{1,63}", args.character): raise ValueError("Invalid character ID")
        out = ROOT / "art/runs" / args.character
        if out.exists(): raise ValueError("Run already exists. Use a new candidate ID.")
        skill("prepare_sprite_run.py", "--out-dir", out, "--character-id", args.character,
              "--base-image", args.base.resolve(), "--request", args.request.resolve())
        # Upstream deliberately drops application-specific fields. Restore our
        # source contract so preparing a run cannot silently erase its evidence.
        source_request = json.loads(args.request.read_text(encoding="utf-8"))
        prepared_path = out / "sprite-request.json"
        prepared = json.loads(prepared_path.read_text(encoding="utf-8"))
        for key in ("source_character_id", "source_form", "chroma"):
            if key in source_request:
                prepared[key] = source_request[key]
        for state, spec in source_request.get("states", {}).items():
            for key in ("motion_evidence", "takes"):
                if key in spec:
                    prepared["states"][state][key] = spec[key]
        prepared_path.write_text(json.dumps(prepared, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    elif args.command == "sprite":
        scripts = {"extract": "extract_sprite_row_frames.py",
                   "preview": "preview_animation.py", "inspect": "inspect_sprite_run.py",
                   "compose": "compose_sprite_atlas.py", "curate": "serve_curation.py", "export": "export_curated_pngs.py"}
        forwarded = extra[1:] if extra and extra[0] == "--" else extra
        skill(scripts[args.stage], "--run-dir", args.run.resolve(), *forwarded)
    elif args.command == "validate": print(json.dumps(validate_bundle(args.manifest), indent=2))
    elif args.command == "review-hash":
        validate_bundle(args.manifest); print(bundle_hash(args.manifest))
    elif args.command == "promote": promote(args)


if __name__ == "__main__":
    from frontend_session_client import FrontendError
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError, FrontendError) as exc:
        print("Art pipeline:", str(exc), file=sys.stderr)
        sys.exit(1)
