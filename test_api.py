# -*- coding: utf-8 -*-
"""LightTrans 接口自测脚本（仅用标准库）"""
import json, os, sys, tempfile, urllib.parse, urllib.request

BASE = "http://127.0.0.1:8765"
ok = fail = 0

def check(name, cond, extra=""):
    global ok, fail
    if cond:
        ok += 1
        print(f"  PASS  {name} {extra}")
    else:
        fail += 1
        print(f"  FAIL  {name} {extra}")

def get(p):
    return urllib.request.urlopen(BASE + p).read()

def post_json(p, obj):
    req = urllib.request.Request(BASE + p, data=json.dumps(obj).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req).read()

# 1. 清空现场，从零开始（消息编号单调递增不清零，取当前编号作为基准）
urllib.request.urlopen(urllib.request.Request(BASE + "/api/messages", method="DELETE"))
base = json.loads(get("/api/messages?since=0"))["current_seq"]

# 2. 发送文字（模拟手机 -> 电脑）
r = json.loads(post_json("/api/text", {"text": "你好，LightTrans！这是手机发来的文字", "sender": "手机"}))
check("发送文字", r.get("seq") == base + 1 and r.get("text", "").startswith("你好"))

# 3. 再发一条（模拟电脑 -> 手机）
r = json.loads(post_json("/api/text", {"text": "收到！电脑回复你", "sender": "电脑"}))
check("发送第二条", r.get("seq") == base + 2)

# 4. 增量拉取（since=base+1 应只返回第二条）
d = json.loads(get("/api/messages?since=%d" % (base + 1)))
check("增量拉取", len(d["items"]) == 1 and d["items"][0]["seq"] == base + 2, f"epoch={d['epoch']}")

# 5. 全量拉取
d = json.loads(get("/api/messages?since=0"))
check("全量拉取", len(d["items"]) == 2)

# 6. 上传文件（模拟手机传文件）
tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")
content = ("LightTrans 文件传输测试 " * 100).encode() + b"\x00\x01\x02END"
tmp.write(content); tmp.close()
boundary = "----LightTransBoundary"
body = b""
body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"sender\"\r\n\r\n手机\r\n").encode()
body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"files\"; filename=\"测试文档.txt\"\r\nContent-Type: text/plain\r\n\r\n").encode()
body += content + b"\r\n"
body += (f"--{boundary}--\r\n").encode()
req = urllib.request.Request(BASE + "/api/upload", data=body,
                             headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
up = json.loads(urllib.request.urlopen(req).read())
check("上传文件", len(up) == 1 and up[0]["size"] == len(content) and up[0]["name"] == "测试文档.txt", f"id={up[0]['id']}")

# 7. 下载回读并比对
fid = up[0]["id"]
dl = urllib.request.urlopen(BASE + "/api/files/" + urllib.parse.quote(fid)).read()
check("下载内容一致", dl == content, f"({len(dl)} bytes)")
hdr = urllib.request.urlopen(BASE + "/api/files/" + urllib.parse.quote(fid) + "?download=1").headers
check("下载头正确", "attachment" in hdr.get("Content-Disposition", ""))

# 8. 中文文件名重名处理
body2 = body.replace("测试文档.txt".encode(), "测试文档.txt".encode())
req = urllib.request.Request(BASE + "/api/upload", data=body2,
                             headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
up2 = json.loads(urllib.request.urlopen(req).read())
check("重名自动改名", up2[0]["id"] != up[0]["id"], f"-> {up2[0]['id']}")

# 9. 清空接口
urllib.request.urlopen(urllib.request.Request(BASE + "/api/messages", method="DELETE"))
d = json.loads(get("/api/messages?since=0"))
check("清空生效", d["items"] == [], f"epoch={d['epoch']}")

# 10. 非法文件访问
try:
    urllib.request.urlopen(BASE + "/api/files/../server.py")
    check("路径穿越防护", False)
except urllib.error.HTTPError as e:
    check("路径穿越防护", e.code in (404, 400))

os.unlink(tmp.name)
print(f"\n结果: {ok} 通过, {fail} 失败")
sys.exit(1 if fail else 0)
