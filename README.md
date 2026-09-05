# ⚡ LightTrans

> **A zero-config LAN bridge between your phone and PC.**
> Transfer text, images and files as easily as chatting — scan a QR code once, then tap an icon. Your data never leaves your local network.

> **局域网内的手机 ↔ 电脑快递站。** 像聊天一样传文字、图片、文件，扫码一次、点图标即用，数据不出家门。

[English](#english) · [中文](#中文)

---

# English

## ✨ Features

- 📝 **Bidirectional text** — paste on one device, tap-to-copy on the other, ~1s realtime sync
- 🖼️ **Images & files** — full-size, zero compression, drag-and-drop on PC, photo picker on phone
- 📱 **PWA on iPhone** — add to Home Screen once, works like a native app (mDNS stable address: `lighttrans.local`)
- ⚡ **No internet required** — pure LAN; works on phone hotspot even when the network is down
- 🔐 **Access token** — keeps strangers on the same Wi-Fi out (localhost is always trusted)
- 🗑️ **Message management** — per-device delete, long-press action sheet, batch multi-select
- 🖥️ **Silent background service** — optional auto-start at Windows login (no window)
- 🌐 **Adaptive UI** — one page for both phone (440×956pt class) and desktop

## 🚀 Quick Start (Windows)

Requirements: Python 3.10+, [uv](https://docs.astral.sh/uv/) (or pip)

```bash
git clone https://github.com/Edison-q/LightTrans.git
cd LightTrans
uv sync                # install dependencies
uv run server.py       # or: double-click 启动LightTrans.bat
```

Then:

1. Your browser opens `http://localhost:8765` automatically
2. Click **连接手机 (Connect phone)** in the top-right corner
3. Scan the QR code with your iPhone camera → tap **Share** → **Add to Home Screen**
4. Done — tap the icon to use it forever (the QR already contains the access token)

**Daily open (recommended):** double-click `打开LightTrans.vbs` (pin its desktop shortcut to the taskbar): opens the page instantly if the server is up; if not, auto-starts it, waits until ready, then opens — you never worry about server state. `停止服务.bat` stops all instances on ports 8765-8774.

> Windows 11 refuses to pin script shortcuts to the taskbar — use `LightTrans.exe` (prebuilt launcher with the icon embedded; source: `launcher.cs`) for the taskbar pin instead.

**Auto-start (optional):** create a shortcut to `静默启动.vbs` and place it in the Startup folder (`Win+R` → `shell:startup`). The service runs silently in the background.

## 📱 Mobile Usage

| Action | How |
|--------|-----|
| Send text | Type in the composer, press Enter |
| Send photo/file | Tap ➕ |
| Copy text | Tap any text bubble |
| View image | Tap thumbnail → fullscreen preview (✕ / tap blank to close) |
| Save image to Photos | Open fullscreen → **long-press** the image |
| Long-press menu | Copy / Select text / Download / Delete |
| Partial text select | Long-press → 选择文字 (Select text) → long-press again to drag handles |
| Batch delete | Tap ☑ 多选 → tick messages → Delete |

## 🛡️ Security

- A random access token is generated on first run (`token.txt`). Remote devices must present it; `localhost` bypasses auth.
- The QR code embeds the token, so your phone never types it manually.
- Transport is plain HTTP — it stops casual neighbors, not professional sniffers. Use it on networks you trust (home, personal hotspot).

## 🏫 Campus & Hotspot Notes

- If devices are on different network segments (e.g. laptop on ethernet, phone on Wi-Fi) or the network blocks client-to-client traffic, direct LAN transfer may fail.
- **Fallback that always works:** turn on the phone's hotspot, connect the laptop to it — both are now on one LAN. No internet, no data usage, transfers keep working.

## 🛠 Tech Stack

- Backend: Python + FastAPI + uvicorn, single file (`server.py`)
- Frontend: vanilla HTML/CSS/JS PWA (`index.html`, `login.html`), no build step
- Service discovery: mDNS via zeroconf (`lighttrans.local`)
- Extras: Pillow (icon, HEIC→JPEG conversion), qrcode (pairing QR)

### API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/messages?since=N` | Incremental message pull |
| POST | `/api/text` | Send text `{text, sender}` |
| POST | `/api/upload` | Upload file(s) (multipart) |
| GET | `/api/files/{id}` | Download / view file |
| DELETE | `/api/messages` | Clear server history |
| POST | `/api/login` | Token login `{token}` |
| GET | `/api/state` | URLs + token |

## 🧪 Tests

```bash
uv run python test_api.py
```

## 🗺 Roadmap

- [ ] iOS Shortcuts share-sheet integration (send from any app)
- [ ] Push notifications to phone (Bark)
- [ ] Two-way clipboard sync
- [ ] Dark mode
- [ ] Config file (port, history size, receive folder)

## 📄 License

[MIT](LICENSE) © [Edison-q](https://github.com/Edison-q)

---

# 中文

## ✨ 特性

- 📝 **文字双向互传**：一边粘贴、另一边点气泡即复制，约 1 秒实时同步
- 🖼️ **图片/文件原样传输**：不压缩、不缩水；电脑端拖拽发送，手机端相册选择
- 📱 **iPhone 主屏幕 PWA**：扫码添加一次，之后点图标即用（mDNS 固定地址 `lighttrans.local`）
- ⚡ **无需互联网**：纯局域网；手机热点下照样传，断网也能用
- 🔐 **访问令牌**：同 WiFi 陌生人无法访问（本机免令牌）
- 🗑️ **消息管理**：单边删除、长按操作面板、多选批量删除
- 🖥️ **静默后台服务**：可选开机自启（无窗口）
- 🌐 **自适应界面**：手机（440×956pt 级别）与电脑共用一页

## 🚀 快速开始（Windows）

环境要求：Python 3.10+、[uv](https://docs.astral.sh/uv/)（或 pip）

```bash
git clone https://github.com/Edison-q/LightTrans.git
cd LightTrans
uv sync                # 安装依赖
uv run server.py       # 或双击 启动LightTrans.bat
```

然后：

1. 浏览器自动打开 `http://localhost:8765`
2. 点右上角「连接手机」
3. iPhone 相机扫码 → 「分享」→「添加到主屏幕」
4. 完成 —— 以后点图标即用（二维码已包含访问令牌）

**日常打开（推荐）：** 双击 `打开LightTrans.vbs`（桌面快捷方式可固定到任务栏）：服务在线则秒开页面；服务不在线会自动拉起、等待就绪后打开，永远不用关心服务状态。`停止服务.bat` 会停掉 8765-8774 端口上的全部实例。

> Windows 11 不允许把脚本快捷方式固定到任务栏，固定任务栏请用 `LightTrans.exe`（预编译启动器，图标已内嵌；源码 `launcher.cs`）。

**开机自启（可选）：** 给 `静默启动.vbs` 创建快捷方式，放入启动文件夹（`Win+R` → `shell:startup`），服务静默后台运行。

## 📱 手机端操作

| 操作 | 方法 |
|------|------|
| 发文字 | 输入框打字，Enter 发送 |
| 发图片/文件 | 点 ➕ |
| 复制文字 | 点任意文字气泡 |
| 查看图片 | 点缩略图全屏预览（✕ / 点空白关闭） |
| 保存图片到相册 | 全屏预览时**长按图片** |
| 长按操作面板 | 复制 / 选择文字 / 下载 / 删除 |
| 部分选择文字 | 长按 → 选择文字 → 再长按拖动手柄 |
| 批量删除 | 点 ☑ 多选 → 勾选 → 删除 |

## 🛡️ 安全说明

- 首次运行自动生成随机访问令牌（`token.txt`）；局域网设备访问需令牌，本机 localhost 免令牌
- 二维码内嵌令牌，手机扫码后零感知
- 传输为 HTTP 明文：防"路人随手访问"，不防"专业网络嗅探"。建议在信任的网络（家庭、个人热点）使用

## 🏫 校园网与热点

- 若设备处于不同网段（如电脑插网线、手机连 WiFi）或网络开启设备隔离，局域网直连可能失败
- **永远有效的兜底方案**：手机开热点 → 电脑连热点 → 两者即处于同一局域网。无需互联网、不耗流量，断网也能传

## 🛠 技术栈

- 后端：Python + FastAPI + uvicorn，单文件（`server.py`）
- 前端：原生 HTML/CSS/JS PWA（`index.html`、`login.html`），无需构建
- 服务发现：mDNS（zeroconf，`lighttrans.local`）
- 其他：Pillow（图标、HEIC→JPG 转换）、qrcode（配对二维码）

## 🗺 路线图

- [ ] iOS 快捷指令分享菜单（任意 App 一键发送）
- [ ] 手机推送通知（Bark）
- [ ] 双向剪贴板同步
- [ ] 深色模式
- [ ] 配置文件（端口、历史条数、接收目录）

## 📄 许可证

[MIT](LICENSE) © [Edison-q](https://github.com/Edison-q)
