# -*- coding: utf-8 -*-
"""青瞳方案生成引擎：相机库 + 场景模板 + 布局/选型/BOM 规则
所有数字均由规则计算，不臆造。规则来源于青瞳内部方案文档的部署经验值。
"""
import math
import re

# ---------------------------------------------------------------- 相机库
# dist_p/dist_a: 最远被动/主动追踪距离(m)；fov: (水平, 垂直)度；acc: 典型3D精度
CAMERAS = {
    "MC1000": dict(res="1280×1024（130万像素）", fps=120, fov=(90, 76), dist_p=10, dist_a=20,
                   acc="±0.12mm", delay="8.3ms", power="5-9W", leds=10,
                   use="院校CAVE虚拟仿真、小型动画制作", tag="高性价比"),
    "MC1300": dict(res="1280×1024（130万像素）", fps=210, fov=(90, 70), dist_p=15, dist_a=30,
                   acc="±0.08-0.12mm", delay="4.8ms", power="5.5-18W", leds=20,
                   use="专业动画制作、虚拟偶像直播、高精度测量、大空间VR", tag="应用广泛"),
    "MC2000": dict(res="2048×1088（220万像素）", fps=380, fov=(89, 49), dist_p=20, dist_a=40,
                   acc="±0.1mm", delay="2.6ms", power="6-18W", leds=20,
                   use="生命工程、运动分析、XR/虚拟拍摄", tag="高速运动"),
    "MC3000": dict(res="1936×1464（280万像素）", fps=400, fov=(82, 67), dist_p=25, dist_a=50,
                   acc="±0.08mm", delay="2.5ms", power="13-24W", leds=20,
                   use="无人机定位、体育运动分析、人机互动研究（高速运动+室外增强）", tag="高速运动/室外增强"),
    "MC4000": dict(res="2048×2048（410万像素）", fps=180, fov=(53, 53), dist_p=30, dist_a=60,
                   acc="±0.06mm", delay="5.5ms", power="6-18W", leds=20,
                   use="科研工业自动化、1000㎡超大空间", tag="超大空间"),
    "MC4000W": dict(res="2048×2048（410万像素）", fps=180, fov=(89, 89), dist_p=20, dist_a=40,
                    acc="±0.1mm", delay="5.5ms", power="6-18W", leds=20,
                    use="1000㎡+场地、XR、科研工业自动化、生命工程", tag="全域无死角"),
    "K5": dict(res="2640×2160（530万像素）", fps=360, fov=(63, 51), dist_p=28, dist_a=56,
               acc="±0.06mm", delay="2.7ms", power="12-55W", leds=60,
               use="影视动画、XR虚拍、运动分析、康复、定位测量", tag="高端"),
    "K9": dict(res="4256×2160（860万像素）", fps=360, fov=(73, 40), dist_p=30, dist_a=60,
               acc="±0.04mm", delay="2.7ms", power="12-55W", leds=60,
               use="影视动画、高精度精准测量、工业机器人定位、运动分析", tag="高端"),
    "K18": dict(res="4512×4096（1800万像素）", fps=172, fov=(49, 45), dist_p=30, dist_a=60,
                acc="±0.03mm", delay="5.8ms", power="12-55W", leds=60,
                use="影视动画、大空间VR、大空间无人机定位", tag="高端旗舰"),
    "K26": dict(res="5120×5120（2600万像素）", fps=180, fov=(58, 58), dist_p=32, dist_a=64,
                acc="±0.02mm", delay="5.6ms", power="12-55W", leds=24,
                use="大型影视动画、大空间VR、细微物体运动捕捉", tag="高端旗舰"),
    "R3": dict(res="2048×1544（320万像素）", fps=216, fov=(63, 49), dist_p=10, dist_a=10,
               acc="AI无标记/有标记双模式", delay="2.5ms", power="12-36W", leds=48,
               use="AI无标记动捕、影像参考、运动分析、康复评估（可外接麦克风、双RJ45级联）",
               tag="AI无标记/参考"),
    "U4": dict(res="2048×2048（410万像素）", fps=180, fov=(49, 49), dist_p=10, dist_a=10,
               acc="±0.06mm", delay="5.5ms", power="4-16W", leds=24,
               use="水下机器人测试、水动力实验、水下运动分析（450nm蓝光，IP68/100m防水，另有69°×69°镜头可选）",
               tag="水下IP68"),
}

K_SERIES = {"K5", "K9", "K18", "K26"}

# ---------------------------------------------------------------- 同步机型号库
# 选型规则（CMLOCK 系列选型说明 V1.0）：Genlock/Timecode/VESA、多路同步、机架集中 → CMLOCK；
# 单路主动光同步、补光灯/开关量联动、轻量低成本 → CMLOCK mini；外接补光灯只能选 mini。
SYNC_MODELS = {
    "CMLOCK": dict(io="通用同步 6 入 6 出", genlock="1 入 1 出", timecode="1 入 1 出",
                   vesa="1 入 1 出", gpio="无", wireless="1 路无线同步口",
                   power="RJ45 / PoE+，另支持 DC 12V/0.8A", display="LCD 状态显示屏",
                   size="482.6×200×45mm（1U 机架式）",
                   use="Genlock/Timecode/VESA 专业协议、多路同步汇聚、机架集中部署与复杂系统"),
    "CMLOCK mini": dict(io="通用同步 1 入 1 出", genlock="无", timecode="无", vesa="无",
                        gpio="开关量 1 入 1 出（支持补光灯同步控制）", wireless="1 路无线同步口",
                        power="RJ45 / PoE", display="无",
                        size="120×126×46.2mm（紧凑型）",
                        use="单路主动光同步、补光灯/开关量联动、轻量分散部署与成本敏感项目"),
}

# 场景默认同步机：虚拍 Genlock/影视 Timecode 工作流/复杂定制 → CMLOCK；其余单路通用同步即可 → mini
SCENE_SYNC_DEFAULT = {"xr": "CMLOCK", "human": "CMLOCK", "custom": "CMLOCK"}

# ---------------------------------------------------------------- 交换机型号库
# 选型规则：K 系列相机（PoE++ 供电，单台约 60W）必须选用 PoE++（IEEE 802.3bt）交换机；
# 其余系列 PoE+ 即可。口数与整机功率双重校核，单台不足时多台分区接入。
SWITCHES = [
    dict(model="TL-SG1005P", brand="TP-Link", ports=5, watts=57, grade="PoE+", note=""),
    dict(model="S1205V-PWR", brand="H3C", ports=4, watts=60, grade="PoE+", note=""),
    dict(model="TL-SG2210PE", brand="TP-Link", ports=8, watts=120, grade="PoE+", note=""),
    dict(model="S1208V-HPWR", brand="H3C", ports=8, watts=125, grade="PoE+", note=""),
    dict(model="KP-9000-45-2GX8GP", brand="KeepLink", ports=8, watts=245, grade="PoE+", note="工业级"),
    dict(model="TL-SG2218PE", brand="TP-Link", ports=16, watts=225, grade="PoE+", note=""),
    dict(model="MS4016P-HPWR-EI", brand="H3C", ports=16, watts=225, grade="PoE+", note=""),
    dict(model="KP-9000-65-2GX16GP", brand="KeepLink", ports=16, watts=386, grade="PoE+", note="工业级"),
    dict(model="TL-SG2226PE", brand="TP-Link", ports=24, watts=375, grade="PoE+", note=""),
    dict(model="S1226F-HPWR", brand="H3C", ports=24, watts=370, grade="PoE+", note=""),
    dict(model="KP-9000-65-4GX24GP", brand="KeepLink", ports=24, watts=386, grade="PoE+", note="工业级"),
    dict(model="TL-SG1005PB", brand="TP-Link", ports=5, watts=242, grade="PoE++",
         note="单口 90W，可带 4 台 K26"),
    dict(model="TL-SE2420PB", brand="TP-Link", ports=16, watts=498, grade="PoE++",
         note="单口 90W，可带 8 台 K26"),
]

# 工业场景（机器人/定制）PoE+ 时优先工业级机型
INDUSTRIAL_SCENES = {"robot", "custom"}


