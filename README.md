# SSO Monorepo (Casdoor)

基于 Casdoor 的可运行 SSO 示例（门户 + 应用1 + 应用2），均为 FastAPI 后端与 Jinja2 模板，支持 OAuth2/OIDC 授权码模式、会话管理、用户信息获取与跨应用单点登录跳转。

## 先决条件
- 已有 Casdoor 服务: 例如 `http://192.168.12.225:8000`
- 在 Casdoor 中创建 3 个应用：Portal、App1、App2
  - 分别获取 Client ID 与 Client Secret
  - 设置回调URI：
    - Portal: `http://localhost:9000/callback`
    - App1: `http://localhost:9001/callback`
    - App2: `http://localhost:9002/callback`

## 配置
复制 `.env/.env.example` 为 `.env/.env.local` 并填入各应用凭证：

```
cp .env/.env.example .env/.env.local
```

## 安装与运行
```
pip install -r requirements.txt
chmod +x scripts/dev.sh
./scripts/dev.sh
```

启动后：
- Portal: http://localhost:9000
- App1: http://localhost:9001
- App2: http://localhost:9002

## 功能点
- OAuth2/OIDC 登录与回调
- ID Token 验证（基于 JWKS）
- UserInfo 获取并展示
- 会话 Cookie 管理
- 门户展示按用户信息动态显示应用入口（示例按存在 email/username 即可）
- 从门户一键跳转到目标应用登录（Casdoor 已登录将免登）

## 目录结构
```
sso-monorepo/
  common/
    src/
      config.py
      oidc.py
  portal/
    src/
      main.py
      session.py
    templates/
      base.html
      index.html
  app1/
    src/main.py
    templates/
      base.html
      index.html
      protected.html
  app2/
    src/main.py
    templates/
      base.html
      index.html
      protected.html
```

## 备注
- 如需前端 React，可在后续阶段替换模板层，服务端接口保持不变。

