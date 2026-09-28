# CMSolution · 青瞳动捕方案生成器

输入客户信息与场地参数，一键生成完整的光学动捕技术方案（Word）。

## 功能特性

- **8 类场景**：机器人定位、无人机定位、影视动画动捕、具身智能数据采集、虚拟仿真/VR 大空间、XR/VP 虚拟拍摄、特殊定制化项目、水下动捕
- **三档详略**：基础版 / 标准版 / 深度版（章节结构随场景差异化）
- **自动选型**：相机按场地尺寸+标记点类型做识别距离校核并自动升档；数量按部署规则计算，高度 >6m 自动两层
- **交换机选型**：口数+功率+供电等级三重校核（K 系列强制 PoE++ 802.3bt，其余 PoE+，工业场景优先工业级机型）
- **同步机选型**：按场景自动匹配 CMLOCK / CMLOCK mini（水下强制 CMLOCK）
- **水下清单**：U 系列自动配接入盒（3 台/盒）、防水电缆、水下固定套件、蓝光标记点
- **集成产品章**：每场景配“动捕+被测对象”集成产品与应用场景实拍图
- **报告内容**：部署俯视图/立面图、原理图、流程图、设备清单（BOM）、产品配图、附录

## 运行方式

### 桌面版（免环境）

双击 `CMSolution.exe`（需与 `_internal` 文件夹同级，系统需 WebView2 运行时）。

### 源码运行

```bash
pip install -r requirements.txt
python app.py          # 网页版 http://127.0.0.1:5099
python webview_app.py  # 桌面窗口版（pywebview）
```

### 打包 exe

```bash
build_exe.bat   # PyInstaller
```

## 目录结构

```
app.py / webview_app.py   # Flask 入口 / 桌面壳
engine.py                 # 场景/相机库、布局、选型、BOM、交换机/同步机选型
report.py                 # 章节库与 docx 渲染（宋体公文规范、页眉 logo）
diagrams.py               # matplotlib 示意图（原理/流程/数据流）
templates/                # 表单与完成页
assets/                   # 产品与场景图片、logo、图标
test_gen.py               # 端到端冒烟测试（9 用例）
```

## 说明

- 生成的 Word 保存在 `output/`，目录仅保留 docx（中间配图自动清理）
- 使用说明见 `CMSolution使用说明.docx / .pdf`
- 内部工具，清单不含价格
