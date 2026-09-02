"""LightTrans — 局域网双向快递站（文字 / 图片 / 文件）

电脑端: http://localhost:<port>
手机端: http://lighttrans.local:<port>  (mDNS，失败时用局域网 IP)
"""
import io
import json
import mimetypes
import os
import secrets
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
except Exception:
    pass

import qrcode
import uvicorn
from fastapi import Body, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from PIL import Image, ImageDraw

# ---------------- 配置 ----------------
BASE_DIR = Path(__file__).resolve().parent
RECEIVE_DIR = BASE_DIR / "接收文件"
HISTORY_FILE = BASE_DIR / "history.json"
ICON_FILE = BASE_DIR / "icon.png"
SERVICE_NAME = "lighttrans"
PORT_START = 8765
MAX_HISTORY = 50
MAX_TEXT_LEN = 10000

RECEIVE_DIR.mkdir(exist_ok=True)

# 访问令牌：公共网络防护。本机 localhost 免令牌，手机/局域网访问需令牌。
TOKEN_FILE = BASE_DIR / "token.txt"
if TOKEN_FILE.exists():
    TOKEN = TOKEN_FILE.read_text("utf-8").strip() or secrets.token_hex(8)
else:
    TOKEN = secrets.token_hex(8)
    TOKEN_FILE.write_text(TOKEN, "utf-8")

# 运行时全局状态
LAN_IP = "127.0.0.1"
PORT = PORT_START
QR_PNG = b""
MDNS_OK = False
_zc = None  # zeroconf 实例，需保持存活
_mdns_info = None  # 已注册的 mDNS 服务，IP 变化时先注销再重注册


# ---------------- 消息存储 ----------------
class Store:
    def __init__(self):
        self.lock = threading.Lock()
        self.epoch = 0
        self.seq = 0
        self.messages = []
        self._load()

    def _load(self):
        if HISTORY_FILE.exists():
            try:
                data = json.loads(HISTORY_FILE.read_text("utf-8"))
                self.epoch = int(data.get("epoch", 0))
                self.seq = int(data.get("seq", 0))
                self.messages = data.get("messages", [])[-MAX_HISTORY:]
            except Exception:
                pass

    def _save(self):
        try:
            HISTORY_FILE.write_text(
                json.dumps(
                    {"epoch": self.epoch, "seq": self.seq,
                     "messages": self.messages[-MAX_HISTORY:]},
                    ensure_ascii=False),
                "utf-8")
        except Exception:
            pass

    def add_text(self, text, sender):
        with self.lock:
            self.seq += 1
            msg = {"seq": self.seq, "type": "text", "text": text,
                   "sender": sender, "time": time.time()}
            self.messages.append(msg)
            self.messages = self.messages[-MAX_HISTORY:]
            self._save()
            return msg

    def add_file(self, name, size, sender, stored_name, mime):
        with self.lock:
            self.seq += 1
            msg = {"seq": self.seq, "type": "file", "name": name, "size": size,
                   "id": stored_name, "sender": sender, "time": time.time(),
                   "mime": mime}
            self.messages.append(msg)
            self.messages = self.messages[-MAX_HISTORY:]
            self._save()
            return msg

    def list_since(self, seq):
        with self.lock:
            items = [m for m in self.messages if m["seq"] > seq]
            return {"epoch": self.epoch, "current_seq": self.seq, "items": items}

    def clear(self):
        with self.lock:
            self.messages = []
            self.epoch += 1
            self._save()


store = Store()

app = FastAPI(title="LightTrans", docs_url=None, redoc_url=None)
app.add_middleware(GZipMiddleware, minimum_size=500)

LOGIN_HTML = (BASE_DIR / "login.html").read_text("utf-8")


def _authorized(request):
    return (request.cookies.get("lt_token") == TOKEN
            or request.query_params.get("k") == TOKEN)


@app.middleware("http")
async def token_guard(request, call_next):
    host = request.client.host if request.client else "127.0.0.1"
    is_local = host in ("127.0.0.1", "::1")
    path = request.url.path
    exempt = path in ("/login", "/api/login", "/icon.png", "/favicon.ico",
                      "/manifest.webmanifest")
    if is_local or _authorized(request) or exempt:
        resp = await call_next(request)
        if not is_local and request.query_params.get("k") == TOKEN:
            resp.set_cookie("lt_token", TOKEN, max_age=365 * 24 * 3600)
        return resp
    if path in ("/", "/index.html"):
        return HTMLResponse(LOGIN_HTML, headers={"Cache-Control": "no-store"})
    return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)


# ---------------- 工具函数 ----------------
def get_lan_ip():
    """通过 UDP 探测默认路由对应的局域网 IP。"""
    for target in ("223.5.5.5", "119.29.29.29", "114.114.114.114", "8.8.8.8"):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.connect((target, 53))
            ip = s.getsockname()[0]
            s.close()
            if ip and not ip.startswith("127."):
                return ip
        except OSError:
            continue
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip.startswith(("192.168.", "10.", "172.")):
                return ip
    except OSError:
        pass
    return "127.0.0.1"