def _cam_watts(model):
    """相机功耗上限（W）；K 系列按 PoE++ 60W 计"""
    if model in K_SERIES:
        return 60
    nums = [int(x) for x in re.findall(r"\d+", CAMERAS[model]["power"])]
    return max(nums) if nums else 25


def select_switch(counts, n_ref, sync_model, scene_key):
    """按口数+功率+供电等级选交换机，返回 (机型, 数量, 追加说明)。
    口数需求 = 相机数 + 参考相机 + 服务器 + 同步机；功率需求按各相机功耗上限累加。"""
    ports_req = sum(counts.values()) + n_ref + 1 + (1 if sync_model else 0)
    watts_req = sum(_cam_watts(m) * n for m, n in counts.items())
    watts_req += n_ref * _cam_watts("R3")
    if sync_model:
        watts_req += 15 if sync_model == "CMLOCK" else 10
    need_pp = any(m in K_SERIES for m in counts)
    grade = "PoE++" if need_pp else "PoE+"
    pool = sorted((s for s in SWITCHES if s["grade"] == grade),
                  key=lambda s: (s["ports"], s["watts"]))
    if scene_key in INDUSTRIAL_SCENES and not need_pp:
        pool = ([s for s in pool if s["note"] == "工业级"]
                + [s for s in pool if s["note"] != "工业级"])
    for s in pool:                                   # 单台可满足：取最小档
        if s["ports"] >= ports_req and s["watts"] >= watts_req:
            return s, 1, ""
    biggest = max(pool, key=lambda s: (s["ports"], s["watts"]))
    n_sw = max(math.ceil(ports_req / biggest["ports"]),
               math.ceil(watts_req / biggest["watts"]))
    return biggest, n_sw, "单台口数/功率不足，按分区接入多台"

# 标记点类型 → 是否纯主动（距离校核口径：纯主动按 dist_a；被动/主被动混用按 dist_p 从严）
MARKER_TYPES = {
    "passive": "被动反光标记点",
    "active": "主动光标记体",
    "hybrid": "主被动混用",
}


def marker_is_active(marker_type):
    """纯主动标记才允许按主动识别距离校核；主被动混用须覆盖被动点，按被动距离从严"""
    return marker_type == "active"

# ---------------------------------------------------------------- 设备扩展规格（详细产品资料）
EXT_SPECS = {
    "_mc": dict(focus="12mm（另有广角可选）", aperture="F1.8 最大光圈",
                install="100m", cpu="双核 ARM A9，1GB DDR3，4GB eMMC",
                indicator="多色 LED 灯圈（工作状态可视）", ip="IP44",
                cert="RoHS / CE / FCC / VCCI",
                features=["全局快门 CMOS，850nm 红外补光，强度可调",
                          "一根 RJ45 网线完成 PoE 供电、数据传输与同步，即插即用",
                          "支持 100+ 台大规模级联与有线/无线同步",
                          "高低温、震动、潮湿环境经专业机构检测认证，性能可靠"]),
    "_k": dict(focus="12mm", aperture="F1.8 最大光圈",
               install="100m", cpu="高性能嵌入式处理器",
               indicator="多色 LED 灯圈（工作状态可视）", ip="IP44",
               cert="RoHS / CE / FCC / VCCI",
               features=["旗舰级高分辨率传感器，单台覆盖能力约为 MC 系列数倍",
                         "60 颗高能近红外 LED（850nm），强度可调，远距回波稳定",
                         "PoE++ 供电（IEEE802.3bt），单台功耗约 60W",
                         "支持主动视觉定位与多相机有线/无线同步"]),
    "R3": dict(focus="6mm", aperture="F2.0", install="50m",
               cpu="AI 边缘计算处理器", indicator="多色 LED 状态灯", ip="IP44",
               cert="RoHS / CE / FCC",
               features=["AI 无标记/有标记双模式，可外接麦克风",
                         "双 RJ45 级联，影像与光学数据同步采集",
                         "支持影像映射与重投影校验，辅助 AI 算法训练"]),
    "U4": dict(focus="12.5mm", aperture="F1.4 大光圈", install="水下 30m",
               cpu="嵌入式处理器", indicator="多色 LED 状态灯", ip="IP68（100m 防水）",
               cert="RoHS / CE / FCC",
               features=["450nm 蓝光专用光源，24 颗蓝光补光 LED，水下散射条件下成像对比度高",
                         "抗水压、防渗漏、防结露设计，最大可 100 台级联",
                         "PoE+ 供电与千兆网口，特制防水电缆（供电数据一体）",
                         "尺寸 120×120×161mm，快装底座，便于水下支架安装"]),
}


def ext_spec(model):
    """按型号返回扩展规格（MC/K 系列走平台通用值）"""
    if model in EXT_SPECS:
        return EXT_SPECS[model]
    if model in K_SERIES:
        return EXT_SPECS["_k"]
    return EXT_SPECS["_mc"]


# ---------------------------------------------------------------- 布局结果
class Layout(dict):
    """layout 结果：n_total, layers[ {label,count,height,desc} ], positions[(x,y,z)], notes[], spacing"""


# ---------------------------------------------------------------- 场景规则
def layout_robot(L, W, H, cam, opts):
    """机器人定位：顶部环绕 + 可选低位补盲层（机械臂/移动机器人近地作业）"""
    perim = 2 * (L + W)
    n_top = max(8, math.ceil(perim / 6))
    layers = [dict(label="顶部环绕层", count=n_top, height=H,
                   desc=f"沿场地顶部 {H}m 桁架环绕均布，间距约 {perim / n_top:.1f}m，朝向场地中心")]
    positions = _ring_positions(L, W, H, n_top)
    notes = []
    if opts.get("low_layer") and H >= 2.5:
        n_low = 4
        layers.append(dict(label="低位补盲层", count=n_low, height=1.2,
                           desc="场地四角 1.2m 高度部署，补盲机器人末端近地作业区域"))
        positions += _ring_positions(L * 0.8, W * 0.8, 1.2, n_low)
        notes.append("低位层用于覆盖末端执行器近地运动，避免顶部相机俯角过大造成的遮挡")
    n_total = sum(l["count"] for l in layers)
    return Layout(n_total=n_total, layers=layers, positions=positions,
                  notes=notes, spacing=perim / n_top, layout_type="ring")


def layout_drone(L, W, H, cam, opts):
    """无人机大空间：顶部网格均布（间距5-10m经验值，默认8m），超大场地分区矩阵"""
    s = 8.0
    nx = max(2, math.ceil(L / s) + 1)
    ny = max(2, math.ceil(W / s) + 1)
    n_total = nx * ny
    install_h = max(4, H - 2)
    positions = [(L * i / (nx - 1), W * j / (ny - 1), install_h)
                 for j in range(ny) for i in range(nx)]
    sL = L / (nx - 1) if nx > 1 else L
    sW = W / (ny - 1) if ny > 1 else W
    layers = [dict(label="顶部网格阵列", count=n_total, height=install_h,
                   desc=f"{nx}×{ny} 网格均布于 {install_h}m 高度桁架，实际间距约 {sL:.1f}m×{sW:.1f}m，俯角约 42°")]
    notes = ["相机间距按 5-10m 经验值取 8m，兼顾经济性与覆盖冗余",
             f"安装高度预留 2m 飞行冗余（场地净高 {H}m → 安装 {install_h}m）"]
    # 距离冗余校验（按标记体类型取识别距离）
    c = CAMERAS[cam]
    active = opts.get("active_marker", True)
    key = dist_key(active)
    rng = c[key]
    required = required_range(L, W, H)
    if required > rng:
        notes.append(f"⚠ 场地最远工作距离约 {required:.1f}m，已超出 {cam} "
                     f"{'主动' if active else '被动'}追踪上限 {rng}m，"
                     "必须升级型号或改用主动光标记体/分区部署")
    elif required > 0.85 * rng:
        notes.append(f"⚠ 场地最远工作距离约 {required:.1f}m，接近 {cam} "
                     f"{'主动' if active else '被动'}追踪上限 {rng}m，余量不足，建议升档或分区部署")
    else:
        notes.append(f"场地最远工作距离约 {required:.1f}m，{cam} "
                     f"{'主动' if active else '被动'}追踪 {rng}m，冗余充足")
    if L * W > 400:
        n_zone = math.ceil(L / 25) * math.ceil(W / 20)
        notes.append(f"场地面积 {L * W:.0f}㎡ 较大，建议划分为约 {n_zone} 个捕捉矩阵分区，各区独立校准、可单独运行也可联动捕捉")
    return Layout(n_total=n_total, layers=layers, positions=positions,
                  notes=notes, spacing=(sL + sW) / 2, layout_type="grid")


