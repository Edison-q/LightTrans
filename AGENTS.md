# LightTrans — 项目交接本

> 给未来的协作者（AI 助手/贡献者）的项目速览。最近更新：2026-09-05。

## 项目是什么

局域网手机↔电脑传输工具（文字/图片/文件），像聊天一样互传。FastAPI 单文件后端 + 原生 HTML PWA 前端，无构建步骤。已开源 MIT（github.com/Edison-q/LightTrans）。

## 架构速览

| 文件 | 职责 |
|------|------|
| `server.py` | 全部后端：消息 Store（内存 + history.json，epoch/seq 增量同步）、令牌认证（localhost 免令牌）、mDNS + 15s IP 变化监听、HEIC→JPG、端口 8765-8774 自动选 |
| `index.html` | 全部前端：1s 轮询同步、图片查看器（跟手分页）、单边删除/多选/误删救援（长按清空按钮恢复） |
| `login.html` | 令牌验证页 |
| `gen_icon.py` | 图标生成：icon.png（180）、icon.ico（16-256 多尺寸）、icon-192/512.png |
| `test_api.py` | 冒烟测试 |

## 启动脚本体系（Windows）

| 入口 | 行为 |
|------|------|
| `打开LightTrans.vbs` | **日常入口（推荐）**。服务在线→秒开 Edge App 窗口；不在线→静默拉起→等就绪→开窗口。桌面有同款快捷方式（高清 ico 图标） |
| `LightTrans.exe` | 任务栏固定入口（`launcher.cs` 用系统自带 csc 编译，内嵌高清图标）。**Win11 拒绝固定脚本快捷方式，必须用 exe**。运行 = 拉起同目录 vbs 后立即退出。重新编译：`C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe /nologo /target:winexe /win32icon:icon.ico /out:LightTrans.exe launcher.cs` |
| `静默启动.vbs` + `silent-start.bat` | 后台常驻服务（开机自启，Startup 文件夹有快捷方式）。bat 内有防重入检查 |
| `启动LightTrans.bat` | 前台调试模式（终端里跑，**关窗口=停服务**，设计如此） |
| `停止服务.bat` | 扫 8765-8774 全端口杀 python 实例 |

### 脚本踩坑记录（重要）
- **bat 必须 CRLF + ASCII**：LF 行尾或 UTF-8 中文会让 cmd 行错位/乱码。
- **for /f 命令串里的 `^`**：正则取反 `[^0-9]` 必须写 `[^^0-9]`（第一层解析吞一个 ^）；`for` 变量必须 `%%a`。
- **vbs 中文必须 GBK 编码写盘**（wscript 按 ANSI 解析；UTF-8 中文会乱码）。
- **MSXML2.ServerXMLHTTP 探测空端口极慢**（每端口 ~2s 且超时设置不生效）——端口扫描一律用 `netstat`（0.06s），HTTP 只用于确认 `/health`。
- 任务栏图标用 `/favicon.ico`（真 ICO 多尺寸）；旧版把它路由到 PNG 导致 Edge App 任务栏图标模糊。
- **Edge favicon 双重缓存坑**：Favicons SQLite（图标位图）+ HTTP cache（响应缓存）都要处理——改图标后必须同时：① 路由 Cache-Control 改 no-cache ② 页面引用加版本号 `?v=2` ③ 必要时删 `%LOCALAPPDATA%\Microsoft\Edge\User Data\Default\Favicons`（需先杀 msedge.exe 全部后台进程，否则文件锁）。

## 当前状态与待办（2026-09-05）

**核心功能全部正常**（传输/聊天/扫码/网络自适应均已实测）。最近两天的折腾集中在两块外围：网络地址过期、任务栏窗口图标。

**网络（2026-09-05 已解决根因）：**
- 手机打不开的根因：电脑换网络后 IP 变化（10.2.x → 热点 172.20.10.x），手机主屏/旧二维码存的是旧地址。15s IP 自适应已验证工作（日志：IP 变化自动更新 mDNS + 二维码）。
- `lighttrans.local` 在「手机开热点给电脑」场景解析失败（iOS 系统怪癖，非我方 bug）；宿舍 WiFi 场景仍可用。
- iPhone 热点给电脑的 IP 稳定分配 172.20.10.2，但换网络/重开热点可能变——主屏存 IP 属临时方案。

**任务栏窗口图标（2026-09-05 战役记录，重要教训）：**
- 根因：`--app` 模式窗口**未安装成 PWA 时**，Windows 任务栏窗口图标 = Edge logo（Chromium 硬行为，根本不读 favicon）。删 Favicons 缓存无效（已实测）。
- Edge 152（新版本）手动「作为应用安装」两次尝试均无数据落盘（Preferences/Web Applications 无记录）——疑似 152 行为变化，别再让用户手动装。
- **下一步方案（未执行）**：WebAppInstallForceList 策略自动安装。写注册表 `HKCU\SOFTWARE\Policies\Microsoft\Edge\WebAppInstallForceList`，值名 `1`，内容 JSON `{"url":"http://localhost:8765/","default_launch_container":"window"}`，重启 Edge 自动装。注意：force 安装后无法手动卸载，删策略键即恢复（需向用户说明）。
- 用户情绪低点：连续两天外围 bug 产生挫败感，认为「项目烂尾」（实际核心无恙）。下次会话先对齐、再动手，避免方案来回摇摆。

**待办：**
- **git 未提交**：两次会话的改动全在工作区（新增 打开LightTrans.vbs / LightTrans.exe / launcher.cs / gen_icon.py / icon.ico / icon-192.png / icon-512.png / AGENTS.md；修改 server.py / index.html / README.md / silent-start.bat / 停止服务.bat）。提交前问用户
- 网络测试：宿舍网线直连（预期 ✗，且用户笔记本无网线口，需拓展坞——用户不倾向）→ 电脑开热点（Windows 移动热点，主方案）
- 任务栏最终方案未决（图标问题挂起）：Edge App 固定 / 双图标 / 自动唤醒（Service Worker + lighttrans:// 协议）

## 已知网络结论

- 手机热点（主卡/副卡均可）：✓ 可用。换热点后旧 IP 地址失效属正常。`lighttrans.local` 仅在「手机作为普通 WiFi 客户端」（宿舍 WiFi）时可靠；「手机开热点给电脑」时 iOS 解析 .local 失败（系统怪癖），主屏只能存 IP（iPhone 热点稳定给 172.20.10.2）。
- 运营商公共 WiFi：✗ 永久不可用（AP 隔离）。
- 宿舍有线+同运营商 WiFi 混搭：大概率 ✗（运营商隔离）。宿舍方案：电脑开热点（Windows 移动热点）或自购路由器。

## 用户环境

Windows 11 + iPhone（PWA 主屏）。用户非程序员（会跑终端命令），中文交流，重视界面美观与交互流畅；改动前先讨论方案，获得明确授权再动工。

## 功能候选（用户按需挑选，小步做）

剪贴板同步、传输进度条、深色模式、文件夹拖拽打包、iOS 快捷指令分享、视频/音频在线播放、txt/md 预览、README 升级（GIF+双语）、一键安装脚本/Releases、HTTPS（暂缓）。