def get_lan_ip_with_retry(attempts=6, delay=2):
    """启动时网络可能尚未就绪：探测失败则重试，避免落回 127.0.0.1。"""
    for i in range(attempts):
        ip = get_lan_ip()
        if not ip.startswith("127."):
            return ip
        print(f"[网络] 尚未就绪（第 {i + 1}/{attempts} 次探测），{delay}s 后重试…")
        time.sleep(delay)
    return "127.0.0.1"


def pick_port():
    for p in range(PORT_START, PORT_START + 10):
        with socket.socket() as s:
            try:
                s.bind(("0.0.0.0", p))
                s.close()
                return p
            except OSError:
                continue
    raise RuntimeError("端口 8765-8774 全部被占用")


def make_qr(url):
    qr = qrcode.QRCode(border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image()
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def ascii_qr(url):
    qr = qrcode.QRCode(border=1)
    qr.add_data(url)
    qr.make(fit=True)
    qr.print_ascii(invert=True)


def make_icon(path):
    """星际跃迁风格图标：深空蓝 -> 青渐变 + 星空 + 光带 + 四角跃迁星。"""
    if path.exists():
        return
    import random
    size = 180
    c1, c2 = (10, 42, 74), (6, 182, 212)
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for y in range(size):
        t = y / size
        color = tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))
        d.line([(0, y), (size, y)], fill=color + (255,))
    # 星空
    random.seed(42)
    for _ in range(26):
        x = random.randint(6, 174)
        y = random.randint(6, 174)
        r = random.choice((1, 1, 2))
        a = random.randint(90, 190)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(200, 240, 255, a))
    # 跃迁光带
    d.rounded_rectangle([28, 58, 78, 63], radius=2, fill=(180, 240, 255, 190))
    d.rounded_rectangle([96, 118, 168, 123], radius=2, fill=(180, 240, 255, 160))
    d.rounded_rectangle([30, 150, 64, 154], radius=2, fill=(160, 230, 255, 140))
    # 四角跃迁星
    cx, cy, ro, ri = 90, 95, 58, 17
    pts = [(cx, cy - ro), (cx + ri, cy - ri), (cx + ro, cy), (cx + ri, cy + ri),
           (cx, cy + ro), (cx - ri, cy + ri), (cx - ro, cy), (cx - ri, cy - ri)]
    d.polygon(pts, fill=(255, 255, 255, 255))
    d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(200, 245, 255, 255))
    mask = Image.new("L", (size, size), 0)
    dm = ImageDraw.Draw(mask)
    dm.rounded_rectangle([0, 0, size - 1, size - 1], radius=40, fill=255)
    img.putalpha(mask)
    img.save(path)


def unique_path(p: Path) -> Path:
    if not p.exists():
        return p
    stem, suffix = p.stem, p.suffix
    i = 1
    while True:
        cand = p.with_name(f"{stem} ({i}){suffix}")
        if not cand.exists():
            return cand
        i += 1


def convert_heic(p: Path) -> Path | None:
    """iPhone 直出的 HEIC 转成 JPG，方便电脑浏览器显示。"""
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
        img = Image.open(p)
        new = p.with_suffix(".jpg")
        img.convert("RGB").save(new, "JPEG", quality=90)
        p.unlink()
        return new
    except Exception:
        return None


def register_mdns(ip, port) -> bool:
    global _zc, _mdns_info
    try:
        from zeroconf import ServiceInfo, Zeroconf
        if _zc is None:
            _zc = Zeroconf()
        if _mdns_info is not None:
            _zc.unregister_service(_mdns_info)
        info = ServiceInfo(
            "_http._tcp.local.",
            f"{SERVICE_NAME}._http._tcp.local.",
            addresses=[socket.inet_aton(ip)],
            port=port,
            server=f"{SERVICE_NAME}.local.",
        )
        _zc.register_service(info, allow_name_change=True)
        _mdns_info = info
        print(f"[mDNS] 已注册 {SERVICE_NAME}.local -> {ip}:{port}")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[mDNS] 注册失败（手机请改用备用 IP 地址）: {e}")
        return False


# ---------------- 路由 ----------------
@app.get("/")
def index():
    return FileResponse(BASE_DIR / "index.html",
                        headers={"Cache-Control": "no-store"})


@app.get("/favicon.ico")
@app.get("/icon.png")
def icon():
    make_icon(ICON_FILE)
    return FileResponse(ICON_FILE, headers={"Cache-Control": "public, max-age=3600"})


@app.get("/manifest.webmanifest")
def manifest():
    return JSONResponse(
        {"name": "LightTrans", "short_name": "LightTrans", "start_url": "/",
         "display": "standalone", "background_color": "#ecfeff",
         "theme_color": "#06b6d4",
         "icons": [{"src": "/icon.png", "sizes": "180x180", "type": "image/png"}]},
        media_type="application/manifest+json")


@app.get("/qr.png")
def qr_png():
    return Response(content=QR_PNG, media_type="image/png",
                    headers={"Cache-Control": "public, max-age=300"})


@app.get("/health")
def health():
    return {"ok": True, "name": SERVICE_NAME}


