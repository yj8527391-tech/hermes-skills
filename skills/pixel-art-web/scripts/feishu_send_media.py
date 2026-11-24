# -*- coding: utf-8 -*-
"""发图片/文件到飞书：按扩展名自动选接口（给使用者看截图用）。

用法:  set FEISHU_CHAT_ID=oc_xxx  →  python feishu_send_media.py <文件...>

图片(png/jpg/jpeg/gif/webp/bmp) -> /im/v1/images + msg_type=image + image_key
其他                          -> /im/v1/files  + msg_type=file  + file_key

⚠️ 图片和文件是**两个不同接口**，发错会失败：图片只能走 /im/v1/images。
API 细节与更多坑见 feishu-file-send 技能（若未装，本脚本已自含完整流程）。
"""
import json, os, sys, requests

ENV = os.environ.get("HERMES_ENV", r"E:\Hermes Agent CN Desktop\data\hermes-home\.env")
CHAT_ID = os.environ.get("FEISHU_CHAT_ID", "")
BASE = "https://open.feishu.cn/open-apis"
IMG_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


def load_env(path):
    cfg = {}
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


def get_token():
    cfg = load_env(ENV)
    r = requests.post(f"{BASE}/auth/v3/tenant_access_token/internal",
                      json={"app_id": cfg["FEISHU_APP_ID"],
                            "app_secret": cfg["FEISHU_APP_SECRET"]}, timeout=20)
    return r.json()["tenant_access_token"]


def send(path, token, chat_id):
    H = {"Authorization": f"Bearer {token}"}
    ext = os.path.splitext(path)[1].lower()
    fn = os.path.basename(path)
    if ext in IMG_EXT:
        with open(path, "rb") as f:
            up = requests.post(f"{BASE}/im/v1/images", headers=H,
                               data={"image_type": "message"},
                               files={"image": (fn, f, "image/png")}, timeout=60).json()
        if up.get("code") != 0:
            return f"上传图片失败 {fn}: {up}"
        content, msg_type = json.dumps({"image_key": up["data"]["image_key"]}), "image"
    else:
        with open(path, "rb") as f:
            up = requests.post(f"{BASE}/im/v1/files", headers=H,
                               data={"file_type": "stream", "file_name": fn},
                               files={"file": (fn, f, "application/octet-stream")},
                               timeout=120).json()
        if up.get("code") != 0:
            return f"上传文件失败 {fn}: {up}"
        content, msg_type = json.dumps({"file_key": up["data"]["file_key"]}), "file"
    sj = requests.post(f"{BASE}/im/v1/messages?receive_id_type=chat_id",
                       headers={**H, "Content-Type": "application/json"},
                       json={"receive_id": chat_id, "msg_type": msg_type,
                             "content": content}, timeout=30).json()
    return f"已发送: {fn}" if sj.get("code") == 0 else f"发送失败 {fn}: {sj}"


def main():
    if len(sys.argv) < 2:
        print("用法: python feishu_send_media.py <文件...>  (需设 FEISHU_CHAT_ID)")
        return
    if not CHAT_ID:
        print("错误: 未设置 FEISHU_CHAT_ID（形如 oc_xxx）")
        return
    token = get_token()
    for p in sys.argv[1:]:
        print(send(p, token, CHAT_ID) if os.path.exists(p) else f"不存在: {p}")


if __name__ == "__main__":
    main()