def layout_human(L, W, H, cam, opts):
    """人体/影视动捕：顶部密排环绕（约2m间距），最少8台"""
    perim = 2 * (L + W)
    n = max(8, math.ceil(perim / 2))
    layers = [dict(label="顶部环绕阵列", count=n, height=H,
                   desc=f"沿场地 {H}m 高度桁架环绕均布，间距约 {perim / n:.1f}m，指向场地中心")]
    notes = ["人体为复杂柔性目标，遮挡频繁，高密度环绕部署保证任意姿态下 ≥3 台相机可见"]
    if opts.get("persons", 1) > 1:
        notes.append(f"同时捕捉 {opts['persons']} 人，建议每人按 60 个标记点配置并预留解算余量")
    positions = _ring_positions(L, W, H, n)
    return Layout(n_total=n, layers=layers, positions=positions,
                  notes=notes, spacing=perim / n, layout_type="ring")


def layout_embodied(L, W, H, cam, opts):
    """具身智能数采：高密度环绕（≥12台）+ R3 参考相机"""
    perim = 2 * (L + W)
    n = max(12, math.ceil(perim / 2))
    layers = [dict(label="顶部环绕阵列", count=n, height=H,
                   desc=f"沿场地 {H}m 高度桁架环绕均布，间距约 {perim / n:.1f}m，高密度覆盖手指级精细动作")]
    notes = ["灵巧手/手指动作目标小、自遮挡严重，单阵列相机数不少于 12 台（人形/人体级捕捉经验值）",
             "配套 R3 AI 参考相机，用于影像映射、重投影校验与 AI 无标记辅助"]
    positions = _ring_positions(L, W, H, n)
    return Layout(n_total=n, layers=layers, positions=positions,
                  notes=notes, spacing=perim / n, layout_type="ring", extra_cam=dict(model="R3", count=1))


def layout_vr(L, W, H, cam, opts):
    """VR大空间：顶部环绕（约4.5m间距，最少8台），大面积自动加密"""
    perim = 2 * (L + W)
    area = L * W
    spacing = 4.5 if area <= 200 else 4.0
    n = max(8, math.ceil(perim / spacing))
    layers = [dict(label="顶部环绕阵列", count=n, height=H,
                   desc=f"沿场地 {H}m 高度桁架环绕均布，间距约 {perim / n:.1f}m，头显/手柄/道具全区域覆盖")]
    notes = ["红外光学覆盖方案可按场地灵活配置，标准场地与异形场地均可覆盖，支持几十到几百平米；"
             "上千平米需求建议分区部署"]
    persons = opts.get("persons", 1)
    if persons > 1:
        notes.append(f"同场 {persons} 人交互，系统支持多人同场（单套可扩展至百人同场），"
                     "各角色依靠刚体 ID 与全身算法区分")
    if H < 3:
        notes.append("⚠ 训练场地房高最低点建议不低于 3m，当前场地高度偏低，请注意顶部相机安装方式")
    positions = _ring_positions(L, W, H, n)
    return Layout(n_total=n, layers=layers, positions=positions,
                  notes=notes, spacing=perim / n, layout_type="ring")


