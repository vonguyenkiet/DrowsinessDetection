# 🚘 Hệ Thống Giám Sát và Cảnh Báo Lái Xe An Toàn (Driver Monitoring System - DMS)

Dự án phát hiện trạng thái buồn ngủ (Drowsiness) và mất tập trung (Distraction) của tài xế theo thời gian thực sử dụng Computer Vision. Được nâng cấp với giao diện **Desktop Application (Tkinter)** chuyên nghiệp và **Hệ thống tự học ngưỡng (Threshold Tuning)**.

## 🌟 Điểm Nổi Bật (Tính Khoa Học & Kỹ Thuật)
Dự án được thiết kế chuẩn mực như một phần mềm công nghiệp thu nhỏ:
- **Kiến trúc Đa Luồng (Multi-threading):** Tách biệt I/O (Camera, Âm thanh, UI) và AI (MediaPipe) thành 4 luồng song song, sử dụng `queue.Queue` với chiến lược *"Drop old, keep new"* nhằm triệt tiêu độ trễ (latency <= 2 giây), tối ưu FPS.
- **Giao diện Desktop (Tkinter + Pillow):** Bảng điều khiển sinh trắc học trực quan hiển thị thông số EAR, MAR, Head Pose và FPS theo thời gian thực. Hỗ trợ "Hot-Swap" đổi nguồn Video/Webcam mà không cần khởi động lại.
- **MediaPipe FaceMesh (One-Stage Detector):** Trích xuất 468 điểm landmarks với tốc độ cực cao trên CPU, thay vì dùng các mô hình Two-Stage nặng nề.
- **Tính toán Sinh trắc học & Hình học:** 
  - **EAR (Eye Aspect Ratio):** Nhận diện hành vi nhắm mắt/ngủ gật.
  - **MAR (Mouth Aspect Ratio):** Nhận diện hành vi ngáp (được nâng cấp lên 8 điểm mốc để chống nhiễu).
  - **Head Pose Estimation:** Tính toán góc quay của đầu (Pitch, Yaw, Roll) để phát hiện mất tập trung. Đã xử lý triệt để lỗi lật trục tọa độ (Gimbal Lock).
- **Tự động tinh chỉnh ngưỡng (Data-Driven Tuning):** Cung cấp công cụ tự động phân tích hàng ngàn video để tìm ra bộ ngưỡng sinh trắc học cá nhân hóa cho từng tài xế (Threshold Tuning) bằng phương pháp thống kê (Phân vị thứ 10).
- **Xử lý thiếu sáng (CLAHE):** Tự động áp dụng cân bằng Histogram trên không gian màu LAB khi phát hiện môi trường ánh sáng yếu.

## 📂 Cấu Trúc Thư Mục Chi Tiết
```text
DrowsinessDetection/
├── assets/
│   └── sounds/
│       └── alarm.wav             # File âm thanh chuông báo động
├── data/
│   ├── raw_videos/               # Dữ liệu video thô 5s (dành cho huấn luyện/đánh giá)
│   └── merged_videos/            # Dữ liệu video đã ghép 15s siêu tốc
├── src/
│   ├── config/
│   │   └── settings.py           # Quản lý tập trung các hằng số và ngưỡng sinh trắc (EAR, MAR, Pose)
│   ├── threads/
│   │   ├── camera_thread.py      # Luồng I/O (Đọc ảnh liên tục từ Webcam/Video file)
│   │   ├── ai_thread.py          # Luồng CPU (Chạy MediaPipe FaceMesh & Logic nhận diện)
│   │   └── alert_thread.py       # Luồng I/O (Chờ tín hiệu để phát âm thanh chuông báo)
│   ├── ui/
│   │   └── main_window.py        # Mã nguồn giao diện Desktop App bằng Tkinter & Pillow
│   └── utils/
│       ├── geometry.py           # Chứa thuật toán khoảng cách Euclidean tính EAR và MAR
│       ├── pose.py               # Thuật toán solvePnP và giải mã Euler tính góc xoay đầu
│       ├── preprocessing.py      # Xử lý thiếu sáng ban đêm (thuật toán CLAHE)
│       ├── merge_videos.py       # Script hỗ trợ hợp nhất video dùng FFmpeg Stream-copy
│       └── threshold_tuning.py   # Script tự động học và phân tích ngưỡng từ dữ liệu video
├── threshold_features15s.csv     # Bảng dữ liệu thô (được xuất ra sau khi chạy Tuning)
├── requirements.txt              # Danh sách toàn bộ thư viện Python (Dependencies)
├── README.md                     # File hướng dẫn sử dụng (Tài liệu dự án)
└── main.py                       # File khởi chạy ứng dụng DMS (Entry Point)
```

## ⚙️ Cài Đặt (Installation)

**Yêu cầu:** Khuyến nghị sử dụng **Miniconda** hoặc **Anaconda** (Python 3.8 - 3.11).

1. **Clone dự án về máy:**
```bash
git clone https://github.com/vonguyenkiet/DrowsinessDetection.git
cd DrowsinessDetection
```

2. **Cài đặt thư viện:**
Mở Terminal/Command Prompt và chạy lệnh sau để tự động cài đặt toàn bộ thư viện:
```bash
pip install -r requirements.txt
```
*Các thư viện chính bao gồm: `opencv-python` (Xử lý ảnh), `mediapipe` (AI Landmarks), `pygame` (Âm thanh), `Pillow` (Giao diện Tkinter), `numpy`, `moviepy` & `tqdm` (Cắt ghép video).*

## 🚀 Hướng Dẫn Sử Dụng

### 1. Khởi chạy Ứng dụng Giám sát (DMS App)
```bash
python main.py
```
- Giao diện Control Panel sẽ hiện lên.
- Bạn có thể nhấn nút **"Mở Camera Mặc Định"** để test trực tiếp bằng Webcam.
- Hoặc nhấn **"Tải Video Test"** để chọn một file `.mp4` test độ chính xác.
- Khi nhắm mắt lâu, ngáp, hoặc nhìn lệch hướng, bảng trạng thái sẽ nhấp nháy ĐỎ và chuông báo động sẽ vang lên.

### 2. Các Công Cụ Tiện Ích (Utilities)
- **Ghép video siêu tốc (15s):** Gom các video 5s thành 15s để làm dữ liệu kiểm thử.
  ```bash
  python -m src.utils.merge_videos
  ```
- **Tự học và Tinh chỉnh Ngưỡng (Threshold Tuning):** Phân tích hàng ngàn video để tìm ra ngưỡng EAR, MAR tối ưu và tự động cập nhật vào `settings.py`. Đồng thời xuất dữ liệu thô ra file CSV.
  ```bash
  python -m src.utils.threshold_tuning
  ```

## 📝 Dành Cho Đồ Án Sinh Viên
Dự án được tối ưu rất sâu về mặt học thuật. Toàn bộ mã nguồn đã được gắn các **khối Docstring giải thích lý thuyết chi tiết** (Lý do chọn kiến trúc One-Stage, giải pháp Gimbal Lock, tính chất Scale Invariance của EAR/MAR, MLOps configuration...). Bạn hoàn toàn có thể trích xuất các bình luận này để đưa vào Báo cáo Đồ án / Luận văn để lấy điểm cao về phần Thiết kế Hệ Thống.
