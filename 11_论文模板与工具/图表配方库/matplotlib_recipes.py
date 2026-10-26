# -*- coding: utf-8 -*-
"""
UPC 金牌论文图表配方库 —— 从 73 篇金牌论文中归纳的 8 类核心图
每个配方 = 一个函数，docstring 注明该图型在哪些金牌论文中出现、
评委视角的"为什么这样画"。运行本文件可生成 _recipes_preview.png 预览全部 8 类。

依赖：numpy, matplotlib
"""
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.size": 11, "axes.linewidth": 0.8, "figure.dpi": 110,
    "axes.spines.top": False, "axes.spines.right": False,
})


# ────────────────────────────────────────────────────────────
# 配方 1：轨迹图（三色语义 + 结论进图题 + 等比例）
# 出现于：2010-A-160（海王星气动制动）、2018-A 三篇（光帆）、2025-B 全部（弹道）
# 设计要点：① 颜色语义全文统一 ② 关键数值写进 title ③ aspect='equal'
# ────────────────────────────────────────────────────────────
def recipe_trajectory(ax, title="Trajectory with numbers in title"):
    g, R = 9.8, 1e4                      # 示例：真空抛体 + 行星表面
    th, v0 = np.radians(38), 700
    t = np.linspace(0, 2*v0*np.sin(th)/g, 300)
    x, y = v0*np.cos(th)*t, v0*np.sin(th)*t - .5*g*t**2
    ax.plot(x/1e3, y/1e3, "r--", lw=1.6, label="Trajectory")
    ax.axhline(0, color="royalblue", lw=2, label="Surface")     # 语义色 1
    ax.axhline(60, color="teal", lw=1.2, ls=":", label="Atmosphere")  # 语义色 2
    ax.plot(x[-1]/1e3, 0, "k+", ms=12)
    ax.set(xlabel="x (km)", ylabel="y (km)", aspect="equal",
           title=title)
    ax.set_title(f"v0={v0} m/s, θ=38°\nRange={x[-1]/1e3:.1f} km")  # ← 结论进图题
    ax.legend(fontsize=9, loc="upper right")


# ────────────────────────────────────────────────────────────
# 配方 2：参数扫描网格图（把"哪个区可行"画成一块区域）
# 出现于：2014-A-726（环双星稳定区）、2017-A 三篇（帆参数区）、2022-B（点球可行域）
# 设计要点：不画曲线画"区域"，可行域填色 + 边界线加粗，一眼看出解空间
# ────────────────────────────────────────────────────────────
def recipe_regime_map(ax):
    a = np.linspace(0.1, 0.9, 300)      # 参数1：半长轴比
    e = np.linspace(0, 0.5, 300)        # 参数2：偏心率
    A, E = np.meshgrid(a, e)
    stable = A*(1+E) < 0.55             # 示例判据：希尔稳定条件
    ax.contourf(A, E, stable, levels=[0.5, 1.5], colors=["#cfe3ff"], alpha=.9)
    ax.contour(A, E, stable.astype(float), levels=[0.5], colors="#3b62a8", linewidths=2)
    ax.plot(0.35, 0.12, "r*", ms=14, label="Chosen design")
    ax.set(xlabel="semi-major axis $a/a_{bin}$", ylabel="eccentricity $e$",
           title="Stability regime: shaded = survives 10 orbital periods")
    ax.legend(fontsize=9)


# ────────────────────────────────────────────────────────────
# 配方 3：灵敏度龙卷风图（哪些参数值得care）
# 出现于：2012-A-449、2019-A-289、2025-B-392 —— 所有做参数不确定度的金牌
# 设计要点：按影响排序的横向条形 ±%，红线是结果容差 → 高于红线的参数必须精查
# ────────────────────────────────────────────────────────────
def recipe_tornado(ax):
    params = ["$v_{ex}$", "$C_d$", "atmos. $\\beta$", "mass $m$", "wind"]
    delta  = [18, 12, 9, 4, 2]           # 参数 ±20% 时结果变化 %
    order  = np.argsort(delta)
    ax.barh(np.array(params)[order], np.array(delta)[order],
            color="#6E7BF2", edgecolor="white")
    ax.axvline(10, color="crimson", ls="--", lw=1.2, label="result tolerance")
    ax.set(xlabel="change in final answer (%) for ±20% input",
           title="Sensitivity: only $v_{ex}$ and $C_d$ dominate")
    ax.legend(fontsize=9)


