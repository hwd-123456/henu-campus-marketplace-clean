# API 字段合同 — 跑腿（Errands）

> 交付包三（成员 3 · 张显 · 后端负责人）。本文件是团队统一字段合同，
> 前后端以此为唯一依据；变更需先改本文件再改代码。

## 状态机

```
open ──claim(接单)──> claimed ──complete(完成)──> completed
  │                      │
  └── 409: 创建者不能接自己的单
                         └── 409: 仅 claimed 可完成; 403: 仅创建者/接单者可完成
```

- 新任务创建即为 `open`
- 接单后为 `claimed`（`claimer_id` 写入接单人）
- 完成后为 `completed`（终态，不能再被接单）

## 统一字段（Errand 对象）

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `task_id` | string | 服务端生成，`task-` 前缀 + 12 位 hex |
| `creator_id` | string | 发布者（取自登录态，不信任客户端）|
| `claimer_id` | string \| null | 接单者；未接单为 `null` |
| `campus` | string | 校区，如 `金明校区` |
| `title` | string | 任务标题，如 `代取快递` |
| `origin` | string | 取件地 |
| `destination` | string | 送达地 |
| `reward` | number | 报酬（元），≥ 0 |
| `status` | string | `open` / `claimed` / `completed` |
| `note` | string \| null | 接单/完成时的可选备注 |
| `created_at` | string (ISO) | 服务端时间 |
| `updated_at` | string (ISO) | 服务端时间 |

## 接口

### GET /api/v1/errands — 列表（公开）

Query 参数：`campus`（可选）、`status`（可选）。按 `created_at` 倒序。

```json
[
  {
    "task_id": "task-3f9c2a1b8d4e",
    "creator_id": "user-001",
    "claimer_id": null,
    "campus": "金明校区",
    "title": "代取快递",
    "origin": "金明校区北门",
    "destination": "生活服务中心",
    "reward": 3,
    "status": "open",
    "note": null,
    "created_at": "2026-10-14T12:00:00",
    "updated_at": "2026-10-14T12:00:00"
  }
]
```

### POST /api/v1/errands — 创建（需登录）

请求体：

```json
{
  "campus": "金明校区",
  "title": "代取快递",
  "origin": "金明校区北门",
  "destination": "生活服务中心",
  "reward": 3
}
```

响应 `201`：完整 Errand 对象（见上，`status="open"`，`claimer_id=null`）。

错误：`401` 未登录；`422` 字段校验失败（如 `reward < 0`）。

### POST /api/v1/errands/{task_id}/claim — 接单（需登录）

请求体可选：`{"note": "半小时到"}`。

响应 `200`：Errand 对象（`status="claimed"`，`claimer_id=<当前用户>`）。

错误：`401` 未登录；`404` 任务不存在；`409` 非 `open` 状态，或创建者接自己的单。

### POST /api/v1/errands/{task_id}/complete — 完成（需登录）

仅创建者或接单者可调用（`403` 否则）。

请求体可选：`{"note": "已送到北门驿站"}`。

响应 `200`：Errand 对象（`status="completed"`）。

错误：`401` 未登录；`404` 任务不存在；`409` 非 `claimed` 状态；`403` 非创建者/接单者。

## 认证方式

`Authorization: Bearer <campuscart session token>`（与登录接口签发的 token 相同）。

## 交互式文档

后端启动后访问 `/docs`，Errands 分组下可见全部四个接口。
