---
name: feishu-file-send
description: Use when 发文件/文档到飞书。走飞书开放API上传发送。
version: 1.0.0
author: Alice
platforms: [windows]
metadata:
  hermes:
    tags: [feishu, lark, file-send, media, api]
    category: communication
---

# 飞书文件发送

## 何时使用

- 使用者要求把文件/图片/文档发到飞书(裸文本可用 hermes send,文件不行)
- `hermes send --to feishu` 报错 `feishu plugin not registered or missing standalone_sender_fn`

## 关键背景

本机 `FEISHU_CONNECTION_MODE=websocket`,飞书插件没有注册独立发送器(standalone_sender_fn),
因此 **`hermes send` 无法向飞书发送任何内容**(文本也不行)。唯一可行路径是直接调飞书开放API。

## 配置来源

`E:\Hermes Agent CN Desktop\data\hermes-home\.env`:
- `FEISHU_APP_ID` / `FEISHU_APP_SECRET`(从文件读取,勿 print,会被脱敏)
- API 域固定 `https://open.feishu.cn`(注意 `.env` 里 `FEISHU_DOMAIN` 值只是 `feishu` 标识,不是 URL)

## chat_id 获取

```
"E:/Hermes Agent CN Desktop/data/versions/<版本>/hermes-agent-cn-runtime-win32-x64.exe" send --list
```
或读 `hermes-home/sessions/sessions.json` 中 `agent:main:feishu:...` 的 `origin.chat_id`(形如 `oc_xxx`)。

## 发送文本

```python
TOKEN = requests.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": APP_ID, "app_secret": APP_SECRET}).json()["tenant_access_token"]
requests.post("https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={"receive_id": CHAT_ID, "msg_type": "text",
          "content": json.dumps({"text": "内容"}, ensure_ascii=False)})
```

## 发送文件(上传+发送两步)

```python
# 1. 上传,拿 file_key
up = requests.post("https://open.feishu.cn/open-apis/im/v1/files",
    headers={"Authorization": f"Bearer {TOKEN}"},
    data={"file_type": "stream", "file_name": fn},
    files={"file": (fn, open(path, "rb"), "application/octet-stream")})
file_key = up.json()["data"]["file_key"]
# 2. 发送
requests.post("https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
    headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    json={"receive_id": CHAT_ID, "msg_type": "file",
          "content": json.dumps({"file_key": file_key})})
```

## 常见坑

| 现象 | 原因/解法 |
|:----|:---------|
| `standalone_sender_fn` 报错 | websocket 模式不支持,直接用本技能 |
| `unknown url type: 'feishu/...'` | `.env` 的 `FEISHU_DOMAIN=feishu` 不是 URL,硬编码 `https://open.feishu.cn` |
| docx 上传被拒 | `file_type` 用 `stream`;图片 `image`,视频 `mp4` |
| bash 下路径报错 | python 传参用 Windows 路径 `E:/xxx`,勿用 `/e/xxx` |

## 清理

含 token 的临时文件用完即删,避免密钥泄漏。
