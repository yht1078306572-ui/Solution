# -*- coding: utf-8 -*-
"""自动生成相机部署示意图（俯视图 + 立面图）"""
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle, Wedge

from engine import CAMERAS

_BUNDLED_FONT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "fonts", "NotoSansCJKsc-Regular.otf")
_FONTS = []
if os.path.exists(_BUNDLED_FONT):
    font_manager.fontManager.addfont(_BUNDLED_FONT)
    _FONTS.append("Noto Sans CJK SC")
_FONTS += ["Microsoft YaHei", "SimHei", "Noto Sans CJK SC",
           "WenQuanYi Zen Hei", "Arial Unicode MS", "sans-serif"]
plt.rcParams["font.sans-serif"] = _FONTS
plt.rcParams["axes.unicode_minus"] = False

C_FIELD = "#eaf3fb"
C_EDGE = "#2f6db3"
C_CAM = "#d63031"
C_CAM2 = "#0984e3"
C_CONE = "#7fb3e0"
C_CONE2 = "#a3d9c9"
C_TEXT = "#1a1a1a"


def _assign_list(cfg):
    """统一返回 [(x, y, z, model), ...]，兼容旧格式"""
    if cfg.get("cam_assign"):
        return cfg["cam_assign"]
    return [(x, y, z, cfg["cam"]) for (x, y, z) in cfg["layout"]["positions"]]


def _model_color(cfg, model):
    return C_CAM if model == cfg["cam"] else C_CAM2


def _model_cone(cfg, model):
    return C_CONE if model == cfg["cam"] else C_CONE2


def _legend(ax, cfg, x, y):
    if not cfg.get("cam2"):
        return
    for i, (m, n) in enumerate(cfg["cam_counts"].items()):
        ax.plot(x, y - i * 0.06 * cfg["W"], "o", color=_model_color(cfg, m), ms=7,
                mec="white", mew=1.2, zorder=6)
        ax.text(x + 0.03 * cfg["L"], y - i * 0.06 * cfg["W"], f"{m} × {n}",
                fontsize=9, color=C_TEXT, va="center", zorder=6)


