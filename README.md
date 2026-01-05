HƯỚNG DẪN CÀI ĐẶT VÀ SỬ DỤNG
HỆ THỐNG AN NINH CĂN HỘ THÔNG MINH (FACE ID + ANTI-SPOOFING)

YÊU CẦU HỆ THỐNG

Hệ điều hành: Windows 10/11 (64-bit).

Camera: Webcam laptop hoặc Webcam rời (kết nối qua USB).

Phần mềm: Không cần cài đặt Python (đã đóng gói thành file .exe).

CẤU TRÚC THƯ MỤC

Thư mục chạy chương trình bao gồm:
/dist
├── SmartSecurity.exe      (File chương trình chính)
├── /data                  (BẮT BUỘC - Chứa cơ sở dữ liệu khuôn mặt)
└── /logs                  (Nơi lưu lịch sử ra vào)

LƯU Ý QUAN TRỌNG: Không được tách rời file .exe ra khỏi thư mục data.

HƯỚNG DẪN SỬ DỤNG

BƯỚC 1: KHỞI ĐỘNG

Chạy file "SmartSecurity.exe".

Đợi khoảng 5-10 giây để hệ thống nạp Model AI.

BƯỚC 2: ĐĂNG KÝ CƯ DÂN MỚI (Dành cho Admin)

Nhấn nút "Thêm Cư Dân" ở menu bên trái.

Nhập mật khẩu quản trị mặc định: admin

Nhập tên cư dân (viết liền không dấu, VD: NguyenVanA).

Nhìn thẳng vào Camera và nhấn OK để chụp ảnh.

BƯỚC 3: HUẤN LUYỆN HỆ THỐNG

Sau khi thêm người mới, nhấn nút "Huấn Luyện AI".

Nhập mật khẩu: admin

Chờ thanh tiến trình chạy đến 100% và thông báo thành công.

BƯỚC 4: KIỂM SOÁT RA VÀO (DEMO)

Người dùng đứng trước Camera.

Hệ thống nhận diện khuôn mặt và yêu cầu thực hiện thử thách "NHÁY MẮT".

Người dùng nháy mắt dứt khoát 1 lần.

Nếu đúng người thật: Hệ thống báo "MỞ CỬA" (Màu xanh).

Nếu dùng ảnh giả mạo: Hệ thống không mở cửa.

XEM LỊCH SỬ

Vào thư mục /logs, mở file .csv theo ngày tương ứng để xem giờ ra vào.

===============================================================
Nhóm thực hiện: [Điền tên nhóm bạn vào đây]
Môn: Computer Vision
