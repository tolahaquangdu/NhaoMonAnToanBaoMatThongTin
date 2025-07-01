**Ứng Dụng Bảo Mật Tin Nhắn Văn Bản Với TripleDES & RSA**

_Đề tài tập trung vào việc phát triển một hệ thống nhắn tin P2P bảo mật, đảm bảo tính bí mật, toàn vẹn và xác thực thông tin thông qua các thuật toán mã hóa đối xứng và bất đối xứng._


---


### 🌟 **Giới thiệu**  
- **Bí mật tin nhắn:** Nội dung tin nhắn được bảo vệ bằng thuật toán mã hóa đối xứng TripleDES với chế độ CBC.

- **Xác thực danh tính:** Danh tính người gửi và người nhận được xác thực bằng chữ ký số RSA.

- **Toàn vẹn dữ liệu:** Tính toàn vẹn của tin nhắn được kiểm tra bằng hàm băm SHA-256, đảm bảo không bị thay đổi trong quá trình truyền.

- **Ứng dụng:** Xây dựng nền tảng cơ bản cho các ứng dụng chat, hệ thống trao đổi thông tin nội bộ yêu cầu bảo mật cao.

### 🏗️ **Hệ thống**  
#### 📂 **Cấu trúc dự án**  
📦 SecureMessagingSystem
├── 📂 server # Backend trung gian, mô phỏng server ảo Google Cloud
│ ├── server.py # Mã nguồn server chính để trung chuyển dữ liệu và quản lý khóa
├── 📂 client # Client side, nơi diễn ra toàn bộ quá trình mã hóa/giải mã
│ ├── client.py # Mã nguồn ứng dụng chat client
├── run_server.sh # Script chạy server
├── run_client.sh # Script chạy client
├── requirements.txt # Danh sách thư viện Python cần cài đặt


---


### 🛠️ **Công nghệ sử dụng**  
#### 📡 **Phần cứng**  
- **Máy chủ:** Server ảo (VM) trên Google Cloud Free Tier để chạy backend.

- **Thiết bị xử lý:** Máy tính cá nhân để chạy các ứng dụng client (người gửi/người nhận).

#### 🖥️ **Phần mềm**  
- **Python (Socket):** Xây dựng kết nối mạng giữa client và server.

- **Cryptography:** Thư viện Python mạnh mẽ để triển khai các thuật toán mã hóa và băm.

### 🧮 **Thuật toán**
1. **Trao khóa & Ký số (RSA 2048-bit):**

   - Người gửi tạo khóa TripleDES ngẫu nhiên.

   - Mã hóa khóa này bằng khóa công khai RSA của người nhận (sử dụng chế độ OAEP + SHA-256).

   - Ký thông tin xác thực (ID + thời gian) bằng khóa riêng tư RSA của người gửi để xác nhận danh tính.

2. **Mã hóa tin nhắn (TripleDES):**

   - Tạo IV (Initialization Vector) ngẫu nhiên cho mỗi tin nhắn để tăng tính bảo mật.

   - Mã hóa nội dung tin nhắn bằng TripleDES ở chế độ CBC (Cipher Block Chaining).

3. **Kiểm tra toàn vẹn (SHA-256):**

   - Tạo băm SHA-256 của chuỗi (IV || ciphertext) để đảm bảo dữ liệu không bị thay đổi.

   - Ký băm này bằng khóa riêng tư RSA của người gửi để đảm bảo tính xác thực.


---


### 🚀 **Hướng dẫn cài đặt và chạy**
1️⃣ **Cài đặt môi trường:**  

```bash
pip install pycryptodome
```

2️⃣ **Khởi chạy server:**

```bash
python "Nhom4_UngDungChatAnToan\server.py"
```

3️⃣ **Khởi chạy client (Người gửi - NGUYEN):**

```bash
python "Nhom4_UngDungChatAnToan\client.py" NGUYEN
```

4️⃣ **Khởi chạy client (Người nhận - DU):**

```bash
python "Nhom4_UngDungChatAnToan\client.py" DU
```

5️⃣ **Gửi tin nhắn:**

- Tại terminal của NGUYEN, chọn send và nhập DU làm người nhận.

6️⃣ **Nhận tin nhắn:**

- Tại terminal của DU, chọn check để kiểm tra và giải mã tin nhắn.

📖 **Hướng dẫn sử dụng**
1️⃣ **Đăng ký người dùng:**

- Mỗi khi chạy client với một ID mới, khóa công khai sẽ tự động được tạo và đăng ký lên server.

2️⃣ **Trao đổi tin nhắn:**

- Hệ thống hoạt động theo mô hình "kéo" (pull-based), người nhận cần chủ động kiểm tra tin nhắn.

3️⃣ **Cấu hình server:**

- Có thể thay đổi địa chỉ IP và cổng của server trong client.py để kết nối với server ảo thực tế.


---


### 🔧 **Ghi chú**
- **Lưu trữ khóa:** Khóa công khai được lưu tạm thời trong bộ nhớ của server. Để có hệ thống bền vững, cần thay thế bằng cơ sở dữ liệu như Firestore hoặc Redis.

- **Bảo mật:** Khóa riêng tư không bao giờ được rời khỏi thiết bị của người dùng, đảm bảo bí mật tuyệt đối.


---


### 🤝 **Đóng góp nhóm**  

| Họ và Tên                  | Vai trò                                                                                                                                       |  
|----------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|  
| Đỗ Quang Minh              | Phân công dự án, phát triển toàn bộ mã nguồn (client.py, server.py) và triển khai các thuật toán mã hóa, giải mã, ký số.                      |  
| Nguyễn Trọng Đức Nguyên    | Phát triển mã nguồn báo cáo trên Overleaf, chịu trách nhiệm chuyển đổi các kết quả thực nghiệm và phân tích từ code vào tài liệu.             |  
| Hà Quang Dự                | Xây dựng bố cục tổng thể của báo cáo, tìm kiếm và tổng hợp nội dung lý thuyết liên quan đến TripleDES, RSA, SHA-256, và các giao thức bảo mật.|  


---


© 2025 NHÓM 4, XÂY DỰNG ỨNG DỤNG BẢO MẬT TIN NHẮN VĂN BẢN VỚI MÃ HÓA TRIPLEDES VÀ XÁC THỰC RSA, NHẬP MÔN AN TOÀN BẢO MẬT THÔNG TIN, TRƯỜNG ĐẠI HỌC Đại NAM
