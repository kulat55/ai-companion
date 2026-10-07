# -*- coding: utf-8 -*-
"""后端进程管理：按顺序启动 内嵌PostgreSQL -> Letta(记忆大脑) -> VTuber(桌宠服务)。

可靠性设计：
- 启动前对“已在运行”的服务做【深度健康检查】，僵尸/半死进程会被先清理再重启，不再只看端口；
- 各服务超时 120s，失败自动重启一次；
- 父进程（Electron）看门：父进程一旦异常退出，自动停掉全部服务并退出，杜绝孤儿残留；
- PG 端口由 init_pg 固定（见 init_pg.py），消除端口漂移。
所有数据仍在部署根目录（仓库根）下。
"""
import ctypes
from ctypes import wintypes
import os
import socket
import subprocess
import sys
import threading
import time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # 部署根目录（仓库根）
LETTA_PY = os.path.join(ROOT, r"letta-server\venv\Scripts\python.exe")
LETTA_EXE = os.path.join(ROOT, r"letta-server\venv\Scripts\letta.exe")
INIT_PG = os.path.join(ROOT, r"letta-server\init_pg.py")
PG_CTL = os.path.join(ROOT, r"letta-server\venv\Lib\site-packages\pgserver\pginstall\bin\pg_ctl.exe")
PGDATA = os.path.join(ROOT, "pgdata")
PORT_FILE = os.path.join(PGDATA, "PORT")
VT_PY = os.path.join(ROOT, r"Open-LLM-VTuber\.venv\Scripts\python.exe")
VT_ROOT = os.path.join(ROOT, "Open-LLM-VTuber")
RUN_SERVER = os.path.join(VT_ROOT, "run_server.py")
KEY_FILE = os.path.join(ROOT, r"companion\deepseek_key.txt")
LETTA_DIR = os.path.join(ROOT, "letta-data")

LETTA_LOG = os.path.join(ROOT, r"letta-server\letta.log")
LETTA_ERR = os.path.join(ROOT, r"letta-server\letta.err.log")
VT_LOG = os.path.join(ROOT, "vtuber.log")
VT_ERR = os.path.join(ROOT, "vtuber.err.log")

LETTA_PORT = 8283
VT_PORT = 12393

CREATE_NO_WINDOW = 0x08000000
READY_TIMEOUT = 120          # 单个服务就绪超时（秒）
MAX_ATTEMPTS = 2             # 单个服务最多启动次数
FIXED_PG_PORT = 55432        # 内嵌 PostgreSQL 固定端口（与 init_pg.py 一致）


# ---------------- 基础探测 ----------------
def port_open(port, host="127.0.0.1"):
    try:
        with socket.create_connection((host, port), timeout=0.8):
            return True
    except OSError:
        return False


def port_busy(port):
    """IPv4(127.0.0.1) 或 IPv6(::1) 任一在监听即视为占用（VTuber 默认会绑 ::1）。"""
    if port_open(port, "127.0.0.1"):
        return True
    try:
        with socket.create_connection(("::1", port), timeout=0.8):
            return True
    except OSError:
        return False


def read_pg_port():
    try:
        return int(open(PORT_FILE).read().strip())
    except Exception:
        return None


def _read_tail(path, n=300):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()[-n:]
    except Exception:
        return ""


def http_status(url, timeout=3):
    try:
        return requests.get(url, timeout=timeout).status_code
    except Exception:
        return None


def http_ok(url, timeout=3):
    return http_status(url, timeout) == 200


def wait_for(cond, timeout, interval=1.0):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(interval)
    return cond()


# ---------------- 深度健康检查 ----------------
def letta_healthy():
    """Letta 不仅要在跑，还要能连通它依赖的 PostgreSQL（agents 接口能正常返回）。"""
    if http_status(f"http://127.0.0.1:{LETTA_PORT}/v1/health/", 4) != 200:
        return False
    try:
        r = requests.get(f"http://127.0.0.1:{LETTA_PORT}/v1/agents/", timeout=6)
        return r.status_code == 200
    except Exception:
        return False


def vtuber_healthy():
    """VTuber HTTP 根路径能返回前端页面（uvicorn 完全就绪后才会）。"""
    return http_status(f"http://127.0.0.1:{VT_PORT}/", 4) == 200