# ────────────────────────────────────────────────────────────
# 配方 4：收敛性双曲线（步长减半法可视化）
# 出现于：2010-A-160（Fig 6）、2020-A 多篇 —— 数值类论文的"诚信图"
# 设计要点：两种步长曲线几乎重合 + 图题报出两次数值 → 收敛自证
# ────────────────────────────────────────────────────────────
def recipe_convergence(ax):
    t = np.linspace(0, 10, 400)
    v1 = 100*np.exp(-t/3) * (1 + 8e-4*np.sin(9*t))     # Δt
    v2 = 100*np.exp(-t/3) * (1 + 4e-4*np.sin(9*t))     # Δt/2
    ax.plot(t, v1, lw=2, label=r"$\Delta t = 10^{-3}$ s")
    ax.plot(t, v2, lw=1.4, ls="--", label=r"$\Delta t = 5\times10^{-4}$ s")
    ax.set(xlabel="time (s)", ylabel="speed (m/s)",
           title=f"step-halving: exit 16876.86 vs 16876.53 m/s (5 sig figs agree)")
    ax.legend(fontsize=9)


# ────────────────────────────────────────────────────────────
# 配方 5：Pareto 前沿（trade study 的标准呈现）
# 出现于：2019-A-343（屏蔽质量 vs 剂量）、2024-B（电源质量 vs 功率）
# 设计要点：可行点灰、前沿点大且连线、最优点星标 + 标注坐标
# ────────────────────────────────────────────────────────────
def recipe_pareto(ax):
    rng = np.random.default_rng(3)
    mass = np.sort(rng.uniform(10, 60, 40))
    dose = 2.2 - 0.02*mass + rng.normal(0, .06, 40)
    front = np.ones_like(mass, bool)
    for i in range(len(mass)):                       # 支配筛选
        front[i] = np.all((dose >= dose[i]) | (mass <= mass[i]))
    ax.scatter(mass, dose, s=18, c="#9aa7bd", label="feasible designs")
    ax.plot(mass[front], dose[front], "-o", color="#6E7BF2", ms=5, lw=1.6, label="Pareto front")
    k = np.argmin(dose + 0.02*mass)
    ax.plot(mass[k], dose[k], "r*", ms=16, label=f"knee: ({mass[k]:.0f} t, {dose[k]:.2f} Sv)")
    ax.set(xlabel="shield mass (t)", ylabel="dose (Sv)", title="Trade study: mass vs dose")
    ax.legend(fontsize=9)


# ────────────────────────────────────────────────────────────
# 配方 6：多子图时间序列（状态量演化）
# 出现于：2018-B 两篇（堆肥温度-氧浓度）、2023-A 多篇（跳伞速度-高度-过载）
# 设计要点：sharex + 各子图单位不同；关键阈值画水平虚线
# ────────────────────────────────────────────────────────────
def recipe_timeseries():
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(6, 4.6), sharex=True,
                                 gridspec_kw={"hspace": .12})
    t = np.linspace(0, 60, 400)
    T = 20 + 55*np.exp(-((t-25)/9)**2)                # 温度峰
    v = 200*np.exp(-t/12)
    a1.plot(t, T, color="#DB7A74"); a1.axhline(60, ls="--", color="crimson", lw=1)
    a1.set(ylabel="core temp (°C)"); a1.text(45, 62, "ignition limit", fontsize=8, color="crimson")
    a2.plot(t, v, color="#5CB3A8"); a2.axhline(76, ls="--", color="crimson", lw=1)
    a2.set(ylabel="O$_2$ (%)", xlabel="time (h)")
    return fig


