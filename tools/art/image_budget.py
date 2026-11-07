"""官方生图的本机预算：先占额再POST；未知结果不自动释放或重发。"""
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation, ROUND_UP
import hashlib
import json
import os
from pathlib import Path
import time
import uuid


@contextmanager
def _locked(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix('.lock').open('a+b') as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b'1')
            handle.flush()
        while True:
            try:
                handle.seek(0)
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except (BlockingIOError, PermissionError):
                time.sleep(0.05)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)


def _money(value):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError('Invalid official image budget amount') from None
    if not amount.is_finite() or amount < 0:
        raise ValueError('Invalid official image budget amount')
    return amount


def usage_cost(usage):
    """直接Images API不扣缓存折扣；未知输入类型按较贵的图像输入计。"""
    if not isinstance(usage, dict):
        return None
    def tokens(value):
        if type(value) is not int or value < 0:
            raise ValueError('Invalid official image usage')
        return value
    try:
        incoming = tokens(usage['input_tokens'])
        outgoing = tokens(usage['output_tokens'])
        details = usage.get('input_tokens_details') or {}
        text = tokens(details.get('text_tokens', 0))
        image = tokens(details.get('image_tokens', 0))
        if text + image > incoming:
            return None
        return ((Decimal(incoming * 8 - text * 3 + outgoing * 30)) / 1000000).quantize(
            Decimal('0.000001'), rounding=ROUND_UP)
    except (KeyError, TypeError, ValueError):
        return None


class OfficialImageBudget:
    def __init__(self, config, url, fields, references):
        settings = config.get('official_budget')
        if not settings or url.rstrip('/') != 'https://api.openai.com/v1':
            raise ValueError('Official image requests require the configured official host and budget')
        self.limit = _money(settings['limit_usd'])
        self.reserve = _money(settings['reserve_usd'])
        # 2026-11-02 用户授权每单预占1美元；总上限与旧未知占额保持。
        if not 1 <= self.reserve <= self.limit <= 60:
            raise ValueError('Official image budget must remain at or below USD 60 with at least USD 1 reserved per request')
        # 保守占额只适用于当前明确的单张1024高质量配置，不准auto/max绕过。
        if (fields['model'] != 'gpt-image-2.5-sunburst' or fields['size'] != '1024x1024'
                or fields['quality'] != 'high' or fields['n'] != 1
                or len(fields['prompt'].encode('utf-8')) > 24000 or len(references) > 4):
            raise ValueError('Official image request is outside the reviewed budget envelope')
        from PIL import Image
        for reference in references:
            with Image.open(reference) as image:
                if max(image.size) > 1024:
                    raise ValueError('Official budget references must be at most 1024 pixels per edge')
        self.path = Path(settings['ledger_path'])
        if not self.path.is_absolute():
            raise ValueError('Official image budget ledger must be machine-local and absolute')
        self.request_id = uuid.uuid4().hex
        self.request_sha = hashlib.sha256(json.dumps(fields, sort_keys=True).encode()).hexdigest()

    def _read(self):
        if not self.path.exists():
            return {'schema': 'ufeneo.official-image-budget.v1', 'limit_usd': str(self.limit), 'entries': []}
        data = json.loads(self.path.read_text('utf-8'))
        if data['schema'] != 'ufeneo.official-image-budget.v1' or _money(data['limit_usd']) != self.limit:
            raise ValueError('Official image budget ledger policy mismatch')
        return data

    def _write(self, data):
        staging = self.path.with_name(self.path.name + '.' + uuid.uuid4().hex + '.tmp')
        try:
            with staging.open('x', encoding='utf-8', newline='\n') as handle:
                json.dump(data, handle, ensure_ascii=False, indent=2)
                handle.write('\n')
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(staging, self.path)
        finally:
            if staging.exists():
                staging.unlink()

    def begin(self):
        with _locked(self.path):
            data = self._read()
            committed = sum((_money(entry['committed_usd']) for entry in data['entries']), Decimal(0))
            if committed + self.reserve > self.limit:
                raise ValueError('Official image budget exhausted or reserved; no request sent')
            data['entries'].append({'id': self.request_id, 'request_sha256': self.request_sha,
                                    'status': 'reserved_remote_result_unknown',
                                    'committed_usd': str(self.reserve), 'created_unix': int(time.time())})
            self._write(data)

    def complete(self, result):
        usage = result.get('usage')
        cost = usage_cost(usage)
        with _locked(self.path):
            data = self._read()
            entry = next(entry for entry in data['entries'] if entry['id'] == self.request_id)
            entry['status'] = 'completed_usage_cost' if cost is not None else 'completed_usage_unknown_reserved'
            entry['committed_usd'] = str(cost if cost is not None else self.reserve)
            entry['usage'] = usage
            entry['completed_unix'] = int(time.time())
            self._write(data)
            total = sum((_money(item['committed_usd']) for item in data['entries']), Decimal(0))
        return {'request_id': self.request_id, 'usage': usage,
                'estimated_cost_usd': str(cost) if cost is not None else None,
                'reserved_if_cost_unknown_usd': str(self.reserve),
                'project_committed_usd': str(total), 'project_limit_usd': str(self.limit)}