# ---------------- 进程存活（父进程看门用） ----------------
_k32 = ctypes.windll.kernel32

def pid_alive(pid):
    STILL_ACTIVE = 259
    h = _k32.OpenProcess(0x1000, False, pid)   # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return False
    code = ctypes.c_ulong()
    _k32.GetExitCodeProcess(h, ctypes.byref(code))
    _k32.CloseHandle(h)
    return code.value == STILL_ACTIVE


# ---------------- Windows Job Object：内核级“同生共死” ----------------
# backend 一启动就创建 KILL_ON_JOB_CLOSE 的 Job 并把自己放进去；此后所有子进程
# （init_pg/pg_ctl/letta/run_server，以及 postgres、uv-python）默认继承该 Job。
# 无论 backend 是崩溃、被任务管理器结束还是被 taskkill /T 杀掉，只要它一终止，Job 句柄
# 关闭，OS 就会自动杀掉 Job 内全部进程——毫秒级、零孤儿，不依赖轮询看门是否来得及。
def _install_kill_job():
    def _jl(m):
        try:
            open(os.path.join(ROOT, r"desktop\job_install.log"), "a",
                 encoding="utf-8").write(m + "\n")
        except Exception:
            pass
    try:
        _jl("=== install job start ===")
        k = ctypes.windll.kernel32
        # 关键：声明句柄类型，否则 64 位伪句柄 GetCurrentProcess()(-1) 会被 ctypes
        # 默认的 c_int 截断成 32 位无效值，导致 AssignProcessToJobObject 报错误码 6
        k.CreateJobObjectW.restype = wintypes.HANDLE
        k.GetCurrentProcess.restype = wintypes.HANDLE
        k.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        k.AssignProcessToJobObject.restype = wintypes.BOOL
        k.SetInformationJobObject.restype = wintypes.BOOL
        if not hasattr(k, "CreateJobObjectW"):
            _jl("no CreateJobObjectW")
            return None
        job = k.CreateJobObjectW(None, None)
        _jl("create job=%s err=%s" % (job, ctypes.GetLastError()))
        if not job:
            return None

        class _IO_COUNTERS(ctypes.Structure):
            _fields_ = [("ReadOperationCount", ctypes.c_ulonglong),
                        ("WriteOperationCount", ctypes.c_ulonglong),
                        ("OtherOperationCount", ctypes.c_ulonglong),
                        ("ReadTransferCount", ctypes.c_ulonglong),
                        ("WriteTransferCount", ctypes.c_ulonglong),
                        ("OtherTransferCount", ctypes.c_ulonglong)]

        class _BASIC_LIMIT(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong),
                        ("PerJobUserTimeLimit", ctypes.c_longlong),
                        ("LimitFlags", wintypes.DWORD),
                        ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t),
                        ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_void_p),
                        ("PriorityClass", wintypes.DWORD),
                        ("SchedulingClass", wintypes.DWORD)]

        class _EXT_LIMIT(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", _BASIC_LIMIT),
                        ("IoInfo", _IO_COUNTERS),
                        ("ProcessMemoryLimit", ctypes.c_size_t),
                        ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t),
                        ("PeakJobMemoryUsed", ctypes.c_size_t)]

        KILL_ON_CLOSE = 0x2000
        info = _EXT_LIMIT()
        info.BasicLimitInformation.LimitFlags = KILL_ON_CLOSE
        rs = k.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))
        _jl("setinfo=%s err=%s sizeof=%s" % (rs, ctypes.GetLastError(), ctypes.sizeof(info)))
        if not rs:
            return None
        ra = k.AssignProcessToJobObject(job, k.GetCurrentProcess())
        _jl("assign self=%s err=%s" % (ra, ctypes.GetLastError()))
        if not ra:
            return None
        _jl("JOB OK")
        return job
    except Exception as ex:
        _jl("EXC %r" % ex)
        return None


JOB_HANDLE = _install_kill_job()


