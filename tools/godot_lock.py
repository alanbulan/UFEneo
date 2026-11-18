"""多会话并行时串行运行 Godot：python tools/godot_lock.py -- <命令...>。
锁被占用就按先来后到排队；持锁进程已退出则接管。返回被包装命令的退出码。"""

import os
from pathlib import Path
import subprocess
import sys
import time

LOCK = Path(__file__).resolve().parents[1] / 'art/shared/locks/godot.lock'


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


# 先到先得：每个等待者在 QUEUE 里放一张按时间命名的票，只有排在最前的活票才去抢锁。
# 以前所有等待者每 2 秒随机抢，十几个会话同时排队时有人等满 2 小时超时。
QUEUE = LOCK.parent / 'godot-queue'


def ticket_pid(ticket):
    try:
        return int(ticket.name.rsplit('-', 1)[1])
    except (IndexError, ValueError):
        return 0


def ahead_of(ticket):
    ahead = 0
    for other in sorted(QUEUE.iterdir()):
        if other.name >= ticket.name:
            break
        if alive(ticket_pid(other)):
            ahead += 1
        else:
            try:
                other.unlink()
            except FileNotFoundError:
                pass
    return ahead


def acquire(timeout):
    QUEUE.mkdir(parents=True, exist_ok=True)
    ticket = QUEUE / f'{time.time_ns():020d}-{os.getpid()}'
    ticket.write_text('')
    start = time.time()
    noted = start
    try:
        while True:
            ahead = ahead_of(ticket)
            pid = 0
            if ahead == 0:
                try:
                    fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    os.write(fd, str(os.getpid()).encode())
                    os.close(fd)
                    return
                except FileExistsError:
                    try:
                        pid = int(LOCK.read_text().strip() or 0)
                    except (OSError, ValueError):
                        pid = 0
                    if pid and not alive(pid):
                        try:
                            LOCK.unlink()
                        except FileNotFoundError:
                            pass
                        continue
            if time.time() - start > timeout:
                raise SystemExit(f'Godot 锁等待超时（前面还有 {ahead} 个，持有进程 {pid}）：{LOCK}')
            if time.time() - noted > 300:
                print(f'Godot 锁排队中：前面还有 {ahead} 个，已等 {int(time.time() - start)} 秒', flush=True)
                noted = time.time()
            time.sleep(1)
    finally:
        try:
            ticket.unlink()
        except FileNotFoundError:
            pass


def release():
    try:
        if LOCK.read_text().strip() == str(os.getpid()):
            LOCK.unlink()
    except FileNotFoundError:
        pass


if __name__ == '__main__':
    args = sys.argv[1:]
    if args[:1] == ['--']:
        args = args[1:]
    if not args:
        raise SystemExit('用法：python tools/godot_lock.py -- <命令...>')
    acquire(timeout=int(os.environ.get('GODOT_LOCK_TIMEOUT', '21600')))
    try:
        code = subprocess.call(args)
    finally:
        release()
    sys.exit(code)
