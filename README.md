# Lovable Project Downloader Web UI 🚀

Công cụ hỗ trợ tải toàn bộ mã nguồn dự án từ [Lovable.dev](https://lovable.dev) về máy cục bộ với giao diện Web (Web UI) trực quan, hiện đại và tốc độ tải cực nhanh.

---

## 📌 Các bước chuẩn bị trước khi sử dụng

### 1. Đăng nhập vào Lovable trên trình duyệt (Quan trọng)
*   Trước tiên, bạn **phải mở trình duyệt Chrome (hoặc trình duyệt bạn thường dùng) và đăng nhập sẵn** vào tài khoản Lovable của mình.
*   Mở một dự án bất kỳ trên Lovable (ví dụ trang Code Editor của dự án bạn muốn tải).
*   Công cụ này hoạt động bằng cách gọi API của Lovable sử dụng Token của phiên đăng nhập hiện tại trên trình duyệt.

### 2. Yêu cầu hệ thống local
*   Đã cài đặt **Python 3.10+**
*   (Khuyên dùng) Đã cài đặt **`uv`** (Trình quản lý gói Python siêu nhanh của astral-sh) để khởi chạy không cần cài đặt tay các thư viện.

---

## 🛠️ Hướng dẫn cài đặt và sử dụng

### Bước 1: Khởi động Web Server cục bộ
Mở Terminal tại thư mục này và chạy lệnh:
```bash
python web_server.py
```
*Hệ thống sẽ chạy một HTTP Server nội bộ tại cổng `8088`.*

Sau đó, mở trình duyệt và truy cập:
👉 **[http://localhost:8088](http://localhost:8088)**

---

### Bước 2: Lấy mã Token xác thực từ Lovable (Firebase Auth)
Do Lovable sử dụng Firebase Auth để bảo mật, token được lưu trữ mã hóa trong cơ sở dữ liệu IndexedDB của trình duyệt. 

Để lấy token tự động:
1.  Truy cập vào trang dự án Lovable của bạn trên trình duyệt.
2.  Nhấn **F12** (hoặc chuột phải -> **Inspect**) và chuyển sang tab **Console**.
3.  Sao chép và dán đoạn mã JavaScript dưới đây vào rồi nhấn **Enter**:

```javascript
(async function() {
  const jwtRegex = /\beyJhbGciOi[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\b/g;
  let tokens = [];
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    const val = localStorage.getItem(key);
    if (val && typeof val === 'string') {
      const matches = val.match(jwtRegex);
      if (matches) tokens.push(...matches);
    }
  }
  for (let i = 0; i < sessionStorage.length; i++) {
    const key = sessionStorage.key(i);
    const val = sessionStorage.getItem(key);
    if (val && typeof val === 'string') {
      const matches = val.match(jwtRegex);
      if (matches) tokens.push(...matches);
    }
  }
  const cookieMatches = document.cookie.match(jwtRegex);
  if (cookieMatches) tokens.push(...cookieMatches);
  if (window.indexedDB && window.indexedDB.databases) {
    try {
      const dbs = await window.indexedDB.databases();
      for (const dbInfo of dbs) {
        if (!dbInfo.name) continue;
        await new Promise((resolve) => {
          const openRequest = window.indexedDB.open(dbInfo.name);
          openRequest.onsuccess = async (event) => {
            const db = event.target.result;
            const objectStoreNames = Array.from(db.objectStoreNames);
            for (const storeName of objectStoreNames) {
              await new Promise((resStore) => {
                try {
                  const transaction = db.transaction(storeName, "readonly");
                  const store = transaction.objectStore(storeName);
                  const getAllRequest = store.getAll();
                  getAllRequest.onsuccess = () => {
                    const items = getAllRequest.result;
                    for (const item of items) {
                      const strItem = JSON.stringify(item);
                      const matches = strItem.match(jwtRegex);
                      if (matches) tokens.push(...matches);
                    }
                    resStore();
                  };
                  getAllRequest.onerror = () => resStore();
                } catch (e) {
                  resStore();
                }
              });
            }
            db.close();
            resolve();
          };
          openRequest.onerror = () => resolve();
        });
      }
    } catch (e) {}
  }
  tokens = [...new Set(tokens)];
  if (tokens.length > 0) {
    console.log("%c=== ĐÃ TÌM THẤY BEARER TOKEN ===", "color: #00ff00; font-weight: bold; font-size: 14px;");
    console.log(tokens[0]);
    copy(tokens[0]);
    console.log("%cĐã tự động COPY token vào Clipboard của bạn!", "color: #e0a0ff; font-style: italic;");
  } else {
    console.log("%cKhông tìm thấy token dạng JWT nào. Hãy tải lại trang hoặc kiểm tra tab Network.", "color: #ff0000; font-weight: bold;");
  }
})();
```

4.  Đoạn mã trên sẽ tìm ra mã JWT và **tự động sao chép (copy)** vào Clipboard của bạn.

---

### Bước 3: Lưu Token và tải dự án về máy
1.  Quay lại trang giao diện Web UI cục bộ (`http://localhost:8088`).
2.  Dán Token vừa được copy vào ô **Mã Lovable Bearer Token** và bấm **Lưu Cấu Hình Token** (Token sẽ được lưu trữ an toàn trong file `.env` cục bộ trên máy bạn, bạn chỉ cần làm bước này một lần).
3.  Dán link dự án Lovable (ví dụ: `https://lovable.dev/projects/37b864eb-2058-48b7-bea4-e3f71532aa7d?view=codeEditor`) vào ô **Link Dự Án Lovable (URL)**.
4.  Bấm nút **Bắt Đầu Tải Về Máy** và theo dõi danh sách các file được tải xuống theo thời gian thực (real-time) tại khung log Terminal phía dưới.

Toàn bộ dự án sẽ được tự động tạo và lưu trữ đầy đủ trong thư mục `projects/<uuid_của_dự_án>`.

---

## 📂 Cấu trúc thư mục công cụ
```text
ToolDownload/
├── src/
│   ├── api.py          # Xử lý gọi API tải code
│   ├── builder.py      # Tái tạo thư mục và ghi file local
│   ├── config.py       # Quản lý cấu hình dự án
│   ├── core.py         # Quản lý phiên kết nối HTTP client
│   └── model.py        # Định nghĩa kiểu dữ liệu JSON trả về
├── projects/           # Thư mục chứa các dự án đã tải về
├── web_server.py       # HTTP server chạy nền và API backend
├── index.html          # Giao diện điều khiển Web UI
├── .env                # Lưu trữ Token đăng nhập
├── pyproject.toml      # Khai báo các thư viện yêu cầu
└── README.md           # Hướng dẫn sử dụng
```