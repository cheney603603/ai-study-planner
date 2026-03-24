# 日志目录

本目录用于存储应用运行日志。

## 日志文件

| 文件 | 说明 | 级别 |
|------|------|------|
| app.log | 应用日志 | INFO+ |
| agents.log | AI Agent 执行日志 | DEBUG+ |
| api.log | API 请求日志 | INFO+ |
| error.log | 错误日志 | ERROR+ |

## 日志格式

```
2026-03-24 18:50:00 | INFO | api.auth | 发送验证码
```

## 查看命令

```bash
# 实时查看应用日志
tail -f logs/app.log

# 查看错误日志
type logs\error.log
```

---
*请勿删除本目录*
