from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        # لاگ‌های اضافی سرور را نادیده بگیر تا شلوغ نشود
        pass

def run_webserver():
    port = int(os.environ.get("PORT", 10000))  # پورتی که Render به ما می‌دهد
    server_address = ('', port)
    httpd = HTTPServer(server_address, SimpleHandler)
    print(f"✅ Web server started on port {port}")
    httpd.serve_forever()

def start_server():
    # سرور را در یک ترد جداگانه اجرا کن تا با ربات تداخل نداشته باشد
    server_thread = threading.Thread(target=run_webserver, daemon=True)
    server_thread.start()
    print("🚀 Keep-alive server is running in background")