def draw_top_view(cfg, path):
    L, W, H = cfg["L"], cfg["W"], cfg["H"]
    cam = CAMERAS[cfg["cam"]]
    layout = cfg["layout"]
    fig, ax = plt.subplots(figsize=(9, 6.4), dpi=160)
    ax.add_patch(Rectangle((0, 0), L, W, facecolor=C_FIELD, edgecolor=C_EDGE, lw=2))

    cx, cy = L / 2, W / 2
    for i, (x, y, z, model) in enumerate(_assign_list(cfg), 1):
        fov_h = CAMERAS[model]["fov"][0]
        ang = math.degrees(math.atan2(cy - y, cx - x))
        half = fov_h / 2
        r = min(L, W) * 0.55
        ax.add_patch(Wedge((x, y), r, ang - half, ang + half,
                           facecolor=_model_cone(cfg, model), alpha=0.20, edgecolor="none"))
        ax.plot(x, y, "o", color=_model_color(cfg, model), ms=7, mec="white", mew=1.2, zorder=5)
        ax.annotate(str(i), (x, y), textcoords="offset points", xytext=(6, 6),
                    fontsize=7.5, color=C_TEXT, zorder=6)
    _legend(ax, cfg, L * 1.02, W * 0.98)

    ax.annotate("", xy=(L, -0.06 * W), xytext=(0, -0.06 * W),
                arrowprops=dict(arrowstyle="<->", color=C_TEXT, lw=1))
    ax.text(L / 2, -0.10 * W, f"长 {L:g} m", ha="center", va="top", fontsize=10, color=C_TEXT)
    ax.annotate("", xy=(-0.06 * L, W), xytext=(-0.06 * L, 0),
                arrowprops=dict(arrowstyle="<->", color=C_TEXT, lw=1))
    ax.text(-0.09 * L, W / 2, f"宽 {W:g} m", ha="right", va="center", fontsize=10,
            color=C_TEXT, rotation=90)

    n = layout["n_total"]
    layer_desc = "；".join(f"{l['label']} {l['count']} 台（{l['height']:g}m）" for l in layout["layers"])
    if cfg.get("cam2"):
        cam_desc = " + ".join(f"{m}×{c}" for m, c in cfg["cam_counts"].items())
    else:
        cam_desc = f"{cfg['cam']} × {n}"
    ax.set_title(f"相机部署俯视图（估算）——{cam_desc} 台\n{layer_desc}",
                 fontsize=12, color=C_TEXT, pad=12)
    ax.set_xlim(-0.15 * L, 1.22 * L)
    ax.set_ylim(-0.16 * W, 1.08 * W)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def draw_side_view(cfg, path):
    L, W, H = cfg["L"], cfg["W"], cfg["H"]
    cam = CAMERAS[cfg["cam"]]
    layout = cfg["layout"]
    fig, ax = plt.subplots(figsize=(9, 5.2), dpi=160)
    ax.add_patch(Rectangle((0, 0), L, H, facecolor=C_FIELD, edgecolor=C_EDGE, lw=2))
    ax.plot([0, L], [0, 0], color="#666666", lw=2.5)

    vhalf = cam["fov"][1] / 2
    # 立面上沿 x 轴均匀抽样展示相机（去重、按 x 排序，最多 7 个）
    uniq = sorted({(round(p[0], 2), round(p[2], 2)) for p in layout["positions"]})
    if len(uniq) > 7:
        step = (len(uniq) - 1) / 6
        uniq = [uniq[round(i * step)] for i in range(6)] + [uniq[-1]]
        uniq = sorted(set(uniq))
    for x, zh in uniq:
        if layout["layout_type"] == "grid":
            ang, half, r = -90, min(vhalf, 26), zh * 1.18
        else:
            ang = math.degrees(math.atan2(0 - zh, L / 2 - x))
            half, r = vhalf, zh * 1.25
        ax.add_patch(Wedge((x, zh), r, ang - half, ang + half,
                           facecolor=C_CONE, alpha=0.20, edgecolor="none"))
        ax.plot(x, zh, "s", color=C_CAM, ms=7, mec="white", mew=1.2, zorder=5)
    for layer in layout["layers"]:
        ax.text(L * 1.01, layer["height"], f"{layer['label']}（{layer['height']:g}m）",
                fontsize=9, color=C_TEXT, va="center")

    ax.annotate("", xy=(L * 1.06, H), xytext=(L * 1.06, 0),
                arrowprops=dict(arrowstyle="<->", color=C_TEXT, lw=1))
    ax.text(L * 1.08, H / 2, f"高 {H:g} m", fontsize=10, color=C_TEXT, va="center", rotation=90)
    ax.annotate("", xy=(L, -0.05 * H), xytext=(0, -0.05 * H),
                arrowprops=dict(arrowstyle="<->", color=C_TEXT, lw=1))
    ax.text(L / 2, -0.11 * H, f"长 {L:g} m", ha="center", va="top", fontsize=10, color=C_TEXT)

    ax.set_title(f"相机部署立面图（估算）——视场角 {cam['fov'][0]}°×{cam['fov'][1]}°",
                 fontsize=12, color=C_TEXT, pad=12)
    ax.set_xlim(-0.08 * L, 1.30 * L)
    ax.set_ylim(-0.18 * H, 1.15 * H)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------- 原理示意图
def draw_principle(path):
    """双目三角测量原理示意图"""
    fig, ax = plt.subplots(figsize=(9, 5.0), dpi=160)
    c1, c2 = (1.2, 1.0), (5.8, 1.0)   # 两相机位置
    mk = (3.5, 4.2)                    # Marker 空间点
    # 视场锥
    for (cx, cy), a1, a2 in ((c1, 38, 82), (c2, 98, 142)):
        ax.add_patch(Wedge((cx, cy), 3.6, a1, a2, facecolor=C_CONE, alpha=0.18,
                           edgecolor="none"))
    # 基线
    ax.annotate("", xy=c2, xytext=c1,
                arrowprops=dict(arrowstyle="<->", color=C_TEXT, lw=1.4))
    ax.text((c1[0] + c2[0]) / 2, c1[1] - 0.28, "基线 Baseline", ha="center",
            va="top", fontsize=10, color=C_TEXT)
    # 射线
    for c in (c1, c2):
        ax.plot([c[0], mk[0]], [c[1], mk[1]], ls="--", color=C_CAM, lw=1.4)
    # 相机图标
    for i, c in enumerate((c1, c2), 1):
        ax.add_patch(Rectangle((c[0] - 0.22, c[1] - 0.22), 0.44, 0.44,
                               facecolor=C_CAM, edgecolor="white", lw=1.5, zorder=5))
        ax.text(c[0], c[1] - 0.5, f"相机 {i}", ha="center", va="top",
                fontsize=10, color=C_TEXT)
        ax.text(c[0], c[1] + 0.42, f"(x{i}, y{i}, z{i})", ha="center", va="bottom",
                fontsize=9, color="#555555")
    # Marker
    ax.plot(*mk, "o", color="#e6a23c", ms=13, mec="white", mew=1.5, zorder=6)
    ax.text(mk[0] + 0.15, mk[1] + 0.12, "Marker（X, Y, Z）", fontsize=11,
            color=C_TEXT, va="bottom")
    ax.text(3.5, 5.0, "同一时刻两台及以上相机捕获同一 Marker → 三角测量解算三维坐标",
            ha="center", fontsize=10.5, color="#2f6db3")
    ax.set_xlim(0, 7)
    ax.set_ylim(0.4, 5.4)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