# ────────────────────────────────────────────────────────────
# 配方 7：射表/修正表热力图（"交付物"类图表）
# 出现于：2025-B-207/392/765（射表）、2022-B-471（策略表）
# 设计要点：行列都是离散档位，单元格填修正量；附 colorbar 与使用说明
# ────────────────────────────────────────────────────────────
def recipe_firing_table(ax):
    rng = np.random.default_rng(0)
    dist = np.arange(1000, 1600, 100)
    wind = np.arange(-10, 11, 5)
    D, W = np.meshgrid(dist, wind)
    corr = 0.9*D/1000 + 1.3*W - 0.02*(D-1200)/100*np.abs(W)
    im = ax.imshow(corr, origin="lower", aspect="auto", cmap="RdBu_r",
                   extent=[dist[0], dist[-1], wind[0], wind[-1]])
    ax.set(xlabel="range (m)", ylabel="headwind (m/s)",
           title="elevation correction (mil) — read row=wind, col=range")
    plt.colorbar(im, ax=ax, shrink=.85, label="Δθ (mil)")


# ────────────────────────────────────────────────────────────
# 配方 8：建模流程示意（论文开头的 "roadmap" 图）
# 出现于：2021-B-385（三过程分解）、2023-A-131、2025-A-112 —— 结构复杂论文的导航图
# 设计要点：圆角框 + 箭头 + 每框一个式号引用；一图讲清模型层级
# ────────────────────────────────────────────────────────────
def recipe_roadmap(ax):
    ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 6)
    box = lambda x, y, w, h, txt, c: (
        ax.add_patch(plt.Rectangle((x, y), w, h, fc=c, ec="#22304c", lw=1.2,
                                   zorder=2, clip_on=False)),
        ax.text(x+w/2, y+h/2, txt, ha="center", va="center", fontsize=8.5, zorder=3))
    box(0.3, 4.2, 2.8, 1.2, "vacuum baseline\nEq.(3)", "#11151D")
    box(3.8, 4.2, 2.8, 1.2, "+ drag $C_d(M)$\nEq.(7)", "#161B24")
    box(7.3, 4.2, 2.4, 1.2, "+ wind field\nEq.(9)", "#1b2233")
    box(3.8, 1.6, 2.8, 1.2, "firing table\ngenerator", "#232d44")
    box(7.3, 1.6, 2.4, 1.2, "officer card\n(deliverable)", "#2c3a5e")
    for x0, y0, x1, y1 in [(3.1, 4.8, 3.8, 4.8), (6.6, 4.8, 7.3, 4.8),
                           (5.2, 4.2, 5.2, 2.8), (6.6, 2.2, 7.3, 2.2)]:
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color="#8b9dff", lw=1.4))
    ax.set_title("Model hierarchy & deliverable flow", fontsize=10)


# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    fig = plt.figure(figsize=(13, 9), facecolor="white")
    recipe_trajectory(fig.add_subplot(3, 3, (1, 4)))
    recipe_regime_map(fig.add_subplot(3, 3, 2))
    recipe_tornado(fig.add_subplot(3, 3, 3))
    recipe_convergence(fig.add_subplot(3, 3, 5))
    recipe_pareto(fig.add_subplot(3, 3, 6))
    recipe_firing_table(fig.add_subplot(3, 3, 7))
    recipe_roadmap(fig.add_subplot(3, 3, 8))
    ts = recipe_timeseries()
    ts.savefig("_recipe6_timeseries.png", dpi=110, bbox_inches="tight")
    plt.close(ts)
    fig.tight_layout()
    fig.savefig("_recipes_preview.png", dpi=110, bbox_inches="tight")
    print("saved _recipes_preview.png + _recipe6_timeseries.png")
