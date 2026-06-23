---
name: baidu-intranet-access
description: 百度内网访问配置与问题排查指南，包含 VPN、内网域名、认证等常见场景
triggers:
  - 内网
  - intranet
  - vpn
  - 内网访问
  - baidu intranet
  - 百度内网
argument-hint: "[场景: vpn|auth|dns|proxy]"
---

# Baidu Intranet Access Skill

## Purpose

处理百度内网访问相关的配置、连接问题和最佳实践，包括 VPN 连接、内网域名解析、代理设置、身份认证等场景。

## When to Activate

- 用户遇到内网服务无法访问的问题
- 需要配置开发环境连接百度内网
- 内网 API、服务、文档的访问指引
- VPN 断线、认证失败等故障排查

## Workflow

### 1. 诊断访问问题

```bash
# 检查 VPN 连接状态
ping -c 3 <内网域名>

# 检查 DNS 解析
nslookup <内网域名>

# 检查代理设置
echo $http_proxy $https_proxy $no_proxy
```

### 2. 常见问题处理

**VPN 未连接**
- 确认 VPN 客户端已启动并登录
- 检查账号是否有访问对应资源的权限

**DNS 解析失败**
- 确认 VPN 连接后 DNS 服务器指向内网 DNS
- 手动设置 DNS: `sudo networksetup -setdnsservers Wi-Fi <内网DNS地址>`

**代理配置**
```bash
# 临时设置代理（终端）
export http_proxy=http://<proxy_host>:<port>
export https_proxy=http://<proxy_host>:<port>
export no_proxy=localhost,127.0.0.1,*.baidu.com
```

### 3. 开发环境配置

**Git 代理**
```bash
git config --global http.proxy http://<proxy_host>:<port>
git config --global https.proxy http://<proxy_host>:<port>
# 内网 Git 仓库不走代理
git config --global http.https://icode.baidu.com.proxy ""
```

**npm/yarn 内网源**
```bash
# 使用内网镜像
npm config set registry http://registry.<内网域名>/
```

## Examples

```
/oh-my-claudecode:baidu-intranet-access vpn
/oh-my-claudecode:baidu-intranet-access dns
/oh-my-claudecode:baidu-intranet-access proxy
```

## Notes

- 内网资源地址以 `.baidu.com`、`.baidubce.com` 等内网域名结尾
- 敏感信息（密码、token）不要记录在此文件中
- 具体内网地址和配置参考团队内部文档