# ---------------------------------------------------------------- 流程图工具
def _flow(ax, steps, colors=None, y=0.5, box_w=None, fontsize=10):
    """横向流程图：steps=[(标题, 副标题)]"""
    n = len(steps)
    gap = 0.035
    bw = box_w or (1.0 - gap * (n + 1)) / n
    for i, (title, sub) in enumerate(steps):
        x = gap + i * (bw + gap)
        fc = colors[i] if colors else "#eef4fb"
        ax.add_patch(Rectangle((x, y - 0.16), bw, 0.32, facecolor=fc,
                               edgecolor=C_EDGE, lw=1.4, zorder=3,
                               transform=ax.transAxes))
        ax.text(x + bw / 2, y + (0.045 if sub else 0), title, ha="center", va="center",
                fontsize=fontsize, color=C_TEXT, weight="bold", transform=ax.transAxes,
                zorder=4)
        if sub:
            ax.text(x + bw / 2, y - 0.075, sub, ha="center", va="center",
                    fontsize=fontsize - 1.6, color="#4a5a6a", transform=ax.transAxes,
                    zorder=4)
        if i < n - 1:
            ax.annotate("", xy=(x + bw + gap * 0.92, y), xytext=(x + bw + gap * 0.08, y),
                        xycoords=ax.transAxes, textcoords=ax.transAxes,
                        arrowprops=dict(arrowstyle="-|>", color=C_EDGE, lw=1.6))


def draw_dataflow(cfg, path):
    """数据传输链路图：相机 → 交换机 → 服务器 → 上位机/第三方"""
    fig, ax = plt.subplots(figsize=(9, 2.9), dpi=160)
    software = cfg.get("software") or "CMAvatar"
    steps = [
        (f"红外相机阵列 ×{cfg['layout']['n_total']}", "POE 数电同传"),
        ("POE 交换机", "CAT-6 局域网"),
        ("动捕服务器", f"{software} 实时解算"),
        ("甲方上位机 / 第三方", "TCP/IP · SDK · 协议输出"),
    ]
    _flow(ax, steps, colors=["#fdecec", "#eef4fb", "#eef4fb", "#e9f7ef"])
    ax.text(0.5, 0.08, "支持 VRPN / TrackD / DTrack / PSN / FreeD / MQTT / ROS 等协议，"
                       "数据格式 FBX / BVH / C3D / CSV",
            ha="center", fontsize=9, color="#4a5a6a", transform=ax.transAxes)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def draw_workflow(path):
    """实施部署流程图"""
    fig, ax = plt.subplots(figsize=(9, 2.6), dpi=160)
    steps = [
        ("场地勘测", "尺寸/遮挡/光照"),
        ("安装架设", "桁架/支架/布线"),
        ("系统校准", "T-Wand + L-Wand"),
        ("标记点部署", "刚体创建"),
        ("试采集验证", "精度/延时核验"),
        ("正式运行", "采集/转发/分析"),
    ]
    _flow(ax, steps, fontsize=9.5)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def draw_steps_flow(steps, path, fontsize=9.5, figsize=(9, 2.6)):
    """通用横向流程图：steps=[(标题, 副标题)]"""
    fig, ax = plt.subplots(figsize=figsize, dpi=160)
    _flow(ax, steps, fontsize=fontsize)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
