# plugins/ — 本地插件与测试市场

两个本地插件的**打包源**，技能正本在 `.agents/skills/`（ZCode 会直接发现它们；
本目录是给「插件市场」分发/装机用的副本）。

| 插件 | 技能 | 版本 |
|---|---|---|
| `upc-coach/` | upc-modeling · upc-writing · upc-figures · upc-review | 0.1.0 |
| `upc-archive/` | upc-site-check · upc-new-edition · upc-content-style | 0.1.0 |

`marketplace.json` 是本地测试市场清单（dev-upc-archive）。

## 同步与更新

改了 `.agents/skills/` 下的技能后同步打包源并升版本：

```bash
python _工具脚本/_sync_plugins.py          # 复制 .agents/skills → plugins/*/skills/
# 然后手动递增两个 .zcode-plugin/plugin.json 的 version，并同步 marketplace.json 的 version 字段
```

安装方式见对话记录：插件市场 → 添加 → 粘贴本目录绝对路径 → 个人市场 → 安装。
