---
name: upc-site-check
description: UPC 档案库站点体检。只要用户提到断链、链接检查、站点体检、构建失败、线上 404、search-index 不同步、页面数对不上、"帮我检查网站"，或准备提交/部署本仓库之前，都必须使用本技能。运行并解读 _site_check.py，修复其发现的问题。
---

# UPC 站点体检

本仓库是纯静态站点（GitHub Pages），历史上一半的线上事故是断链与大小写问题（Linux 服务器大小写敏感、`.gitignore` 白名单漏目录）。构建脚本自带构建期校验，本技能是**不依赖完整构建**的独立体检 + 构建期校验的解读与修复指南。

## 第一步：跑体检脚本

```bash
python _工具脚本/_site_check.py            # 全量体检
python _工具脚本/_site_check.py --external # 附加外链抽查（较慢，默认跳过）
```

输出为 JSON 摘要 + 问题清单，每条问题有 `kind`：

| kind | 含义 | 修法 |
|---|---|---|
| MISSING | 链接目标在磁盘上不存在 | 改链接或补文件；注意路径里的空格与中文 |
| CASE | 大小写与磁盘不一致（线上必 404） | 改成磁盘真实大小写 |
| UNTRACKED | 文件存在但没进 git（.gitignore 白名单漏了） | 在 `.gitignore`（及 `_build_site_tail.py` 里 write_deploy_helpers 的模板）加 `!/目录` |
| ANCHOR | 页内/跨页锚点不存在 | 修 id 或链接 |
| STALE-INDEX | search-index.js 与文档页数量/路径不符 | 重跑 `python _工具脚本/_build_site.py` |
| COUNT | 计数口径对不上（论文数/页面数与导航声明） | 检查 `_meta.json` 与导航模板里的硬编码数字 |
| TMP | 临时目录/文件该清理 | 确认后删除（`_tmp*`、`_verify*`、`out.png` 等） |

## 第二步：修复原则

1. **一次只修一类**：先 UNTRACKED（最致命，线上直接 404），再 CASE，再 MISSING，最后锚点与索引。
2. 修复后**必须重跑** `python _工具脚本/_build_site.py`——构建期校验是最终裁判（大小写 + git 感知 + 运行时注入 URL 全查），非零退出即未修完。
3. 批量修链接用脚本，不要手改 200 个文件；改完抽查 5 个。
4. `.gitignore` 是白名单模式：**任何新目录都要同步加到两处**（`.gitignore` 文件 + `_build_site_tail.py` 的 gi 模板），否则下个构建会把你的白名单改回去。

## 提交前 pre-commit hook

仓库已装 `.git/hooks/pre-commit`（调用本体检脚本的快速模式）。hook 拦下提交时，按上表修完再提交；临时绕过用 `git commit --no-verify`（仅限确认问题来自误报时，并要在提交信息里说明）。
