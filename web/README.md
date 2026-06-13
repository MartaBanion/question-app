# 题练通 Web

这是题练通的多人在线版本，技术栈为 FastAPI + Vue + PostgreSQL + Docker + Nginx。

## 功能范围

第一版已包含：

- 用户注册、登录和 JWT 鉴权
- 用户级数据隔离
- Excel 题库上传预览和确认导入
- 题库列表、顺序/随机/背题模式取题
- 提交答案、自动记录答题结果
- 错题本、收藏、学习统计 API
- Vue 前端基础页面
- Docker Compose 部署

## 本地开发

后端：

```bash
cd web/backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

前端：

```bash
cd web/frontend
npm install
npm run dev
```

## Docker 部署

```bash
cd web
cp .env.example .env
# 修改 .env 里的 SECRET_KEY
# 启动服务
docker compose up -d --build
```

访问：

```text
http://服务器IP:8080
```

## 生产部署建议

- 用随机长字符串替换 `SECRET_KEY`
- 用云数据库或独立 PostgreSQL 实例保存数据
- 在服务器前面配置 HTTPS，例如 Caddy、Nginx + Certbot 或云厂商证书
- 定期备份 PostgreSQL 数据卷
