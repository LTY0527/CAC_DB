# API_CONTRACT_CHECK_REPORT

本报告由 `python scripts/check_api_contract.py` 生成，用于检查主要接口是否能按前端预期返回。

| 状态 | 角色 | 接口 | 参数 | HTTP/code | 数据条数 | 字段缺失 | 全 0 风险 | 备注 |
|---|---|---|---|---|---:|---|---|---|
| 通过 | teacher | `/auth/login` | `{}` | 200/0 | 0 | - | 否 | success |
| 通过 | government | `/auth/login` | `{}` | 200/0 | 0 | - | 否 | success |
| 通过 | public | `/auth/login` | `{}` | 200/0 | 0 | - | 否 | success |
| 通过 | teacher | `/demand/kpi` | `{}` | 200/0 | 1 | - | 否 | success |
| 通过 | teacher | `/demand/forecast` | `{}` | 200/0 | 120 | - | 否 | success |
| 通过 | teacher | `/enrollment/matching` | `{'major_code': 'all', 'limit': 10}` | 200/0 | 10 | - | 否 | success |
| 通过 | teacher | `/major/optimization` | `{}` | 200/0 | 86 | - | 否 | success |
| 通过 | teacher | `/training/rules` | `{}` | 200/0 | 271 | - | 否 | success |
| 通过 | teacher | `/recommendation/summary` | `{}` | 200/0 | 1 | - | 否 | success |
| 通过 | teacher | `/recommendation/student` | `{'graduate_id': '7'}` | 200/0 | 3 | - | 否 | success |
| 通过 | teacher | `/report/ai` | `{}` | 200/0 | 1 | - | 否 | success |
| 通过 | teacher | `/employment-summary` | `{}` | 200/0 | 172 | - | 否 | success |
| 通过 | teacher | `/training-program-optimization` | `{}` | 200/0 | 200 | - | 否 | success |
| 通过 | government | `/demand/kpi` | `{}` | 200/0 | 1 | - | 否 | success |
| 通过 | government | `/demand/forecast` | `{}` | 200/0 | 120 | - | 否 | success |
| 通过 | government | `/monitor/school` | `{}` | 200/0 | 20 | - | 否 | success |
| 通过 | government | `/recommendation/summary` | `{}` | 200/0 | 1 | - | 否 | success |
| 通过 | public | `/monitor/school` | `{}` | 200/0 | 20 | - | 否 | success |