class BackendManager:
    def __init__(self):
        self.procs = []

    def log(self, msg, cb=None):
        print("[backend]", msg, flush=True)
        if cb:
            cb(msg)

    # ---------------- 启动 ----------------
    def start(self, progress=None):
        pgport = self._ensure_pg(progress)
        self._ensure_letta(pgport, progress)
        self._ensure_vtuber(progress)
        return True

    def _ensure_pg(self, progress):
        # 用 Popen + 轮询（并写追踪日志），避免黑盒 subprocess.run；重定向到文件避免管道问题。
        self.log("正在确保内嵌数据库运行…", progress)
        pg_out = os.path.join(ROOT, r"desktop\init_pg.out")
        pg_err = os.path.join(ROOT, r"desktop\init_pg.err")
        tracef = os.path.join(ROOT, r"desktop\pg_ensure_trace.log")
        fo = open(pg_out, "w", encoding="utf-8")
        fe = open(pg_err, "w", encoding="utf-8")
        tlog = open(tracef, "w", encoding="utf-8")
        t0 = time.time()
        # stdin 必须 DEVNULL：本进程有线程阻塞读 stdin 管道，子进程若继承该管道，
        # pg_ctl/postgres 启动会挂死（这是服务“有时起不来”的根因）。
        p = subprocess.Popen([LETTA_PY, INIT_PG], stdin=subprocess.DEVNULL,
                             stdout=fo, stderr=fe, creationflags=CREATE_NO_WINDOW)
        while True:
            el = time.time() - t0
            rc = p.poll()
            tlog.write("t=%.0f rc=%s port55432=%s\n" %
                       (el, rc, port_busy(FIXED_PG_PORT)))
            tlog.flush()
            if rc is not None:
                break
            if el > 90:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)],
                               capture_output=True, creationflags=CREATE_NO_WINDOW)
                break
            time.sleep(5)
        fo.close(); fe.close(); tlog.close()
        pgport = read_pg_port()
        if not (pgport and wait_for(lambda: port_busy(pgport), 30)):
            raise RuntimeError("内嵌数据库启动失败：%s" % _read_tail(pg_err))
        self.log("数据库就绪(端口 %s)" % pgport, progress)
        return pgport

    def _ensure_letta(self, pgport, progress):
        if letta_healthy():
            self.log("Letta 记忆服务已在运行且健康", progress)
            return
        if port_busy(LETTA_PORT):
            self.log("检测到残留/不可用的 Letta，先关闭…", progress)
            self._kill_letta()
            wait_for(lambda: not port_busy(LETTA_PORT), 15)

        env = os.environ.copy()
        env["LETTA_DIR"] = LETTA_DIR
        env["LETTA_DISABLE_TRACING"] = "true"
        env["ACCEPTABLE_ORIGINS"] = (
            "http://localhost:12393,http://127.0.0.1:12393,"
            "http://localhost:8283,http://127.0.0.1:8283")
        env["LETTA_PG_URI"] = f"postgresql+pg8000://letta:letta@127.0.0.1:{pgport}/letta"
        if os.path.isfile(KEY_FILE):
            env["DEEPSEEK_API_KEY"] = open(KEY_FILE).read().strip()

        for attempt in range(1, MAX_ATTEMPTS + 1):
            self.log("正在启动 Letta 记忆大脑（第 %d 次）…" % attempt, progress)
            lf = open(LETTA_LOG, "a", encoding="utf-8")
            le = open(LETTA_ERR, "a", encoding="utf-8")
            p = subprocess.Popen(
                [LETTA_EXE, "server", "--type", "rest", "--host", "localhost",
                 "--port", str(LETTA_PORT)],
                env=env, stdin=subprocess.DEVNULL, stdout=lf, stderr=le,
                creationflags=CREATE_NO_WINDOW)
            self.procs.append(p)
            if wait_for(letta_healthy, READY_TIMEOUT, 1.5):
                self.log("Letta 就绪", progress)
                return
            self.log("Letta 第 %d 次未就绪，重启…" % attempt, progress)
            self._kill_letta()
            wait_for(lambda: not port_busy(LETTA_PORT), 12)
        raise RuntimeError("Letta 多次启动仍失败，见 letta-server\\letta.err.log")

    def _ensure_vtuber(self, progress):
        if vtuber_healthy():
            self.log("Live2D 桌宠服务已在运行且健康", progress)
            return
        if port_busy(VT_PORT):
            self.log("检测到残留/不可用的桌宠服务，先关闭…", progress)
            self._kill_vtuber()
            wait_for(lambda: not port_busy(VT_PORT), 15)

        env = os.environ.copy()
        # 仅把确实存在的本地工具目录加入 PATH（MinGit / bin 为可选扩展，缺省不影响）
        extra = [os.path.join(ROOT, r"MinGit\cmd"), os.path.join(ROOT, "bin")]
        extra = [p for p in extra if os.path.isdir(p)]
        if extra:
            env["PATH"] = os.pathsep.join(extra) + os.pathsep + env.get("PATH", "")

        for attempt in range(1, MAX_ATTEMPTS + 1):
            self.log("正在启动 Live2D 桌宠（第 %d 次）…" % attempt, progress)
            vf = open(VT_LOG, "a", encoding="utf-8")
            ve = open(VT_ERR, "a", encoding="utf-")
            p = subprocess.Popen([VT_PY, RUN_SERVER], cwd=VT_ROOT, env=env,
                                 stdin=subprocess.DEVNULL, stdout=vf, stderr=ve,
                                 creationflags=CREATE_NO_WINDOW)
            self.procs.append(p)
            if wait_for(lambda: vtuber_healthy() and port_busy(VT_PORT),
                        READY_TIMEOUT, 1.5):
                self.log("Live2D 桌宠就绪", progress)
                self._apply_frontend_patch()
                return
            self.log("桌宠第 %d 次未就绪，重启…" % attempt, progress)
            self._kill_vtuber()
            wait_for(lambda: not port_busy(VT_PORT), 12)
        raise RuntimeError("Live2D 桌宠多次启动仍失败，见 vtuber.err.log")

    def _apply_frontend_patch(self):
        """把仓库自带的中性前端增强注入到 index.html（幂等，失败不影响主流程）。"""
        try:
            injector = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "inject_frontend.py")
            subprocess.run([sys.executable, injector, VT_ROOT],
                           capture_output=True, timeout=30,
                           creationflags=CREATE_NO_WINDOW)
        except Exception as e:
            self.log("前端增强注入跳过: %s" % e)

    # ---------------- 进程清理 ----------------
    def _kill_letta(self):
        for p in self.procs:
            try:
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(p.pid)],
                               capture_output=True, creationflags=CREATE_NO_WINDOW)
            except Exception:
                pass
        try:
            subprocess.run(["taskkill", "/F", "/IM", "letta.exe"],
                           capture_output=True, creationflags=CREATE_NO_WINDOW)
        except Exception:
            pass

    def _kill_vtuber(self):
        ps = (
            "Get-CimInstance Win32_Process | Where-Object { "
            "$_.CommandLine -like '*Open-LLM-VTuber*run_server.py*' } | ForEach-Object { "
            "Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }")
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, timeout=40,
                           creationflags=CREATE_NO_WINDOW)
        except Exception:
            pass

    def stop(self):
        self._kill_vtuber()
        self._kill_letta()
        try:
            subprocess.run([PG_CTL, "-D", PGDATA, "stop", "-m", "fast"],
                           capture_output=True, timeout=30,
                           creationflags=CREATE_NO_WINDOW)
        except Exception:
            pass


if __name__ == "__main__":
    import sys

    bm = BackendManager()
    parent_pid = int(os.environ.get("PARENT_PID", "0") or 0)

    def _watch_parent():
        # 父 Electron 异常退出（崩溃/被结束/注销）时，自动清理全部服务，杜绝孤儿
        if not parent_pid:
            return
        while True:
            time.sleep(2)
            if not pid_alive(parent_pid):
                try:
                    bm.stop()
                finally:
                    os._exit(0)

    def _watch_stdin():
        try:
            for line in sys.stdin:
                if line.strip() == "shutdown":
                    bm.stop()
                    sys.exit(0)
        except Exception:
            pass

    threading.Thread(target=_watch_parent, daemon=True).start()
    threading.Thread(target=_watch_stdin, daemon=True).start()

    try:
        bm.start(progress=lambda m: print("PROGRESS:" + m, flush=True))
        print("BACKEND_READY", flush=True)
    except Exception as e:
        print("BACKEND_ERROR:%r" % e, flush=True)
        bm.stop()
        sys.exit(1)

    while True:
        time.sleep(3600)