def layout_xr(L, W, H, cam, opts):
    """XR/VP 虚拍：LED 顶部弧形组 + LED 两侧补盲 + 外围灯架补位"""
    n_top = 2 * max(3, math.ceil(L / 4))       # 每组 2 台
    n_side = 4
    n_aux = max(2, math.ceil((L + W) / 12))
    positions = []
    for i in range(n_top):                     # LED 屏顶部弧形（长边上沿）
        positions.append((L * (i + 0.5) / n_top, W * 0.98, H))
    for i in range(n_side):                    # LED 两侧边缘
        x = 0.02 * L if i < 2 else 0.98 * L
        positions.append((x, W * (0.3 + 0.4 * (i % 2)), H * 0.6))
    for i in range(n_aux):                     # 外围灯架补位（场地后侧）
        positions.append((L * (i + 0.5) / n_aux, W * 0.05, 2.5))
    layers = [
        dict(label="LED 顶部弧形阵列", count=n_top, height=H,
             desc=f"沿 LED 屏顶部弧形结构布置 {n_top // 2} 组×2 台，覆盖屏前核心拍摄区域"),
        dict(label="LED 侧向补盲组", count=n_side, height=round(H * 0.6, 1),
             desc="LED 屏两侧边缘各 2 台，减少边缘遮挡盲区"),
        dict(label="外围灵活补位（灯架/三脚架）", count=n_aux, height=2.5,
             desc="场地外围灯架部署，可按机位调度灵活调整，增强大范围冗余"),
    ]
    notes = ["三类相机协同形成多层次观测网络，经统一时间同步与空间标定建立同一三维坐标体系",
             "LED 尺寸：建议按场地长边为屏宽、高 4-6m 弧形设计；相机亦可直接安装于 LED 屏体结构"]
    return Layout(n_total=n_top + n_side + n_aux, layers=layers, positions=positions,
                  notes=notes, spacing=L / max(1, n_top // 2), layout_type="xr")


def layout_underwater(L, W, H, cam, opts):
    """水下动捕：双层环绕（上层近水面俯视 + 中层平视），汉江项目部署范式。
    layout_type=underwater → 不参与 _apply_layers（自带双层结构）"""
    perim = 2 * (L + W)
    n_top = max(8, math.ceil(perim / 4))
    n_mid = max(8, math.ceil(perim / 4))
    z_top = round(H * 0.85, 1)
    z_mid = round(H * 0.45, 1)
    positions = (_ring_positions(L, W, z_top, n_top)
                 + _ring_positions(L * 0.92, W * 0.92, z_mid, n_mid))
    layers = [
        dict(label="上层环绕阵列（近水面）", count=n_top, height=z_top,
             desc=f"沿池壁 {z_top}m 深度环绕均布，间距约 {perim / n_top:.1f}m，"
                  "俯视覆盖中上层水域"),
        dict(label="中层平视阵列", count=n_mid, height=z_mid,
             desc=f"沿池壁 {z_mid}m 深度环绕均布，与上层俯仰角互补，"
                  "覆盖中下层水域与池底区域"),
    ]
    notes = [
        "双层环绕+重点区域补盲：上层俯视、中层平视，保证全水深覆盖（汉江项目部署范式）",
        "相机经特制防水电缆（供电数据一体）接入岸上 UWConnectionUnit 接入盒，严禁普通网线入水",
        "标记点与标定工具均为 450nm 蓝光专用型号；水质要求清澈低浊，池壁宜深色哑光",
    ]
    return Layout(n_total=n_top + n_mid, layers=layers, positions=positions,
                  notes=notes, spacing=perim / n_top, layout_type="underwater")


def _ring_positions(L, W, z, n):
    """矩形四周均匀布点（含四角），返回 n 个 (x,y,z)"""
    perim = 2 * (L + W)
    pts = []
    for i in range(n):
        d = perim * i / n
        for seg_len, fn in ((L, lambda d: (d, 0)),
                            (W, lambda d: (L, d)),
                            (L, lambda d: (L - d, W)),
                            (W, lambda d: (0, W - d))):
            if d <= seg_len:
                x, y = fn(d)
                pts.append((x, y, z))
                break
            d -= seg_len
    return pts


# ---------------------------------------------------------------- 选型-场地距离校核
def required_range(L, W, H):
    """场地对单台相机的最远工作距离要求（m）。
    工程准则：每台相机须稳定覆盖场地中心区域（校准摆动与全场追踪的公共观测区），
    即 角点相机→场地中心 的距离 sqrt((L/2)^2+(W/2)^2+H^2)。
    场地边角目标由就近多台相机接力覆盖，不构成分布式部署的距离瓶颈。"""
    return math.sqrt((L / 2) ** 2 + (W / 2) ** 2 + H ** 2)


def dist_key(active):
    """按标记体类型取识别距离字段：主动光标记体 / 被动反光标记点"""
    return "dist_a" if active else "dist_p"


def recommend_camera(scene_key, L, W, H, active=False):
    """按场地尺寸+标记体类型自动选型：识别距离必须覆盖最远工作距离。
    返回 (型号, 需求距离, 可行型号列表)。规则：
    1) 场景默认型号满足距离要求 → 沿用默认；
    2) 默认不满足 → 升档为满足条件的最经济型号（距离富余最小者）；
    3) 全部不满足 → 取距离最远者（由调用方追加告警）。"""
    scene = SCENES[scene_key]
    d_req = required_range(L, W, H)
    key = dist_key(active)
    feasible = [m for m in scene["cam_choices"] if CAMERAS[m][key] >= d_req]
    if scene["default_cam"] in feasible:
        pick = scene["default_cam"]
    elif feasible:
        pick = min(feasible, key=lambda m: CAMERAS[m][key])
    else:
        pick = max(scene["cam_choices"], key=lambda m: CAMERAS[m][key])
    return pick, d_req, feasible


# ---------------------------------------------------------------- 场景定义
SCENES = {
    "robot": dict(
        name="机器人定位测试方案",
        object_default="移动机器人本体及末端执行器",
        default_cam="MC3000",
        cam_choices=["MC3000", "K18", "MC4000", "K9"],
        software="CMAvatar",
        layout=layout_robot,
        precision={"MC3000": "位置重复精度≤0.1mm，角度精度≤0.1°",
                   "K18": "位置重复精度≤0.04mm，角度精度≤0.1°",
                   "MC4000": "位置重复精度≤0.06mm，角度精度≤0.1°",
                   "K9": "位置重复精度≤0.04mm，角度精度≤0.1°"},
        purpose="红外光学定位系统是一种高精度、低延迟的测量设备，能够实时捕捉和记录机器人在不同工况下的运动数据。通过该系统，能够精准获取机器人在三维空间中的六自由度位姿，不仅可以用于机器人的标定与校准，还可以用于实时监控机器人的运动状态和性能，为机器人的控制算法验证、轨迹精度评估和出厂检测提供可靠的量化数据支撑。",
        markers="对于机器人各关节的捕捉，红外标记点应分段部署在机器人各连杆处，并尽可能接近关节旋转中心，以便旋转中心的标定；对于末端执行器，推荐在末端顶部、正前方及两侧部署小型标记点（3-4 个），以增强对旋转角度的解算能力。标记点可选反光球（精度高、不易丢失）或反光贴（轻小、不破坏器械结构，复杂动作下有丢失可能），可根据机器人尺寸与运动特性灵活选择。",
    ),
    "drone": dict(
        name="无人机定位测试方案",
        object_default="无人机（含集群）",
        default_cam="K26",
        cam_choices=["K26", "K18", "MC3000", "MC4000"],
        software="CMTracker",
        layout=layout_drone,
        precision={"K26": "亚毫米级定位（典型 ±0.02mm），角度精度≤0.1°",
                   "K18": "亚毫米级定位（典型 ±0.03mm），角度精度≤0.1°",
                   "MC3000": "位置重复精度≤0.1mm，角度精度≤0.1°",
                   "MC4000": "位置重复精度≤0.06mm，角度精度≤0.1°"},
        purpose="红外光学动作捕捉系统具有极高的精度和速度，能够在毫秒级周期内捕捉和跟踪无人机的移动，输出亚毫米级的位置数据和六自由度数据，使无人机能够在实验室环境中进行精细的控制调试。系统不依赖 GPS 信号，特别适用于室内环境下无人机的初期研发、导航控制算法验证、集群编队与协同控制研究。",
        markers="无人机推荐部署主动式标记体（自发光红外灯珠、可编码 ID、可集成 IMU 实现光惯融合，适合大空间与多目标场景）；小型无人机也可选用 8-10mm 被动反光球（无需供电、任意角度反射稳定）。标记点应在机身呈不共面分布并保持适当间距，避免识别混叠。",
    ),
    "human": dict(
        name="影视动画动作捕捉系统方案",
        object_default="动捕演员（人体全身动作）",
        default_cam="MC4000",
        cam_choices=["MC4000", "MC1300", "MC4000W", "K18", "R3"],
        software="CMAvatar",
        layout=layout_human,
        precision={"MC4000": "3D 精度 ±0.06mm，支持 53 点全身骨骼解算",
                   "MC1300": "3D 精度 ±0.08-0.12mm，支持 53 点全身骨骼解算",
                   "MC4000W": "3D 精度 ±0.1mm，大视场无死角覆盖",
                   "K18": "3D 精度 ±0.03mm，影视级高精度",
                   "R3": "AI 无标记/有标记双模式，无穿戴采集"},
        purpose="红外光学动作捕捉系统是影视动画、虚拟制作的核心基础设施。系统通过在人体关键部位粘贴高反射标记点，使用多台红外相机实时解算全身骨骼运动，实现真人与虚拟角色的实时互动，广泛应用于动画制作、虚拟偶像直播、游戏 CG、虚拟预演等场景，可显著提升制作效率、缩短制作周期。",
        markers="推荐青瞳标准 53 点贴点方式：被测人体身穿毛面动捕服，在各关节及关节连接处粘贴标准 12mm 反光球；如需手指动作，可升级 61 点（光学手指）模板或搭配 Feeler 惯性数据手套；道具等简单刚体通常部署不少于 5 个标记点。",
    ),
    "embodied": dict(
        name="具身智能数据采集与评测方案",
        object_default="人形机器人/灵巧手（遥操作与数采）",
        default_cam="MC4000",
        cam_choices=["MC4000", "MC4000W", "K9", "MC3000", "R3"],
        software="CMTracker",
        layout=layout_embodied,
        precision={"MC4000": "位置精度≤0.05mm，角度精度≤0.1°，支持桌面级手指追踪（≤1mm）",
                   "MC4000W": "位置精度≤0.05mm，大视场覆盖",
                   "K9": "位置精度≤0.04mm，工业级高分辨率",
                   "MC3000": "位置精度≤0.08mm，400fps 高速",
                   "R3": "AI 无标记/有标记双模式，遥操作影像映射"},
        purpose="面向具身智能的性能评测、灵巧操作、遥操作与训练数据工厂需求，系统提供亚毫米级位姿与轨迹数据采集能力。通过自定义骨骼功能（.cst 骨骼结构模板/.csk 物理参数模板/.csh 贴点位置模板），可将采集数据直接映射至机器人本体骨架，支撑 Sim2Real 骨架对比测试、平衡与跌倒保护评测、灵巧操作识别等关键任务，构建“数据采集-训练验证-反馈优化”的闭环。",
        markers="灵巧手/末端执行器推荐 6-8mm 小型反光球或反光贴，沿指节与掌背不共面布点；人形机器人本体按关节分段布点并配合自定义骨骼模板；遥操作场景可搭配数据手套实现手部高稳定性捕捉，遮挡工况下由 IMU 数据保持轨迹连续。",
    ),
    "vr": dict(
        name="虚拟仿真/VR大空间解决方案",
        object_default="VR 头显、手柄与虚实道具（多人同场）",
        default_cam="MC1000",
        cam_choices=["MC1000", "MC4000W", "MC1300", "K18"],
        software="CMAvatar",
        layout=layout_vr,
        precision={"MC1000": "亚毫米级定位，延迟≤8.5ms，大视场覆盖",
                   "MC4000W": "亚毫米级定位，大视场无死角覆盖",
                   "MC1300": "亚毫米级定位，210fps 高帧率",
                   "K18": "亚毫米级定位（±0.03mm），大空间旗舰"},
        purpose="青瞳模拟训练/VR 大空间系统是基于光学追踪定位技术、VR 技术与网络通讯技术实现的高精度定位与沉浸式虚拟体验于一体的多人互动系统。参训/体验人员穿戴 VR 头显与动作捕捉套件、手持虚实道具，进入可交互的沉浸式虚拟环境，为小队协作、战术模拟、红蓝对抗、仿真培训、VR 电竞与文旅娱乐等场景提供一体化服务。系统支持多人同场交互、虚实道具 1:1 映射与异地多场地互联。",
        markers="头显与手柄贴附反光标记点构成追踪刚体（每设备不少于 3-4 点，构型各异以便区分）；全身追踪可选两种方式：6 个光学传感器的 IK/FK 混合算法，或 40 点全身动捕算法；虚实道具支持灵活定制——砖体表面固定反光点或将光学传感器固定于道具表面，经快速标定后道具在虚拟场景中与实物 1:1 匹配。",
    ),
    "xr": dict(
        name="XR/VP 虚拟拍摄相机定位方案",
        object_default="真实摄影机（含镜头参数）与虚拟拍摄机位",
        default_cam="MC4000",
        cam_choices=["MC4000", "K5", "K18", "MC4000W"],
        software="CMTracker",
        layout=layout_xr,
        precision={"MC4000": "定位精度≤0.05mm，主动追踪 60m（配定位套件达 0.01mm/0.01°）",
                   "K5": "定位精度≤0.04mm，360fps 高帧率",
                   "K18": "定位精度≤0.03mm，影视级大空间",
                   "MC4000W": "定位精度≤0.05mm，大视场覆盖"},
        purpose="随着虚拟制片（VP）、xR 虚拟拍摄技术在影视、广告与数字内容制作领域的普及，制作模式正向“实时渲染、虚实融合、所见即所得”转变。真实摄影机与虚拟场景之间的空间一致性是高质量虚实融合的基础：系统实时、准确地获取摄影机三维位置、姿态与镜头参数，驱动虚拟引擎还原摄影机视角，保证虚拟画面与真实画面在透视、比例和运动上的一致。本方案基于红外光学定位与光惯融合技术，构建统一空间坐标体系与时间同步机制，为 LED 虚拟拍摄棚提供工程化稳定性的相机定位基础设施。",
        markers="摄影机安装主动式光惯融合定位刚体（摄像机定位套件）：内置 9 轴惯性传感器，支持光学-惯性深度融合与陀螺仪平滑权重调节；主动发光、无线同步，30m 范围稳定追踪且可用于室外强光环境；支持 Genlock/Timecode 接入与断电记忆；内置多套镜头编码器与多规格齿轮，实时采集 Zoom/Focus；FreeD 协议输出，烟雾等复杂拍摄环境下稳定工作。刚体安装应牢固并尽量靠近摄影机光芯位置。",
    ),
    "custom": dict(
        name="特殊定制化项目技术方案",
        object_default="实验目标（运动位置与姿态）",
        default_cam="K9",
        cam_choices=["K9", "K18", "K26", "MC4000", "MC3000", "U4"],
        software="CMTracker",
        layout=layout_robot,
        precision={"K9": "位置精度≤0.04mm，角度精度≤0.1°",
                   "K18": "位置精度≤0.03mm，角度精度≤0.1°",
                   "K26": "位置精度≤0.02mm，角度精度≤0.1°",
                   "MC4000": "位置精度≤0.06mm，角度精度≤0.1°",
                   "MC3000": "位置精度≤0.08mm，400fps 高速",
                   "U4": "水下三维精度 ±0.06mm（450nm 蓝光）"},
        purpose="本项目属于特殊定制化测量系统建设。针对甲方实验环境条件复杂、测量指标要求高、"
                "常规标准方案难以直接覆盖的特点，本方案在青瞳红外光学定位技术体系基础上，"
                "围绕项目特定的被测对象、环境条件与约束边界进行针对性设计，形成涵盖需求分析、"
                "难点拆解、技术路径、系统配置、可靠性设计与实施保障的完整技术方案，"
                "确保系统交付后长期稳定运行并满足全部技术指标要求。",
        markers="根据被测目标的几何特征与运动特性定制标记体方案：刚性目标采用不共面、"
                "非对称布点（不少于 5 点）以形成唯一构型；大型或异形目标可分段布点并分别"
                "建立刚体；特殊工况（高速、强振、室外、水下）相应选用主动光标记体或蓝光专用"
                "标记点；标记体安装须保证结构牢固，必要时辅以结构加强或专用夹具。",
    ),
    "underwater": dict(
        name="水下动捕应用解决方案",
        object_default="水下机器人/航行器模型（水动力试验）",
        default_cam="U4",
        cam_choices=["U4"],
        software="CMTracker",
        layout=layout_underwater,
        precision={"U4": "水下三维精度 ±0.06mm（450nm 蓝光，IP68/100m 防水）"},
        purpose="水下光学动作捕捉系统面向水下机器人定位、航行器水动力试验、水下运动分析"
                "等需求，基于 450nm 蓝光窗口与主动/被动标记点，实现水下刚性体六自由度运动"
                "的高精度实时测量。系统不依赖声学、惯性等手段，在试验水池环境中提供"
                "亚毫米级、高帧率的量化数据基准，支撑航行器控制算法验证、水动力特性研究"
                "与模型试验评估，并可与陆上动捕系统联合构建水上-水下一体化测量体系。",
        markers="水下标记点均为 450nm 蓝光专用型号：主动标记体自发光、可编码 ID、IP68 防水、"
                "磁吸充电，可与定位相机光同步，适合大空间与多目标；被动反光标记点免供电、"
                "部署简便。布点遵循不共面、非对称原则，每个刚体不少于 5 点，"
                "并配置一套备份标记点；标记体与标定工具入水前须做密封性检查。",
    ),
}


# ---------------------------------------------------------------- BOM
def compute_bom(cfg):
    """根据配置计算设备清单（不含价格）"""
    scene_key = cfg["scene"]
    scene = SCENES[scene_key]
    layout = cfg["layout"]
    cam = cfg["cam"]
    cam2 = cfg.get("cam2") or ""
    counts = cfg.get("cam_counts", {cam: layout["n_total"]})
    opts = cfg["opts"]
    rows = []
    extra = layout.get("extra_cam")
    n_ref = extra["count"] if extra else 0
    seq = [0]
    u_cams = sum(n for m, n in counts.items() if m.startswith("U"))   # 水下相机数
    n_all = sum(counts.values())                                      # 相机总数

    def add(t, name, qty, unit, note=""):
        seq[0] += 1
        rows.append([seq[0], t, name, qty, unit, note])

    for m, n in counts.items():
        note = "数量按场地规模与部署规则计算"
        if cam2:
            note += f"；与{('、'.join(x for x in counts if x != m))}交错混用" if len(counts) > 1 else ""
        add("光学相机", m, n, "台", note)
    if n_ref:
        add("AI 参考相机", "R3", n_ref, "台", "影像映射/重投影校验/AI 无标记辅助")

    software = cfg.get("software") or scene["software"]
    add("动捕软件", software, 1, "套", "含实时解算、录制、回放与数据接口")
    if u_cams and u_cams < n_all:
        add("校准工具", "水上水下光学动捕校准套件（含蓝光 450nm 专用工具）", 1, "套",
            "陆上/水下相机联合校准与坐标系设定")
    elif u_cams:
        add("校准工具", "水下校准工具套件（蓝光 450nm 专用）", 1, "套",
            "水下相机校准与坐标系设定")
    else:
        add("校准工具", "CMCALIB（T 型校准杆+L 型尺）", 1, "套", "相机校准与坐标系设定")

    # 交换机（口数+功率+供电等级三重校核；K 系列必须 PoE++ 802.3bt）
    sync = 1 if opts.get("sync", True) else 0
    n_cam = layout["n_total"]
    sw, sw_n, sw_extra = select_switch(counts, n_ref, opts.get("sync_model") or "", scene_key)
    sw_note = (f"口数需求=相机{n_cam}+参考相机{n_ref}+服务器1+同步机{sync}，"
               f"功率按相机功耗上限校核（{sw['ports']}口/{sw['watts']}W）")
    if sw["note"]:
        sw_note += f"；{sw['note']}"
    if sw_extra:
        sw_note += f"；{sw_extra}"
    if any(m in K_SERIES for m in counts):
        sw_note += "；K 系列为 PoE++（802.3bt）供电，已按单台 60W 核算"
    add(f"{sw['grade']} 交换机", f"{sw['model']}（{sw['brand']} {sw['ports']} 口 "
        f"{sw['grade']}/{sw['watts']}W）", sw_n, "台", sw_note)

    # 水下相机接入盒（U 系列每台接入盒可接 3 台相机，汉江招标文件规则）
    if u_cams:
        add("水下相机接入盒", "UWConnectionUnit", math.ceil(u_cams / 3), "个",
            "Camera×3/LAN×2/DC×1，RJ45 防水连接器，配套 24V 电源，岸上部署")

    # 服务器
    add("动捕服务器", "定制（i7-14700F/32G 内存/双网卡/RTX4070）", 1, "台",
        "实时解算与数据分发")
    if scene_key == "xr":
        add("渲染与合成服务器", "定制（i9/64G/RTX A 系列专业卡）", 1, "台",
            "虚拟引擎实时渲染与虚实合成，LED 输出")
    elif opts.get("render_server"):
        add("渲染服务器", "定制（i7/32G/RTX4080 级）", 1, "台", "虚拟场景实时渲染")

    # 标记点（按标记点类型：被动/主动/主被动混用）
    mt = opts.get("marker_type", "active" if opts.get("active_marker") else "passive")
    if u_cams:
        # 水下项目：蓝光 450nm 专用标记点（汉江清单规则：约 2 个/相机，含一套备份）
        n_mk = max(20, 2 * u_cams)
        if mt in ("active", "hybrid"):
            add("水下主动标记点", "蓝光 450nm 主动标记体（IP68、磁吸充电、可编码）",
                n_mk, "个", "水下主动光捕捉，含一套备份标记点")
        if mt in ("passive", "hybrid"):
            add("水下反光标记点", "蓝光 450nm 专用反光标记点", n_mk, "个",
                "水下被动捕捉，含一套备份标记点")
        if u_cams < n_all:
            add("反光标记点", "CMMC-MARKER（含 6-12mm 反光球/反光贴）", 60, "个",
                "陆上目标布点，每个刚体至少 5 个")
    elif scene_key == "human":
        persons = max(1, int(opts.get("persons", 1)))
        add("动捕标记点", "CMMARKER-P（12mm 反光球）", 60 * persons, "个",
            f"按每人 60 点配置（53 点贴点方式×{persons} 人）")
        add("动捕服", "CMSUIT", max(2, persons), "套", "莱卡毛面，可反复粘贴")
    elif scene_key == "drone":
        targets = max(1, int(opts.get("targets", 2)))
        if mt in ("active", "hybrid"):
            add("主动光标记体", "CMMC-RBA 系列（含 IMU）", targets, "套",
                "可编码 ID、光惯融合，适合大空间多目标")
        if mt in ("passive", "hybrid"):
            add("反光标记点", "CMMC-MARKER（8-10mm）", 5 * targets, "个",
                "每个刚体至少 5 个反光球" + ("（被动备份）" if mt == "hybrid" else ""))
    elif scene_key == "vr":
        persons = max(1, int(opts.get("persons", 2)))
        add("反光标记点", "CMMC-MARKER（8-12mm 反光球/反光贴）", 16 * persons, "个",
            f"头显+双手柄刚体约 12-16 点/人×{persons} 人，另备损耗")
        add("虚实道具定制", "训练/交互道具（含标定）", 1, "批",
            "按甲方内容需求定制，道具表面固定反光点或光学传感器，1:1 映射")
    elif scene_key == "xr":
        targets = max(1, int(opts.get("targets", 1)))
        add("摄像机定位套件", "主动光惯融合刚体（9 轴 IMU+镜头编码器）", targets, "套",
            "摄影机 6DoF 定位+Zoom/Focus 采集，Genlock/Timecode，FreeD 输出")
        add("镜头标定服务", "镜头文件制作（畸变/FOV 建模）", 1, "项",
            "标定板/LED 屏标定，含镜头编码器齿轮适配")
    else:
        if mt in ("passive", "hybrid"):
            add("反光标记点", "CMMC-MARKER（含 6-12mm 反光球/反光贴）", 60, "个",
                "每个刚体至少 5 个，另备损耗")
        if mt in ("active", "hybrid"):
            targets = max(1, int(opts.get("targets", 2)))
            add("主动光标记体", "CMMC-RBA 系列（含 IMU）", targets, "套",
                "可编码 ID、无线同步，适合大空间/室外/多目标")

    # 选配
    glove_model = opts.get("glove_model") or ""
    if glove_model == "Feeler":
        add("惯性数据手套", "Feeler（光惯融合）", 1, "套", "手指/手部动作捕捉")
    elif glove_model == "Pulse":
        add("数据手套", "Pulse-H 光学-惯性捕捉手套", 1, "套",
            "Pulse 系统含全身捕捉套件与多模态相机，灵巧手精细操作采集")
    if opts.get("face"):
        add("面捕头盔", "Lookme/G2", 1, "台", "面部捕捉")

    if sync:
        sm = opts.get("sync_model") or "CMLOCK"
        smi = SYNC_MODELS.get(sm, SYNC_MODELS["CMLOCK"])
        add("同步机", sm, 1, "台", f"{smi['io']}、{smi['wireless']}；{smi['use']}")

    n_servers = 2 if (opts.get("render_server") or scene_key == "xr") else 1
    if u_cams:
        # 水下项目：水下相机用特制防水电缆（1 根/相机），陆侧数据线按接入盒等统计
        n_boxes = math.ceil(u_cams / 3)
        add("水下相机线缆", "特制防水电缆（供电数据一体）", u_cams, "根",
            "每台水下相机 1 根，池内走线接入岸上水下相机接入盒")
        n_cables = n_boxes + n_ref + n_servers + sync + sw_n + 2
        add("数据线", "CAT-6 六类网线", n_cables, "根",
            f"接入盒{n_boxes}+参考相机{n_ref}+服务器{n_servers}+同步机{sync}+交换机{sw_n}，另备 2 根")
    else:
        n_cables = n_cam + n_ref + n_servers + sync + sw_n + 2
        add("数据线", "CAT-6 六类网线", n_cables, "根",
            f"相机{n_cam}+参考相机{n_ref}+服务器{n_servers}+同步机{sync}+交换机{sw_n}，另备 2 根")
    land_cams = n_cam + n_ref - u_cams
    if land_cams > 0:
        add("安装支架", "云台+大力夹（含快装板）", land_cams, "套", "相机的安装支架")
    if u_cams:
        add("水下固定套件", "水下相机专用固定支架（防腐蚀、角度可调）", u_cams, "套",
            "水下稳固部署，耐水流冲击，池壁/池顶安装")
    return rows


# ---------------------------------------------------------------- 技术要求
def tech_requirements(scene_key, L, W, H, cam, layout):
    scene = SCENES[scene_key]
    prec = scene["precision"].get(cam, list(scene["precision"].values())[0])
    vol = f"{L:g}米×{W:g}米×{H:g}米"
    return [
        f"可测量{scene['object_default']}的精准六自由度运动数据（位置 X/Y/Z + 姿态 Roll/Pitch/Yaw）；",
        "能够实现六自由度数据的实时传输，端到端延迟≤10ms；",
        f"能实现至少{vol}范围内的精准捕捉，捕捉系统{prec}；",
        "通讯接口能够通过 TCP/IP 通讯协议或其他主流通讯协议，与甲方上位机及软件之间进行数据传输通信。",
    ]


def _assign_mixed(positions, cam, cam2, n2):
    """把 n2 个机位均匀交错地分给第二型号，返回 (cam_assign, cam_counts)"""
    n = len(positions)
    n2 = max(1, min(n - 1, int(n2)))
    idx2 = {round(i * (n - 1) / max(1, n2 - 1)) if n2 > 1 else n // 2 for i in range(n2)}
    assign, counts = [], {}
    for i, (x, y, z) in enumerate(positions):
        m = cam2 if i in idx2 else cam
        assign.append((x, y, z, m))
        counts[m] = counts.get(m, 0) + 1
    counts = {cam: counts.get(cam, 0), cam2: counts.get(cam2, 0)}
    return assign, counts


def _manual_layout(scene_key, L, W, H, n_total):
    """手动数量模式：按场景几何形状生成 n_total 个机位的单层布局"""
    if scene_key == "drone":
        install_h = max(4, H - 2)
        nx = max(2, round(math.sqrt(n_total * L / max(W, 1))))
        ny = max(2, math.ceil(n_total / nx))
        positions = [(L * i / (nx - 1), W * j / (ny - 1), install_h)
                     for j in range(ny) for i in range(nx)]
        n_real = len(positions)
        layers = [dict(label="顶部网格阵列（手动数量）", count=n_real, height=install_h,
                       desc=f"{nx}×{ny} 网格均布于 {install_h}m 高度，实际间距约 "
                            f"{L/(nx-1):.1f}m×{W/(ny-1):.1f}m，俯角约 42°")]
        return Layout(n_total=n_real, layers=layers, positions=positions,
                      notes=["相机数量为用户手动指定，机位按网格几何均布"],
                      spacing=(L / (nx - 1) + W / (ny - 1)) / 2, layout_type="grid")
    positions = _ring_positions(L, W, H, n_total)
    layers = [dict(label="顶部环绕阵列（手动数量）", count=n_total, height=H,
                   desc=f"沿场地 {H}m 高度桁架环绕均布，间距约 {2*(L+W)/n_total:.1f}m，"
                        "指向场地中心")]
    return Layout(n_total=n_total, layers=layers, positions=positions,
                  notes=["相机数量为用户手动指定，机位按环绕几何均布"],
                  spacing=2 * (L + W) / n_total, layout_type="ring")


def _apply_layers(layout, n_layers, H):
    """多层立体部署：场地高度 >6m 时垂直方向分层，相机数量按层数成倍增加。
    第 2/3 层与顶层同平面投影，安装于墙面/立柱/中层桁架，俯仰角互补。"""
    if n_layers < 2:
        return layout
    if layout["layout_type"] not in ("ring", "grid"):
        layout["notes"].append("本场景部署以特定结构（如 LED 屏弧形阵列）为主，"
                               "多层布置需求按现场机位专项评估")
        return layout
    base_pos = list(layout["positions"])
    base_n = len(base_pos)
    for li in range(2, n_layers + 1):
        z = round(H * (n_layers - li + 1) / n_layers, 1)
        layout["positions"] += [(x, y, z) for (x, y, _) in base_pos]
        layout["layers"].append(dict(
            label=f"第 {li} 层补充阵列", count=base_n, height=z,
            desc=f"与顶层同平面投影布置于 {z}m 高度（墙面/立柱/中层桁架），"
                 "与上层相机俯仰角互补，消除垂直方向盲区"))
    layout["n_total"] = base_n * n_layers
    layout["notes"].append(
        f"场地高度 {H:g}m，采用 {n_layers} 层立体部署，相机数量按层数成倍增加"
        f"（{base_n}×{n_layers}={layout['n_total']} 台），保证垂直方向覆盖与高位区域观测冗余")
    return layout


# 定制场景：需求描述关键词 → 难点标签自动推断
CUSTOM_TAG_KEYWORDS = [
    ("outdoor", ["室外", "户外", "半室外", "露天"]),
    ("large", ["大空间", "超大", "大面积", "万平米", "千平"]),
    ("highspeed", ["高速", "m/s", "米/秒", "超音速", "风洞"]),
    ("multitarget", ["多目标", "多机", "集群", "多个目标", "编队"]),
    ("irregular", ["异形", "锥形", "弧形", "狭长", "通道", "穹顶", "不规则"]),
    ("temperature", ["高温", "低温", "高低温", "湿热", "温度", "严寒", "酷热"]),
    ("vibration", ["振动", "震动", "冲击", "颠簸"]),
    ("underwater", ["水下", "水池", "水动力", "防水", "潜水"]),
    ("occlusion", ["遮挡", "导轨", "吊装", "立柱", "结构复杂"]),
]


def build_config(form):
    """把表单输入规整为生成配置"""
    scene_key = form["scene"]
    scene = SCENES[scene_key]
    L, W, H = float(form["L"]), float(form["W"]), float(form["H"])

    # 标记点类型（必选）：被动/主动/主被动混用；兼容旧 active_marker 复选框
    marker_type = (form.get("marker_type") or "").strip()
    if marker_type not in MARKER_TYPES:
        marker_type = "active" if bool(form.get("active_marker", False)) else "passive"
    active = marker_is_active(marker_type)          # 纯主动才按主动距离校核
    key = dist_key(active)
    mk_txt = MARKER_TYPES[marker_type]
    rng_txt = "主动" if active else "被动"

    # 同步机：先记录请求，待相机型号确定后解析（水下项目须 CMLOCK——招标要求 Genlock/Timecode/VESA）
    sync_req = (form.get("sync_model") or "auto").strip()

    # 布置层数：0=自动（场地高度>6m 两层），可手动指定 1-3 层
    n_layers = int(form.get("layers") or 0)
    if n_layers <= 0:
        n_layers = 2 if H > 6 else 1
    n_layers = max(1, min(3, n_layers))

    cam = form.get("camera") or scene["default_cam"]
    cam_reason = ""
    if cam == "auto":
        cam, d_req, feasible = recommend_camera(scene_key, L, W, H, active)
        if cam == scene["default_cam"]:
            cam_reason = (f"相机自动选型说明：按场地 {L:g}m×{W:g}m×{H:g}m 计算，单台相机最远工作"
                          f"距离约 {d_req:.1f}m（须稳定覆盖场地中心区域）；结合{mk_txt}路线，"
                          f"{cam} {rng_txt}识别距离 {CAMERAS[cam][key]}m 满足覆盖要求，"
                          "故沿用本场景推荐型号。")
        elif feasible:
            cam_reason = (f"相机自动选型说明：按场地 {L:g}m×{W:g}m×{H:g}m 计算，单台相机最远工作"
                          f"距离约 {d_req:.1f}m，场景默认型号 {scene['default_cam']}（{rng_txt}识别 "
                          f"{CAMERAS[scene['default_cam']][key]}m）识别距离不足，系统自动升档为 "
                          f"{cam}（{rng_txt}识别 {CAMERAS[cam][key]}m），"
                          "该型号为满足距离要求的最经济选型。")
        else:
            cam_reason = (f"⚠ 相机自动选型说明：按场地计算的最远工作距离约 {d_req:.1f}m，已超出"
                          f"本场景全部可选型号的{rng_txt}识别距离上限，暂取识别距离最远的 {cam}"
                          f"（{rng_txt}识别 {CAMERAS[cam][key]}m）；建议改用主动光标记体、"
                          "划分捕捉分区或联系青瞳进行专项评估。")
    cam2 = (form.get("camera2") or "").strip()
    if cam2 == cam:
        cam2 = ""

    # 同步机型号解析：auto 按场景+水下判定；水下项目必须 CMLOCK
    has_u = cam.startswith("U") or (cam2 or "").startswith("U")
    if sync_req in ("none", "不配置"):
        sync, sync_model = False, ""
    elif sync_req == "auto":
        sync = True
        sync_model = ("CMLOCK" if (scene_key in SCENE_SYNC_DEFAULT or has_u)
                      else "CMLOCK mini")
    elif sync_req in SYNC_MODELS:
        sync, sync_model = True, sync_req
        # 手动选择是否触碰硬门槛，由布局确定后的“同步机选型复核”统一判定
    else:
        sync, sync_model = bool(form.get("sync", True)), "CMLOCK"
    if "sync" in form and not form.get("sync") and form.get("sync_model") is None:
        sync, sync_model = False, ""                # 兼容旧复选框未勾选
    cam_mode = (form.get("cam_mode") or "auto").strip()
    cam_n = int(form.get("cam_n") or 0)          # 手动模式主型号数量
    cam2_n = int(form.get("cam2_n") or 0)        # 混用第二型号数量
    note = form.get("note", "").strip()

    # 定制场景：从需求描述自动推断难点标签，与用户勾选合并
    ctags = list(form.get("ctags") or [])
    if scene_key == "custom" and note:
        for tag, kws in CUSTOM_TAG_KEYWORDS:
            if tag not in ctags and any(kw in note for kw in kws):
                ctags.append(tag)

    cfg = dict(
        scene=scene_key,
        client=form.get("client", "").strip() or "某某单位",
        obj=form.get("obj", "").strip() or scene["object_default"],
        L=L, W=W, H=H,
        cam=cam, cam2=cam2, cam_mode=cam_mode,
        cam_reason=cam_reason,
        detail=(form.get("detail") or "standard").strip(),
        software=(form.get("software") or "").strip() or scene["software"],
        note=note,
        opts=dict(
            low_layer=bool(form.get("low_layer")),
            persons=int(form.get("persons") or 1),
            targets=int(form.get("targets") or 2),
            active_marker=active,
            marker_type=marker_type,
            glove_model=(form.get("glove_model") or "").strip(),
            face=bool(form.get("face")),
            render_server=bool(form.get("render_server")),
            sync=sync,
            sync_model=sync_model,
            layers=n_layers,
            ctags=ctags,
        ),
    )

    if cam_mode == "manual" and cam_n > 0:
        # 手动模式：主型号 cam_n 台 + 混用 cam2_n 台，按几何形状均布
        n_total = cam_n + (cam2_n if cam2 else 0)
        layout = _manual_layout(scene_key, cfg["L"], cfg["W"], cfg["H"], n_total)
        _apply_layers(layout, n_layers, H)
        cfg["layout"] = layout
        if cam2 and cam2_n > 0:
            assign, counts = _assign_mixed(layout["positions"], cam, cam2, cam2_n)
            cfg["cam_assign"] = assign
            cfg["cam_counts"] = counts
            layout["notes"].append(
                f"双型号混用部署：{cam}×{counts[cam]} + {cam2}×{counts[cam2]}，"
                "机位交错排布，两类相机视场互补")
        else:
            cfg["cam_assign"] = [(x, y, z, cam) for (x, y, z) in layout["positions"]]
            cfg["cam_counts"] = {cam: layout["n_total"]}
    else:
        # 自动模式：规则引擎计算总量；混用时从总量中拨出 cam2_n 台（默认 40%）
        cfg["cam_mode"] = "auto"
        layout = scene["layout"](cfg["L"], cfg["W"], cfg["H"], cam, cfg["opts"])
        _apply_layers(layout, n_layers, H)
        cfg["layout"] = layout
        n_total = layout["n_total"]
        if cam2:
            if cam2_n <= 0:
                cam2_n = max(1, round(n_total * 0.4))
            cam2_n = max(1, min(n_total - 1, cam2_n))
            assign, counts = _assign_mixed(layout["positions"], cam, cam2, cam2_n)
            cfg["cam_assign"] = assign
            cfg["cam_counts"] = counts
            layout["notes"].append(
                f"双型号混用部署：{cam}×{counts[cam]} + {cam2}×{counts[cam2]}，"
                "机位交错排布，两类相机视场互补")
        else:
            cfg["cam_assign"] = [(x, y, z, cam) for (x, y, z) in layout["positions"]]
            cfg["cam_counts"] = {cam: n_total}

    # 同步机选型复核（CMLOCK 系列选型说明 V1.0）：
    # 硬门槛 Genlock/Timecode/VESA、通用同步超 1 入 1 出或扩容、机架集中 → CMLOCK；
    # 单路主动光同步/开关量/补光灯联动 → CMLOCK mini；水下强制 CMLOCK
    if sync:
        n_dev = cfg["layout"]["n_total"] + (1 if scene_key == "embodied" else 0)
        multi_ch = n_dev > 16                   # 大阵列：多路同步/扩容需求（硬门槛 2）
        need_lock = scene_key in SCENE_SYNC_DEFAULT or has_u or multi_ch
        if scene_key == "xr":
            lock_why = "虚拟拍摄需 Genlock 锁相与 Timecode 时码（硬门槛，不可降配）"
        elif scene_key == "human":
            lock_why = "影视工作流需 Timecode 时码对齐（硬门槛，不可降配）"
        elif scene_key == "custom":
            lock_why = "定制项目多路同步、机架集中部署与状态管理要求"
        elif has_u:
            lock_why = "水下项目要求 Genlock/Timecode/VESA 接口（水下接入盒链路）"
        else:
            lock_why = f"阵列共 {n_dev} 台设备，通用同步超出 1 入 1 出且存在扩容需求"
        if sync_req == "auto":
            if need_lock and sync_model == "CMLOCK mini":
                sync_model = "CMLOCK"
                cfg["opts"]["sync_model"] = "CMLOCK"
            reason = (f"同步机自动选型说明：{lock_why}，故推荐 CMLOCK。"
                      if need_lock else
                      "同步机自动选型说明：本场景为单路通用同步需求，不涉及 Genlock/Timecode/"
                      "VESA 与多路扩容，CMLOCK mini 即可覆盖（含开关量/补光灯联动），"
                      "方案更轻量、成本更优。")
            cfg["cam_reason"] = (cfg["cam_reason"] + " " + reason).strip()
        elif need_lock and sync_model == "CMLOCK mini":
            # 手动选择触碰硬门槛：强制升级并在报告中说明（水下此前已升级，此处兜底）
            cfg["opts"]["sync_model"] = sync_model = "CMLOCK"
            cfg["cam_reason"] = (cfg["cam_reason"] + " ⚠ 同步机选型复核：手动选择的 "
                                 f"CMLOCK mini 不满足本项目同步需求——{lock_why}；"
                                 "依据 CMLOCK 系列选型规则（硬门槛不可降配），"
                                 "本方案已按 CMLOCK 配置。").strip()
        cfg["bom_sync_final"] = sync_model

    # 选型-场地距离校核：任何所选型号识别距离不足即告警（含混用第二型号）
    d_req = required_range(L, W, H)
    warns = []
    for m in dict.fromkeys([cam] + ([cam2] if cam2 else [])):
        rng = CAMERAS[m][key]
        if rng < d_req:
            best, _, feas = recommend_camera(scene_key, L, W, H, active)
            sug = (f"，建议改用 {best}（{rng_txt}识别 {CAMERAS[best][key]}m）"
                   if feas and m != best else "，建议改用主动光标记体或划分捕捉分区")
            warns.append(f"⚠ 选型校核：{m} {rng_txt}识别距离 {rng}m 小于场地最远工作距离 "
                         f"{d_req:.1f}m，场地中心区域无法稳定覆盖{sug}。")
        elif rng < 1.2 * d_req:
            warns.append(f"△ 选型校核：{m} {rng_txt}识别距离 {rng}m 相对场地最远工作距离 "
                         f"{d_req:.1f}m 的余量不足 20%，远距回波稳定性受限，"
                         "建议升档型号或改用主动光标记体。")
    cfg["cam_warns"] = warns
    if warns:
        layout["notes"].extend(warns)

    cfg["bom"] = compute_bom(cfg)
    cfg["tech_reqs"] = tech_requirements(scene_key, cfg["L"], cfg["W"], cfg["H"], cam,
                                         cfg["layout"])
    # 水下检测：任一相机为 U 系列即按水下方案处理
    cfg["underwater"] = any(m.startswith("U") for m in cfg["cam_counts"])
    if cfg["underwater"]:
        cfg["layout"]["notes"].append(
            "水下部署：相机采用专用防腐蚀水下支架固定于池壁/池顶，特制防水电缆经岸上"
            "水下连接盒接入；标记点与标定工具选用蓝光（450nm）专用型号")
    return cfg