@app.get("/api/state")
def state():
    mdns_url = f"http://{SERVICE_NAME}.local:{PORT}"
    ip_url = f"http://{LAN_IP}:{PORT}"
    return {"phone_url": mdns_url if MDNS_OK else ip_url,
            "ip_url": ip_url, "mdns_ok": MDNS_OK, "token": TOKEN}


@app.post("/api/login")
async def login(payload: dict = Body(...)):
    if str(payload.get("token", "")) == TOKEN:
        resp = JSONResponse({"ok": True})
        resp.set_cookie("lt_token", TOKEN, max_age=365 * 24 * 3600)
        return resp
    return JSONResponse({"ok": False, "error": "bad token"}, status_code=401)


@app.get("/api/messages")
def messages(since: int = 0):
    return store.list_since(since)


@app.delete("/api/messages")
def clear_messages():
    store.clear()
    return {"ok": True}


@app.post("/api/text")
def post_text(payload: dict = Body(...)):
    text = str(payload.get("text", "")).strip()
    if not text:
        raise HTTPException(400, "内容为空")
    sender = str(payload.get("sender", "未知"))[:20]
    return store.add_text(text[:MAX_TEXT_LEN], sender)


@app.post("/api/upload")
async def upload(files: list[UploadFile] = File(...),
                 sender: str = Form("未知")):
    sender = sender[:20]
    results = []
    for f in files:
        name = Path(f.filename or "未命名").name
        stored = unique_path(RECEIVE_DIR / name)
        size = 0
        with stored.open("wb") as w:
            while True:
                chunk = await f.read(256 * 1024)
                if not chunk:
                    break
                w.write(chunk)
                size += len(chunk)
        mime = mimetypes.guess_type(stored.name)[0] or "application/octet-stream"
        if stored.suffix.lower() in (".heic", ".heif"):
            converted = convert_heic(stored)
            if converted:
                stored = converted
                name = converted.name
                size = converted.stat().st_size
                mime = "image/jpeg"
        results.append(store.add_file(name, size, sender, stored.name, mime))
    return results


@app.get("/api/files/{fid}")
def get_file(fid: str, download: bool = False):
    p = RECEIVE_DIR / Path(fid).name
    if not p.exists():
        raise HTTPException(404, "文件不存在或已被删除")
    media = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
    if download or not media.startswith("image/"):
        return FileResponse(p, media_type=media, filename=p.name)
    return FileResponse(p, media_type=media)


def _check_ip_once() -> bool:
    """检测一次 IP 变化；变化则更新 mDNS 与二维码。返回是否有变化。"""
    global LAN_IP, QR_PNG, MDNS_OK
    try:
        ip = get_lan_ip()
    except Exception:
        return False
    if ip.startswith("127.") or ip == LAN_IP:
        return False
    old, LAN_IP = LAN_IP, ip
    print(f"[网络] IP 变化 {old} -> {ip}，更新 mDNS 与二维码…")
    if register_mdns(ip, PORT):
        MDNS_OK = True
    qr_url = (f"http://{SERVICE_NAME}.local:{PORT}" if MDNS_OK
              else f"http://{ip}:{PORT}") + f"?k={TOKEN}"
    QR_PNG = make_qr(qr_url)
    print(f"[网络] 已更新，新备用地址: http://{ip}:{PORT}")
    return True


def ip_watcher():
    """运行中每 15 秒检测一次局域网 IP，切换网络无需重启服务。"""
    while True:
        time.sleep(15)
        try:
            _check_ip_once()
        except Exception:  # noqa: BLE001
            pass


# ---------------- 主入口 ----------------
def main():
    global LAN_IP, PORT, QR_PNG, MDNS_OK
    LAN_IP = get_lan_ip_with_retry()
    PORT = pick_port()
    phone_url = f"http://{SERVICE_NAME}.local:{PORT}"
    ip_url = f"http://{LAN_IP}:{PORT}"

    MDNS_OK = register_mdns(LAN_IP, PORT)
    qr_url = (phone_url if MDNS_OK else ip_url) + f"?k={TOKEN}"
    QR_PNG = make_qr(qr_url)
    make_icon(ICON_FILE)

    line = "=" * 58
    print(line)
    print("  LightTrans 局域网快递站已启动")
    print(f"  电脑端 : http://localhost:{PORT}")
    print(f"  手机端 : {phone_url}?k={TOKEN}")
    if not MDNS_OK:
        print(f"  （mDNS 不可用，手机请用备用地址）")
    print(f"  备用   : {ip_url}?k={TOKEN}")
    print(f"  访问令牌: {TOKEN}")
    print("  首次使用: 电脑页面点「连接手机」-> 手机扫码")
    print("            ->「分享」->「添加到主屏幕」")
    print(f"  接收文件: {RECEIVE_DIR}")
    print("  停止服务: 按 Ctrl+C")
    print(line)
    try:
        print("  备用二维码（终端版）:")
        ascii_qr(qr_url)
    except Exception:
        pass

    if os.environ.get("LT_SILENT") != "1":
        threading.Timer(1.5, lambda: webbrowser.open(f"http://localhost:{PORT}")).start()
    threading.Thread(target=ip_watcher, daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")


if __name__ == "__main__":
    main()
