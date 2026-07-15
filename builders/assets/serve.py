#!/usr/bin/env python3
"""Serve the atlas locally, cross-platform (Linux/macOS/Windows,
multiuser-safe): binds localhost on an OS-assigned free port and opens
the browser. Requires only the Python standard library."""
import http.server, os, socketserver, threading, webbrowser

os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Handler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

with socketserver.TCPServer(("127.0.0.1", 0), Handler) as httpd:
    url = f"http://127.0.0.1:{httpd.server_address[1]}/personal/"
    print(f"Neoplatonic Atlas: {url}")
    print("(Ctrl-C to stop)")
    threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
