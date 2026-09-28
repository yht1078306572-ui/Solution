# -*- coding: utf-8 -*-
"""端到端冒烟测试：覆盖四场景 + 混用/R3/U4/手套/软件选择"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from diagrams import draw_side_view, draw_top_view
from engine import build_config
from report import build_docx

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUT, exist_ok=True)

CASES = [
    # 1 机器人定位：默认 MC3000 + 低位补盲（基础版）
    dict(scene="robot", client="测试机器人公司", obj="", L=8, W=5, H=3,
         camera="auto", note="需与甲方 ROS 系统对接", low_layer=True, sync=True,
         detail="basic"),
    # 2 无人机：K26 主 + MC3000 混用 10 台（自动总量）
    dict(scene="drone", client="某高校无人机实验室", obj="", L=40, W=20, H=12,
         camera="K26", camera2="MC3000", cam2_n=10, note="", targets=3,
         active_marker=True, sync=True),
    # 3 人体动捕：MC4000+MC4000W 混用 3 台 + Pulse 手套 + 面捕
    dict(scene="human", client="某动画工作室", obj="", L=6, W=5, H=3,
         camera="MC4000", camera2="MC4000W", cam2_n=3, note="", persons=2,
         render_server=True, glove_model="Pulse", face=True, software="CMAvatar", sync=True),
    # 4 具身数采：手动数量模式 14 台 MC4000 + 2 台 K18 混用 + Feeler
    dict(scene="embodied", client="某人形机器人公司", obj="", L=5, W=4, H=3,
         camera="MC4000", camera2="K18", cam_mode="manual", cam_n=14, cam2_n=2,
         note="灵巧手遥操作数采", glove_model="Feeler", software="CMTracker", sync=True),
    # 5 水下参数走机器人骨架：U4 相机（自动数量，触发水下实施章）
    dict(scene="robot", client="某水下机器人研究所", obj="水下机器人（水池环境）",
         L=10, W=6, H=4, camera="U4", note="水下环境，450nm 蓝光",
         low_layer=False, software="CMTracker", sync=True),
    # 6 VR 大空间：MC1000 自动 + 4 人同场
    dict(scene="vr", client="某 VR 文旅乐园", obj="", L=15, W=12, H=4,
         camera="auto", note="红蓝对抗主题，需异地互联", persons=4, sync=True),
    # 7 XR 虚拍：MC4000 + 2 机位
    dict(scene="xr", client="某影视虚拟拍摄棚", obj="", L=20, W=14, H=8,
         camera="auto", note="LED 弧形屏 20m 宽，对接 UE5", targets=2, sync=True),
    # 8 特殊定制：国家级实验室，室外大空间+高速+多目标（深度版）
    dict(scene="custom", client="某国家级重点实验室", obj="高速实验探测器及导轨系统",
         L=60, W=30, H=12, camera="K18", camera2="MC3000", cam2_n=6,
         note="实验场地为半室外环境，探测器最高速度约 80m/s，同场目标 4 个，"
              "含导轨与吊装结构，遮挡风险高；要求全年连续运行，数据接入实验室内网。",
         ctags=["large", "outdoor", "highspeed", "multitarget", "occlusion"],
         software="CMTracker", sync=True, detail="full"),
    # 9 水下应用：U4 自动选型（标准版，双层环绕+水下清单）
    dict(scene="underwater", client="某船舶水动力实验室", obj="", L=15, W=8, H=5,
         camera="auto", note="试验水池，水质清澈", targets=2,
         marker_type="active", detail="standard"),
]

for i, c in enumerate(CASES, 1):
    cfg = build_config(c)
    uid = f"case{i}_{c['scene']}"
    top = os.path.join(OUT, f"{uid}_top.png")
    side = os.path.join(OUT, f"{uid}_side.png")
    draw_top_view(cfg, top)
    draw_side_view(cfg, side)
    out = os.path.join(OUT, f"冒烟测试-{uid}.docx")
    build_docx(cfg, top, side, out)
    n_cam = cfg["layout"]["n_total"]
    n_bom = len(cfg["bom"])
    size = os.path.getsize(out)
    mix = f" 混用{cfg.get('cam2')}" if cfg.get("cam2") else ""
    import docx
    d = docx.Document(out)
    chars = sum(len(p.text) for p in d.paragraphs) + \
        sum(len(c.text) for t in d.tables for r in t.rows for c in r.cells)
    breaks = d.element.xml.count('type="page"')
    print(f"[OK] case{i} {c['scene']:9s} {cfg.get('detail','standard'):8s} "
          f"字符 {chars:6d}, 分页 {breaks:2d}, 图 {len(d.inline_shapes):2d}, "
          f"docx {size/1024:.0f} KB")
print("ALL DONE")
