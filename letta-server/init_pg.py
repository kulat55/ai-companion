# 启动内嵌 PostgreSQL（pgserver，数据在部署根目录\pgdata），幂等创建 letta 账号/库，
# 并把实际监听端口写入 部署根目录\pgdata\PORT，供启动脚本读取。
# postgres 进程在本脚本退出后继续常驻（cleanup_mode=None）。
import ctypes
import re
import socket
from pathlib import Path
import pgserver
from pgserver import utils as _pgu
from pgserver import postgres_server as _pgs

PGDATA = Path(__file__).resolve().parents[1] / "pgdata"  # 部署根目录\pgdata

# 固定内嵌 PostgreSQL 端口，避免“停一次再启动端口就漂移”，导致残留的 Letta 连旧端口变僵尸。
# 首选端口被占用时，自动回退到系统分配的空闲端口。
FIXED_PG_PORT = 55432
_orig_find_port = _pgu.find_suitable_port

def _stable_port(address=None):
    a = address or "127.0.0.1"
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((a, FIXED_PG_PORT))
        return FIXED_PG_PORT
    except OSError:
        return _orig_find_port(address)
    finally:
        s.close()

_pgu.find_suitable_port = _stable_port
_pgs.find_suitable_port = _stable_port

def _pid_alive(pid):
    try:
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return code.value == 259                # STILL_ACTIVE
    except Exception:
        return True     # 探测失败时保守视为存活，不贸然删锁

def cleanup_stale_lock():
    # 上次崩溃/强杀可能留下 postmaster.pid，会让 PG 启动卡住；指向的进程已死则删除
    lock = PGDATA / "postmaster.pid"
    if not lock.exists():
        return
    try:
        pid = int(lock.read_text().splitlines()[0].strip())
    except Exception:
        return
    if not _pid_alive(pid):
        try:
            lock.unlink()
            print("removed stale postmaster.pid (pid=%s)" % pid, flush=True)
        except Exception:
            pass

def main():
    cleanup_stale_lock()
    srv = pgserver.get_server(PGDATA, cleanup_mode=None)
    admin_uri = srv.get_uri()  # postgresql://postgres:@127.0.0.1:<port>/postgres
    m = re.search(r":(\d+)/", admin_uri)
    port = m.group(1)
    print("ADMIN_URI:", admin_uri, flush=True)

    # 幂等创建登录角色
    srv.psql(
        "DO $$ BEGIN "
        "IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname='letta') THEN "
        "CREATE ROLE letta LOGIN PASSWORD 'letta'; "
        "END IF; END $$;"
    )
    # CREATE DATABASE 不能在 DO/事务块中，已存在则忽略报错
    try:
        srv.psql("CREATE DATABASE letta OWNER letta;")
        print("created database letta", flush=True)
    except Exception as e:
        msg = str(e)
        if "already exists" in msg:
            print("database letta already exists", flush=True)
        else:
            raise

    (PGDATA / "PORT").write_text(port, encoding="utf-8")
    print("PORT=" + port, flush=True)
    print("LETTA_PG_URI=postgresql+pg8000://letta:letta@127.0.0.1:%s/letta" % port, flush=True)
    print("PG_READY", flush=True)

if __name__ == "__main__":
    main()
