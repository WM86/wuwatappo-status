# wuwatappo-status

🌐 在线状态页：https://wm86.github.io/wuwatappo-status/

鸣潮桌宠（Wuwa Tappo）官方接口的可用性监控，纯静态站。

- 监控目标：`api-mc-wuwatappo.kurogames-global.com`
- 探测：GitHub Actions 每 5 分钟跑一次 `probe/probe.py`，把结果并进 `data/history.json`（保留最近 1000 次）
- 页面：`index.html` 读同一份 JSON，显示当前状态、各接口延迟、24 小时可用率

## 探测的四项

| id | 接口 | 判据 |
| --- | --- | --- |
| common | `/api/common/activity-config` | HTTP 200 且业务码 `code:0` |
| atlas | `/api/common/atlas` | HTTP 200 且业务码 `code:0` |
| socket | `/socket.io/?EIO=4&transport=polling` | 握手回包里带 `sid` |
| auth | `/api/frontend/user/me` | 拿到任何业务响应（401 未鉴权也算在线） |

注意：探测跑在 GitHub 的境外机房，跟国内玩家本机看到的链路不完全一致，这里只说明官方接口本身还能不能应答。

## 本地手动跑一次

```bash
python3 probe/probe.py
```
