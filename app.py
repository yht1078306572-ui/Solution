# -*- coding: utf-8 -*-
"""青瞳方案生成器 - 本地网页工具"""
import glob
import os
import subprocess
import uuid

from flask import Flask, redirect, render_template, request, send_from_directory, url_for

from diagrams import draw_side_view, draw_top_view
from engine import CAMERAS, SCENES, build_config
from report import build_docx

import sys

if getattr(sys, "frozen", False):
    # PyInstaller 打包后：可写目录取 exe 所在位置，只读资源取 _MEIPASS
    BASE = os.path.dirname(sys.executable)
    RES = sys._MEIPASS
else:
    BASE = os.path.dirname(os.path.abspath(__file__))
    RES = BASE
OUT = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)

app = Flask(__name__, template_folder=os.path.join(RES, "templates"))


@app.route("/assets/<path:fn>")
def assets(fn):
    """界面静态资源（logo 等），禁用缓存保证图标更新即时生效"""
    return send_from_directory(os.path.join(RES, "assets"), fn, max_age=0)


@app.route("/")
def index():
    return render_template("index.html", scenes=SCENES, cameras=CAMERAS)


@app.route("/generate", methods=["POST"])
def generate():
    form = request.form.to_dict()
    for k in ("low_layer", "face", "render_server"):
        form[k] = (k in request.form)
    # active_marker / sync 已改为 marker_type / sync_model 下拉，由 engine 解析
    form["ctags"] = request.form.getlist("ctag")
    cfg = build_config(form)
    uid = uuid.uuid4().hex[:8]
    top = os.path.join(OUT, f"{uid}_top.png")
    side = os.path.join(OUT, f"{uid}_side.png")
    draw_top_view(cfg, top)
    draw_side_view(cfg, side)
    safe_client = "".join(ch for ch in cfg["client"] if ch not in '\\/:*?"<>|') or "方案"
    safe_scene = "".join(ch for ch in SCENES[cfg["scene"]]["name"]
                         if ch not in '\\/:*?"<>|')            # 场景名含 / 会变目录
    fname = f"{safe_client}-{safe_scene}-{uid}.docx"
    out = os.path.join(OUT, fname)
    build_docx(cfg, top, side, out)
    # 清理中间配图：输出目录只保留 Word 方案文件
    for f in (top, side):
        if os.path.exists(f):
            os.remove(f)
    base = os.path.splitext(fname)[0]
    for f in glob.glob(os.path.join(OUT, f"{base}_*.png")):
        os.remove(f)
    return redirect(url_for("done", fname=fname))


@app.route("/done/<fname>")
def done(fname):
    return render_template("done.html", fname=fname, folder=OUT)


@app.route("/open/<fname>")
def open_file(fname):
    """用系统默认程序（Word/WPS）打开生成的报告"""
    path = os.path.join(OUT, os.path.basename(fname))
    if os.path.exists(path):
        os.startfile(path)
    return redirect(url_for("done", fname=os.path.basename(fname)))


@app.route("/open_folder/<fname>")
def open_folder(fname):
    """在资源管理器中打开输出文件夹并选中该文件"""
    path = os.path.join(OUT, os.path.basename(fname))
    if os.path.exists(path):
        subprocess.run(["explorer", "/select,", os.path.normpath(path)])
    else:
        subprocess.run(["explorer", os.path.normpath(OUT)])
    return redirect(url_for("done", fname=os.path.basename(fname)))


@app.route("/download/<fname>")
def download(fname):
    return send_from_directory(OUT, fname, as_attachment=True)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5099))
    app.run(host="0.0.0.0", port=port, debug=False)
