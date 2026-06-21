import http.server
import json
import os
import threading
import asyncio
import traceback
from urllib.parse import urlparse

# Re-use our client classes
from src.api import LovableApi
from src.config import Config, BEARER_TOKEN

PORT = 8088

# Global state to track download status
status_lock = threading.Lock()
download_status = {
    "status": "idle",          # idle, downloading, success, error
    "progress": 0,             # 0 to 100
    "current_file": "",
    "downloaded_files": 0,
    "total_files": 0,
    "error_message": "",
    "logs": []
}

def log_message(msg):
    with status_lock:
        download_status["logs"].append(msg)
        print(f"[LOG] {msg}")

def set_status(status, progress=None, current_file=None, downloaded_files=None, total_files=None, error_message=None):
    with status_lock:
        if status is not None:
            download_status["status"] = status
        if progress is not None:
            download_status["progress"] = progress
        if current_file is not None:
            download_status["current_file"] = current_file
        if downloaded_files is not None:
            download_status["downloaded_files"] = downloaded_files
        if total_files is not None:
            download_status["total_files"] = total_files
        if error_message is not None:
            download_status["error_message"] = error_message

async def download_task(url, force_overwrite):
    try:
        set_status("downloading", progress=0, current_file="Đang khởi tạo...", downloaded_files=0, total_files=0, error_message="")
        log_message("Bắt đầu tiến trình tải xuống dự án...")

        # Load config
        rootpath = os.path.dirname(os.path.abspath(__file__))
        dotenv_path = os.path.join(rootpath, ".env")
        if os.path.exists(dotenv_path):
            import dotenv
            dotenv.load_dotenv(dotenv_path=dotenv_path, override=True)
            log_message("Đã nạp biến môi trường từ file .env")

        if not os.environ.get(BEARER_TOKEN):
            raise RuntimeError("Không tìm thấy BEARER_TOKEN. Vui lòng cập nhật Token trước.")

        config = Config.from_env()
        log_message("Đang kết nối tới API Lovable...")

        async with LovableApi.new(config, lovable_url=url) as api:
            log_message(f"Kết nối thành công. Đang tải thông tin project ID: {api.lovable_uid}...")
            source = await api.fetch_source()
            
            total = len(source.files)
            set_status(None, total_files=total)
            log_message(f"Tải thông tin thành công. Tìm thấy tổng cộng {total} file.")

            basedir = os.path.join(rootpath, "projects")
            if not os.path.exists(basedir):
                os.makedirs(basedir)

            directory_path = os.path.join(basedir, api.lovable_uid)
            if os.path.exists(directory_path) and not force_overwrite:
                raise FileExistsError(
                    f"Thư mục '{api.lovable_uid}' đã tồn tại. Vui lòng bật 'Ghi đè' (Force overwrite) để tải lại."
                )

            if not os.path.exists(directory_path):
                os.makedirs(directory_path)

            for idx, file in enumerate(source.files):
                data = file.get_data()
                if data is None:
                    log_message(f"Bỏ qua file (không có dữ liệu): {file.name}")
                    continue

                file_path = os.path.join(directory_path, file.name)
                dir_name = os.path.dirname(file_path)
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)

                with open(file_path, "wb") as f:
                    f.write(data)

                # Cập nhật tiến độ
                downloaded = idx + 1
                progress = int((downloaded / total) * 100)
                set_status(None, progress=progress, current_file=file.name, downloaded_files=downloaded)
                log_message(f"[{downloaded}/{total}] Đã ghi file: {file.name}")

            log_message(f"Tải thành công toàn bộ {total} file!")
            log_message(f"Đường dẫn lưu trữ: projects/{api.lovable_uid}")
            set_status("success", progress=100, current_file="Hoàn thành!")

    except Exception as e:
        traceback.print_exc()
        err_msg = str(e)
        log_message(f"LỖI: {err_msg}")
        set_status("error", error_message=err_msg)

def run_async_download(url, force_overwrite):
    asyncio.run(download_task(url, force_overwrite))

class ApiHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Mute standard HTTP logging to console to keep console clean for logs
        pass

    def do_GET(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/' or parsed_path.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            
            rootpath = os.path.dirname(os.path.abspath(__file__))
            index_path = os.path.join(rootpath, "index.html")
            if os.path.exists(index_path):
                with open(index_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(b"<h1>HTML file not found!</h1>")
                
        elif parsed_path.path == '/api/config':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            rootpath = os.path.dirname(os.path.abspath(__file__))
            dotenv_path = os.path.join(rootpath, ".env")
            has_token = False
            token_preview = ""
            
            if os.path.exists(dotenv_path):
                import dotenv
                dotenv.load_dotenv(dotenv_path=dotenv_path, override=True)
                token = os.environ.get(BEARER_TOKEN, "")
                if token:
                    has_token = True
                    token_preview = token[:15] + "..." if len(token) > 15 else token
            
            response = {
                "has_token": has_token,
                "token_preview": token_preview
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        elif parsed_path.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            with status_lock:
                # Trả về bản sao trạng thái hiện tại
                response = dict(download_status)
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/config':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            token = data.get("token", "").strip()
            if not token:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Token is required")
                return

            # Thêm tiền tố Bearer nếu chưa có
            if not token.lower().startswith("bearer "):
                token = f"Bearer {token}"

            rootpath = os.path.dirname(os.path.abspath(__file__))
            dotenv_path = os.path.join(rootpath, ".env")
            with open(dotenv_path, "w", encoding="utf-8") as f:
                f.write(f'{BEARER_TOKEN}="{token}"\n')
                
            os.environ[BEARER_TOKEN] = token
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))

        elif parsed_path.path == '/api/download':
            # Kiểm tra trạng thái hiện tại
            with status_lock:
                is_running = download_status["status"] == "downloading"
                
            if is_running:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Another download is already running.")
                return
                
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            url = data.get("url", "").strip()
            force_overwrite = data.get("force", False)
            
            if not url:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"URL is required")
                return
                
            # Khởi tạo lại trạng thái
            with status_lock:
                download_status["status"] = "downloading"
                download_status["progress"] = 0
                download_status["current_file"] = "Đang bắt đầu..."
                download_status["downloaded_files"] = 0
                download_status["total_files"] = 0
                download_status["error_message"] = ""
                download_status["logs"] = []

            # Chạy tác vụ tải xuống trong luồng phụ (Thread) để không chặn HTTP server
            thread = threading.Thread(target=run_async_download, args=(url, force_overwrite))
            thread.daemon = True
            thread.start()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": True}).encode('utf-8'))
            
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == "__main__":
    print(f"Starting server on http://localhost:{PORT}")
    server = http.server.HTTPServer(('localhost', PORT), ApiHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()
