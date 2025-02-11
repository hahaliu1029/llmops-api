# 项目中 Node.js 层的作用与关键技术点

## Node.js 层的作用

1. **代理与请求转发**
   - 使用中间件和路由，将请求转发至目标服务（如 `proxyIopsAddr`、`proxyHingeAddr`）。
   - 提供如 KVM 管理、API 聚合等功能。
   - 定制化请求头，如 `X-Forwarded-For`、`X-Real-IP` 等。
   - 处理响应头，去掉一些敏感及不必要的头信息。

2. **静态资源管理**
   - 配置静态文件目录，支持多路径访问。
   - 静态资源包括 `/app/public` 和 `../dist` 目录。
   - 在线文档

3. **安全功能**
   - 支持 HTTPS，动态加载 SSL 证书。
   - 提供 CSRF 防护、HSTS 等安全策略。
   - CSP 策略，限制页面资源加载。

4. **多语言支持**
   - 读取操作系统环境文件，动态设置语言（中文或英文）。

5. **WebSocket 服务**  
   - 实现 KVM 功能，通过 WebSocket 管理服务端连接。
   - 支持 `ws` 和 `wss` 协议。
   - 通过 `target_host` 和 `target_port` 连接目标服务。
   - 代理 WebSocket 如自动发现，webshell， KVM，远程终端等。

6. **证书管理**  
   - 提供证书上传、替换和动态加载功能。
   - 相关接口包括 `/api/certificate-api/uploadCertificate` 等。

7. **视图与模板支持**  
   - 使用 Nunjucks 模板引擎，渲染如 `h5.html` 的页面。

---

## 项目关键技术点

### 1. HTTP 与 HTTPS 配置

```javascript
config.cluster = {
  listen: { port: httpsServer },
  https: {
    key: sslOptions.key,
    cert: sslOptions.cert,
    ciphers: 'ECDHE-RSA-AES128-GCM-SHA256',
  },
};
```

### 2. 请求代理（中间件与路由）

```
const proxyIops = app.middleware.newProxy({
  proxyAddress: app.config.proxyIopsAddr,
  pathRewrite: { '^/api/iops-api': '' },
});
router.all(`${ROOT_URL}iops-api/*`, proxyIops, app.controller.api.index);
```

### 3. 静态资源管理

```javascript
config.static = {
  prefix: '/',
  dir: [
    path.join(appInfo.baseDir, '../dist/'),
    path.join(appInfo.baseDir, '/app/public'),
  ],
  gzip: true, // 启用 gzip 压缩
};
```

### 4. 安全配置

```javascript
config.security = {
  csrf: { enable: false },
  hsts: { enable: true },
  csp: {
    enable: false,
    policy: { "default-src": "'self'" },
  },
};
```

### 5. 多语言支持

```javascript
const language = fs.readFileSync('/etc/INMANAGE', 'utf8').split('=')[1];
config.language = language === 'en' ? 'en' : 'zh_CN';
```

### 6. WebSocket 实现

```javascript
const target = new WebSocket(`wss://${target_host}:${target_port}/kvm`, {
  rejectUnauthorized: false,
  headers: { /* ... */ },
});
target.on('message', data => ws.send(data));
ws.on('message', message => target.send(message));
```

### 7. 证书管理接口

```javascript
router.post(`/api/certificate-api/uploadCertificate`, certificateApiAuth, app.controller.certificate.uploadCertificate);
```

### 8. 视图模板支持

```javascript
config.view = {
  defaultViewEngine: 'nunjucks',
  mapping: { '.html': 'nunjucks' },
}
```