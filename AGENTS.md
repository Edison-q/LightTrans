# LightTrans — 项目交接本

> 给未来的协作者（AI 助手/贡献者）的项目速览。最近更新：2026-09-10。

## 项目是什么

局域网手机↔电脑传输工具（文字/图片/文件），像聊天一样互传。FastAPI 单文件后端 + 原生 HTML PWA 前端，无构建步骤。已开源 MIT（github.com/Edison-q/LightTrans）。

## 架构速览

| 文件 | 职责 |
|------|------|
| `server.py` | 全部后端：消息 Store（内存 + history.json，epoch/seq 增量同步）、令牌认证（localhost 免令牌）、mDNS + 15s IP 变化监听、HEIC→JPG、端口 8765-8774 自动选、**HTTPS 双通道（http:PORT + https:PORT+1，iOS 主屏强制 https）** |
| `index.html` | 全部前端：1s 轮询同步、图片查看器（跟手分页）、单边删除/多选（批量删除+批量保存 zip）/误删救援（长按清空按钮恢复）、逐文件发送进度 |
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

## HTTPS 通道（2026-09-06 实现后停用，代码保留）

**背景**：iOS 主屏 Web App 强制 HTTPS。**版本定位（2026-09-10 用户实测确认）：iOS 26.6.1 引入强制策略**——8.25 在旧版（26.6 或更早）http 主屏可用，升级 26.6.1 后添加主屏直接提示「需要 https」。26.6.1 beta 于 2026-08-11 推送，窗口与行为变化完全吻合。此拦截在 iOS 系统层，与网络/代码无关。

**实现**：server.py 双通道——`http:PORT`（8765）+ `https:PORT+1`（8766），同一 FastAPI app；证书缺失自动降级纯 http（`build_urls`）。已自测通过（TLS1.3 握手、证书链验证、页面 200）。

**停用原因（实测铁证）**：iPhone 作为热点宿主时，手机访问热点内电脑的 **HTTPS 流量整体不可达**——http 通、https 死；换端口（8766/8767）、换服务器实现（uvicorn/std 库）全部一样死（Safari 报「丢失网络连接」）。叠加「iOS 主屏强制 https」形成苹果两头堵：**「手机开热点给电脑」场景下主屏图标无解**。用户日常正是热点场景 → 决定不再折腾：证书文件已全删、手机信任已删。当前手机用法 = Safari 收藏夹 `http://172.20.10.2:8765`（实测通）。

**复活条件**：网络形态变为「手机是普通 WiFi 客户端」（电脑开热点/路由器，宿舍或家 WiFi）→ 重新生成证书（命令见下）+ 手机装 ca.cer 信任 + 主屏加 `https://lighttrans.local:8766`。该场景未实测，理论上 mDNS + https 均正常。

**复现命令**（先重建 san.cnf，内容见下；git-bash 执行）：
```bash
openssl req -x509 -newkey rsa:2048 -keyout ca.key -out ca.crt -days 3650 -nodes -subj "/CN=LightTrans Local CA"
openssl req -newkey rsa:2048 -keyout server.key -out server.csr -nodes -subj "/CN=lighttrans.local"
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 3650 -extfile san.cnf -extensions alt_names
openssl x509 -in ca.crt -outform der -out ca.cer
```
san.cnf 内容：
```
[req]
distinguished_name = dn
[dn]
[alt_names]
subjectAltName = @sans
extendedKeyUsage = serverAuth
[sans]
DNS.1 = lighttrans.local
DNS.2 = localhost
IP.1 = 127.0.0.1
IP.2 = 172.20.10.2
IP.3 = 192.168.137.1
```

**坑**：Windows curl 的 schannel 对自签 CA 握手静默失败——验证证书链用 `openssl s_client -CAfile ca.crt`。私钥（*.key）已被 .gitignore 保护。

## 里程碑 2026-09-10：批量保存 + 批量发送进度（a9e17a6）

