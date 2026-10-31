# -*- coding: utf-8 -*-
"""
_sync_plugins.py — 把 .agents/skills/ 下的技能正本同步进 plugins/ 打包源
用法：python _工具脚本/_sync_plugins.py
映射：upc-modeling/upc-writing/upc-figures/upc-review → plugins/upc-coach/skills/
      upc-site-check/upc-new-edition/upc-content-style → plugins/upc-archive/skills/
"""
import os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, ".agents", "skills")
MAP = {
    "upc-coach": ["upc-modeling", "upc-writing", "upc-figures", "upc-review"],
    "upc-archive": ["upc-site-check", "upc-new-edition", "upc-content-style"],
}

for plugin, names in MAP.items():
    dst_root = os.path.join(ROOT, "plugins", plugin, "skills")
    os.makedirs(dst_root, exist_ok=True)
    for name in names:
        src = os.path.join(SRC, name)
        dst = os.path.join(dst_root, name)
        if not os.path.isdir(src):
            print("missing source:", src)
            continue
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        print(f"synced {name} -> plugins/{plugin}/skills/{name}")
print("done")
