# FRONTEND_STATIC_CHECK_REPORT

- [x] 生产前端不引用 mock/fakeData/demoData/hardcoded/fallbackData: 0，期望 0
- [x] 生产前端无旧版 salary forecast 主链路: []，期望 []
- [x] 前端包含无数据 Empty/暂无数据处理: 12，期望 >0

## Zero Fallback Warnings

共 182 处 `|| 0` / `?? 0` 候选，已作为人工复核项记录；图表关键路径已专项修复为 null/Empty 口径。