- **批量保存**：多选栏新增「💾 保存」——**电脑端**选中文件逐个直接下载进「下载」文件夹（`/api/files?download=true`）；**手机端**打包 zip 进「文件」App（`/api/zip?ids=…`，ZIP_STORED 原样打包、失效文件自动跳过、路径穿越已防护），按钮文案按平台显示「保存」/「保存 (zip)」。选中纯文字消息时按钮置灰；失效图片自动跳过并提示。
- **批量发送**：`sendFiles` 改为逐个上传 + 进度提示（「正在发送 2/5：文件名」→「已发送 N 个文件 ✓」），中途失败能定位到具体文件。
- **验证**：/api/zip 接口 4/4（打包内容无损、混入失效自动跳过、全失效 404、路径穿越 404）；UI 流程真浏览器（Edge 无头 CDP）走通多选→保存全路径，批量发送 2 文件实测通过。下载落盘在无头测试环境被 Windows 应用控制策略拦截（连静态 icon.png 也拦，浏览器已收到全部字节）——属测试环境限制非产品缺陷，真实 Edge 正常。
- **手机端「存相册」未做**：iOS 网页无法批量写相册（zip 进「文件」App 已可用）。候选：iOS 快捷指令逐张存相册（体验最佳），待用户选。
- 附：上一会话的 HTTPS 双通道代码（server.py）与 .gitignore 私钥保护随本次一并入库（无证书时纯 http，无害）。

## 当前状态与待办（2026-09-06 收尾）

**核心功能全部正常**（传输/聊天/扫码/网络自适应均已实测）。用户当前固定用法：
- 手机：Safari 收藏夹 `http://172.20.10.2:8765`（热点场景实测通；IP 若变则改收藏夹地址或扫电脑二维码）
- 电脑：双击任务栏 LightTrans.exe，照旧

**已探明并封存的三条死路（勿再折腾）：**
1. 主屏图标 × 手机开热点：苹果两头堵（主屏强制 https + 热点宿主场景 https 流量被 iOS 掐断），无解，铁证见 HTTPS 节
2. lighttrans.local × 手机开热点：iOS 热点宿主不解析 .local（mDNS 怪癖）
3. Edge 152 手动「作为应用安装」：数据不落盘

**任务栏窗口图标（挂起）：** `--app` 模式未装 PWA 时 Windows 任务栏窗口图标 = Edge logo（Chromium 硬行为，删 Favicons 无效已实测）。下一步备选 = WebAppInstallForceList 注册表策略自动安装（`HKCU\SOFTWARE\Policies\Microsoft\Edge\WebAppInstallForceList`，值名 `1`，JSON `{"url":"http://localhost:8765/","default_launch_container":"window"}`；force 装后不可手动卸载，删策略键即恢复）。未经用户授权不动。

**待办：**
- **停止服务.bat 失效**（实测杀不掉监听进程，tasklist/findstr 匹配逻辑待查；用户日常依赖）
- 防火墙残留规则「LightTrans HTTPS 8766」（无害，放行一个端口；删除需管理员 UAC，用户未决定）

## 已知网络结论

- 手机热点（主卡/副卡均可）：✓ 可用。换热点后旧 IP 地址失效属正常。`lighttrans.local` 仅在「手机作为普通 WiFi 客户端」时可靠；「手机开热点给电脑」时 iOS 解析 .local 失败 + **手机访问电脑 HTTPS 流量被 iOS 整体掐断（http 通 https 死）**——详见 HTTPS 节铁证。
- 运营商公共 WiFi：✗ 永久不可用（AP 隔离）。
- 宿舍有线+同运营商 WiFi 混搭：大概率 ✗（运营商隔离）。宿舍方案：电脑开热点（Windows 移动热点）或自购路由器。

## 用户环境

Windows 11 + iPhone（PWA 主屏）。用户非程序员（会跑终端命令），中文交流，重视界面美观与交互流畅；改动前先讨论方案，获得明确授权再动工。**笔记本无网线口，网线方案需拓展坞（用户不倾向）；日常主场景=手机开热点给电脑（勿当应急场景设计）。**

## 功能候选（用户按需挑选，小步做）

剪贴板同步、传输进度条（真实百分比；已有逐文件进度版）、深色模式、文件夹拖拽打包、iOS 快捷指令分享、视频/音频在线播放、txt/md 预览、README 升级（GIF+双语）、一键安装脚本/Releases。
