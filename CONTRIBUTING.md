# 代码贡献指南

## 分支管理

```
main          # 主分支，保护分支，稳定版本
└── develop   # 开发集成分支
    └── feature/xxx  # 功能分支
```

## 开发流程

1. 从 `develop` 创建功能分支
2. 在分支上开发，频繁 commit
3. 完成功能后，从 `develop` 合并
4. 推送到远程仓库

## Commit Message 规范

```
<type>(<scope>): <subject>

feat(auth): 实现手机号验证码登录
fix(agent): 修复计划生成超时问题
docs(readme): 更新 README
style(code): 格式化代码
refactor(plan): 重构计划生成逻辑
test(badge): 新增徽章系统测试
chore(deps): 升级 FastAPI 版本
```

## 版本号规范

- `v0.x.0-alpha` — 内部开发版
- `v0.x.0-beta` — 测试版
- `v1.0.0` — 正式版

## 提交前检查

- [ ] 所有单元测试通过
- [ ] 代码格式正确
- [ ] 无未解决的 TODO/FIXME
- [ ] 日志级别使用正确
