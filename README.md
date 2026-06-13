# 题练通

题练通包含两个版本：

```text
desktop/  本地单机 PySide6 桌面版
web/      多人在线 FastAPI + Vue + PostgreSQL 服务器版
```

## 桌面版

适合个人本地刷题、离线使用、打包 Windows exe。

```bash
cd desktop
pip install -r requirements.txt
python main.py
```

Windows 打包说明见：

```text
desktop/WINDOWS_BUILD.md
```

## Web 版

适合部署到服务器，让多个用户通过浏览器使用。

```bash
cd web
cp .env.example .env
docker compose up -d --build
```

访问：

```text
http://服务器IP:8080
```

详细说明见：

```text
web/README.md
```
