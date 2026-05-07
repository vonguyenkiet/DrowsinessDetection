# 🚘 Hệ Thống Giám Sát và Cảnh Báo Lái Xe An Toàn (Driver Monitoring System - DMS)

Dự án phát hiện trạng thái buồn ngủ (Drowsiness) và mất tập trung (Distraction) của tài xế theo thời gian thực sử dụng Computer Vision.

## 🌟 Điểm Nổi Bật (Tính Khoa Học)
Dự án được thiết kế chuẩn mực như một phần mềm công nghiệp thu nhỏ với kiến trúc **Đa Luồng (Multi-threading)**, giải quyết triệt để nút thắt cổ chai (bottleneck) trong xử lý ảnh thời gian thực:
- **Kiến trúc Producer-Consumer:** Sử dụng `queue.Queue` kết hợp với chiến lược *"Drop old, keep new"* nhằm đảm bảo hệ thống luôn phân tích khung hình mới nhất, duy trì độ trễ phản hồi (latency) rất thấp.
- **MediaPipe FaceMesh (One-Stage Detector):** Áp dụng kiến trúc One-Stage siêu nhẹ để trích xuất 468 điểm landmarks với tốc độ cao (FPS ổn định ngay cả trên CPU thông thường), thay vì dùng các mô hình Two-Stage nặng nề.
- **Tính toán Sinh trắc học & Hình học:** 
  - **EAR (Eye Aspect Ratio):** Nhận diện hành vi nhắm mắt/ngủ gật.
  - **MAR (Mouth Aspect Ratio):** Nhận diện hành vi ngáp.
  - **Head Pose Estimation:** Tính toán góc quay của đầu (Pitch, Yaw, Roll) để phát hiện hành vi nhìn lệch hướng, mất tập trung.
- **Xử lý thiếu sáng (CLAHE):** Tự động áp dụng kỹ thuật cân bằng Histogram (CLAHE) trên không gian màu LAB khi phát hiện môi trường ánh sáng yếu (mô phỏng IR Camera ban đêm).

## 📂 Cấu Trúc Thư Mục
```text
DrowsinessDetection/
├── assets/           # Chứa file âm thanh cảnh báo (alarm.wav), hình ảnh...
├── data/             # (Không đưa lên Git) Chứa video test, dữ liệu thô
├── src/
│   ├── config/       # Cấu hình các hằng số và ngưỡng (EAR_THRESHOLD...)
│   ├── threads/      # Core logic kiến trúc đa luồng
│   │   ├── camera_thread.py # Luồng I/O: Đọc ảnh từ Camera
│   │   ├── ai_thread.py     # Luồng CPU: Xử lý thuật toán AI
│   │   └── alert_thread.py  # Luồng I/O: Xử lý phát âm thanh cảnh báo
│   ├── ui/           # Vẽ bounding box, text và render giao diện
│   └── utils/        # Các hàm toán học, hình học, tiền xử lý ảnh
├── .gitignore        # Cấu hình loại trừ file/thư mục khi đưa lên Git
├── requirements.txt  # Danh sách các thư viện Python cần thiết
└── main.py           # File điều phối trung tâm (Orchestrator)
```

## ⚙️ Cài Đặt (Installation)

**Yêu cầu:** Máy tính đã cài đặt sẵn Python (khuyến nghị bản 3.8+).

1. **Clone dự án về máy:**
```bash
git clone https://github.com/vonguyenkiet/DrowsinessDetection.git
cd DrowsinessDetection
```

2. **Cài đặt thư viện:**
```bash
pip install -r requirements.txt
```
*(Các thư viện chính bao gồm: `opencv-python`, `mediapipe`, `pygame`, `numpy`)*

## 🚀 Hướng Dẫn Sử Dụng

Khởi động hệ thống thông qua file điều phối chính:
```bash
python main.py
```
- Ứng dụng sẽ tự động bật Webcam và bắt đầu quá trình giám sát.
- Khi người lái xe nhắm mắt lâu, ngáp liên tục hoặc không nhìn thẳng, chuông báo động sẽ vang lên (không gây đơ hình ảnh nhờ chạy đa luồng).
- **Thoát:** Nhấn phím `q` trên cửa sổ video để hệ thống tự động dọn dẹp các luồng bộ nhớ và thoát an toàn.

## 📝 Dành Cho Đồ Án Sinh Viên
Toàn bộ mã nguồn đã được comment giải thích chi tiết bằng tiếng Việt. Đặc biệt, bên trong các file `src/threads/ai_thread.py` và `src/threads/camera_thread.py` có chứa các lập luận học thuật sâu sắc nhằm giải thích lý do tại sao lại chọn các thuật toán và kiến trúc hiện tại. Bạn hoàn toàn có thể trích xuất các ý tưởng này để đưa vào quyển Báo cáo Đồ án / Luận văn của mình một cách thuyết phục.
