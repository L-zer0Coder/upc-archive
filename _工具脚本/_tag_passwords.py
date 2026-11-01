# -*- coding: utf-8 -*-
"""_tag_passwords.py — 给 73 张模式卡片写入 pwd_tags（七条获奖密码的结构化枚举标签）。

角色定位（2026-11-01 决策）：pwd_tags 是基于关键词对卡片字段（core_idea/models/
numerics/gold_secret/reusable/pitfalls）的自动标注，属**管线元数据**——比"赏析正文
显式提及"扫描口径更窄（信息量更低），因此**不用于**首页 n/73 计数（该口径仍是
_build_site._rule_counts 的赏析正文扫描，可复算）。本标签的用途：未来用 LLM 逐篇
精修为人工级标签后的精确计数底座；以及跨卡筛选（某密码的论文清单）。

幂等：重复运行覆盖 pwd_tags。卡片是提炼管线产物、脚本不再重写其他字段——安全。
"""
import os, sys, json, glob, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 与 _build_site.RULES 同一组关键词（宁宽勿漏）；两处必须同步——蓝图「单一数据源」管辖
KEYS = {
    "统一货币": ("统一货币", "Δv", "比冲", "换算成可比", "同一量纲", "统一量纲"),
    "端点锚定再外推": ("锚定", "校准", "实测数据"),
    "模糊词操作化": ("模糊词", "操作化", "可判定", "翻译成"),
    "模型分层递进": ("分层递进", "理想化", "关键修正"),
    "验证三件套": ("三件套", "收敛性", "灵敏度"),
    "负结果显式报告": ("负结果", "反直觉", "劝退", "放弃", "不经济"),
    "降维交付": ("降维", "射表", "列线图", "心算", "口诀", "可用的东西", "设计准则"),
}

def main():
    files = sorted(glob.glob(os.path.join(ROOT, "_知识提炼", "卡片", "*.json")))
    if not files:
        print("no cards found")
        return
    for f in files:
        c = json.load(open(f, encoding="utf-8"))
        blob = json.dumps({k: c.get(k) for k in ("core_idea", "models", "numerics", "gold_secret", "reusable", "pitfalls")},
                          ensure_ascii=False)
        tags = [t for t, ws in KEYS.items() if any(w in blob for w in ws)]
        c["pwd_tags"] = tags
        with open(f, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(c, fh, ensure_ascii=False, indent=1)
    tally = {}
    for f in files:
        c = json.load(open(f, encoding="utf-8"))
        for t in c.get("pwd_tags", []):
            tally[t] = tally.get(t, 0) + 1
    print("tagged cards:", len(files))
    for t, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {t}: {n}")

if __name__ == "__main__":
    main()
