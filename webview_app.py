# -*- coding: utf-8 -*-
"""CMSolution PC 桌面版：内置 Flask + WebView2 原生窗口"""
import socket
import threading
import time

import webview

from app import app as flask_app


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def main():
    port = _free_port()
    server = threading.Thread(
        target=flask_app.run,
        kwargs=dict(host="127.0.0.1", port=port, threaded=True, debug=False, use_reloader=False),
        daemon=True,
    )
    server.start()
    time.sleep(1.2)
    webview.create_window(
        "CMSolution · 青瞳动捕方案生成器",
        f"http://127.0.0.1:{port}/",
        width=980, height=880, min_size=(860, 700),
    )
    webview.start()


if __name__ == "__main__":
    main()
