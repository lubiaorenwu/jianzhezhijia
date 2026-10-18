#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""建设者之家 · 账务系统 v2 本地服务

作用：让电脑和手机在同一 WiFi 下共用同一份 v2 账务数据。
- 打开 http://电脑IP:8081  即可使用（手机浏览器同样地址）
- 数据保存在本文件同目录的 data-v2.json，**不上传任何地方**
- 网页会自动探测本服务：探测到就共用数据，探测不到就退回浏览器本地存储

用法：双击 启动账务服务-v2.cmd，或  python 账务服务-v2.py
"""
import json
import os
import socket
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, 'data-v2.json')
PAGE = os.path.join(HERE, '账务系统-v2.html')
PORT = int(os.environ.get('PORT', '8081'))
LOCK = threading.Lock()


def lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return '127.0.0.1'


def read_data():
    if not os.path.exists(DATA):
        return {}
    try:
        with open(DATA, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def write_data(obj):
    tmp = DATA + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, DATA)          # 原子替换，断电也不易写坏
    try:
        import time
        snap_dir = os.path.join(HERE, '备份')
        os.makedirs(snap_dir, exist_ok=True)
        day = time.strftime('%Y%m%d')
        with open(os.path.join(snap_dir, 'data-v2-%s.json' % day), 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False)
        snaps = sorted(x for x in os.listdir(snap_dir) if x.startswith('data-v2-'))
        for old in snaps[:-14]:
            os.remove(os.path.join(snap_dir, old))
    except Exception:
        pass


class H(BaseHTTPRequestHandler):
    def _send(self, code, body=b'', ctype='application/json; charset=utf-8'):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split('?', 1)[0]
        if path.startswith('/api/data'):
            with LOCK:
                body = json.dumps(read_data(), ensure_ascii=False).encode('utf-8')
            return self._send(200, body)
        if path in ('/', '/index.html', '/账务系统-v2.html'):
            if not os.path.exists(PAGE):
                return self._send(404, b'page not found', 'text/plain; charset=utf-8')
            with open(PAGE, 'rb') as f:
                return self._send(200, f.read(), 'text/html; charset=utf-8')
        if path.lower().endswith('.jpg'):
            fp = os.path.join(HERE, os.path.basename(path))
            if os.path.exists(fp):
                with open(fp, 'rb') as f:
                    return self._send(200, f.read(), 'image/jpeg')
        return self._send(404, b'{}')

    def do_POST(self):
        path = self.path.split('?', 1)[0]
        if path.startswith('/api/data'):
            n = int(self.headers.get('Content-Length') or 0)
            raw = self.rfile.read(n) if n else b'{}'
            try:
                obj = json.loads(raw.decode('utf-8'))
            except Exception:
                return self._send(400, b'{"ok":false}')
            with LOCK:
                write_data(obj)
            return self._send(200, b'{"ok":true}')
        return self._send(404, b'{}')

    def log_message(self, *a):
        pass


def main():
    if not os.path.exists(PAGE):
        print('!! 没找到 账务系统-v2.html，请把它和本文件放在同一个文件夹')
        input('按回车退出…')
        return
    ip = lan_ip()
    print('=' * 48)
    print('  建设者之家 · 账务系统 v2 已启动')
    print('=' * 48)
    print('  本机打开：http://127.0.0.1:%d' % PORT)
    print('  手机打开：http://%s:%d   （手机要连同一个 WiFi）' % (ip, PORT))
    print('  数据文件：%s' % DATA)
    print('  关闭这个窗口即停止服务（数据不丢）')
    print('=' * 48)
    try:
        webbrowser.open('http://127.0.0.1:%d' % PORT)
    except Exception:
        pass
    srv = ThreadingHTTPServer(('0.0.0.0', PORT), H)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\n已停止。')


if __name__ == '__main__':
    main()
