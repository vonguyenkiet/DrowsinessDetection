# 🚗 Đồ Án: Hệ Thống Cảnh Báo Lái Xe An Toàn (Drowsiness & Distraction Detection)

```text
Công nghệ: Python 3.x · OpenCV · MediaPipe FaceMesh · Multi-threading · Pygame · NumPy
Dữ liệu: UTA-RLDD (đã cắt và gán nhãn) · YawDD · NTHU
```

## 🎯 Mục Tiêu Học Tập

Sau khi hoàn thành đồ án này, sinh viên có thể:

* [cite_start]Xây dựng hệ thống thị giác máy tính xử lý luồng video thời gian thực (Real-time Video Processing)[cite: 1].
* [cite_start]Vận dụng các chỉ số sinh trắc học: **EAR** (mắt), **MAR** (miệng) và **Head Pose** (tư thế đầu) để phân tích trạng thái người dùng[cite: 1].
* [cite_start]Triển khai kiến trúc xử lý đa luồng (**Multi-threading**) để tối ưu hiệu năng và giảm độ trễ[cite: 1].
* [cite_start]Xử lý ảnh trong điều kiện thiếu sáng ban đêm bằng kỹ thuật **CLAHE**[cite: 1].
* Thực hiện quy trình tinh chỉnh ngưỡng (Threshold Tuning) dựa trên dữ liệu thực tế (UTA Dataset).

## 📱 Mô Tả Ứng Dụng

[cite_start]Hệ thống phân tích video từ camera để nhận diện các dấu hiệu nguy hiểm: nhắm mắt quá lâu, ngáp liên tục hoặc quay mặt/nhìn lệch khỏi đường đi[cite: 1]. [cite_start]Ứng dụng phải hoạt động ổn định với độ trễ phản hồi không quá 2 giây[cite: 1].

### Các trạng thái nhận diện

| Trạng thái | Mô tả logic |
| :--- | :--- |
| **Bình thường (Normal)** | [cite_start]Mắt mở, miệng đóng, nhìn thẳng về phía trước[cite: 1]. |
| **Buồn ngủ (Drowsy)** | [cite_start]EAR thấp liên tục (nhắm mắt) hoặc MAR cao liên tục (ngáp)[cite: 1]. |
| **Mất tập trung (Distracted)** | [cite_start]Đầu quay trái/phải (Yaw) hoặc cúi/ngẩng (Pitch) vượt ngưỡng[cite: 1]. |

## 📊 Xử Lý Dữ Liệu (UTA Dataset)

Dữ liệu UTA-RLDD đã được cắt nhỏ và gán nhãn đóng vai trò cực kỳ quan trọng trong việc "dạy" và "kiểm chứng" hệ thống.

### Các bước thực hiện với dữ liệu:
1.  **Phân tích nhãn:** Sử dụng các frame đã gán nhãn (Normal/Drowsy) để trích xuất giá trị EAR/MAR tương ứng.
2.  [cite_start]**Tuning Threshold:** Tính toán phân phối xác suất của EAR khi mắt mở và mắt đóng từ dữ liệu UTA để chọn ra ngưỡng (Threshold) tối ưu, thay vì đặt một con số cảm tính[cite: 1].
3.  **Validation:** Chạy thuật toán trên các đoạn clip đã cắt để đo tỷ lệ chính xác (Accuracy) và tỷ lệ cảnh báo sai (False Positive).

### Dữ liệu dùng để làm gì?
* **Chứng minh tính Robust:** Đảm bảo thuật toán hoạt động đúng trên nhiều khuôn mặt khác nhau trong tập UTA.
* [cite_start]**Xác định độ dài Sliding Window:** Dùng dữ liệu video để quyết định cần bao nhiêu khung hình nhắm mắt liên tục thì phát cảnh báo là chính xác nhất[cite: 1].

## 🏗 Cấu Trúc Thư Mục Chuẩn

```text
DrowsinessDetection/
├── assets/
│   ├── sounds/              ← File cảnh báo: alarm.wav, beep.mp3
│   └── icons/               ← Icon hiển thị trạng thái UI
├── data/
│   ├── uta_labeled/         ← Dữ liệu UTA đã cắt và gán nhãn
│   └── raw_videos/          ← Video quay thực tế để test
├── src/
│   ├── threads/
[cite_start]│   │   ├── camera_thread.py ← Thread 1: Đọc frame từ camera [cite: 1]
[cite_start]│   │   ├── ai_thread.py     ← Thread 2: Xử lý MediaPipe & Logic AI [cite: 1]
[cite_start]│   │   └── alert_thread.py  ← Thread 3: Quản lý âm thanh cảnh báo độc lập [cite: 1]
│   ├── utils/
[cite_start]│   │   ├── geometry.py      ← Tính EAR, MAR, Khoảng cách Euclidean [cite: 1]
[cite_start]│   │   ├── pose.py          ← Tính Head Pose (SolvePnP) [cite: 1]
[cite_start]│   │   └── preprocessing.py ← CLAHE, chuyển đổi RGB [cite: 1]
│   └── ui/
[cite_start]│       └── main_window.py   ← UI Thread: Hiển thị OpenCV Overlay [cite: 1]
├── .env                     ← Lưu ngưỡng threshold, đường dẫn camera
├── main.py                  ← Điểm khởi chạy ứng dụng (Entry point)
└── requirements.txt
```

## 🏗 Yêu Cầu Kỹ Thuật (Bắt buộc theo pdf_content)

### 1. Giải pháp AI & Sinh trắc học
* **EAR (Eye Aspect Ratio):** Sử dụng 6 điểm mốc quanh mắt. [cite_start]Công thức phải đảm bảo tính chuẩn hóa để không phụ thuộc khoảng cách camera[cite: 1].
* [cite_start]**MAR (Mouth Aspect Ratio):** Sử dụng 8 điểm mốc vùng môi để phát hiện hành vi ngáp[cite: 1].
* **Head Pose Estimation:** Sử dụng thuật toán `cv2.solvePnP` để tính 3 góc xoay (Yaw, Pitch, Roll). [cite_start]Cảnh báo khi Yaw > $\pm30^\circ$ hoặc Pitch > $\pm20^\circ$[cite: 1].

### 2. Kiến trúc đa luồng (Multi-threading)
* [cite_start]**Thread 1 (Camera):** Sử dụng chiến lược "drop old, keep new" với `maxsize=2` để đảm bảo frame xử lý luôn là mới nhất[cite: 1].
* [cite_start]**Thread 2 (AI):** Thực hiện tiền xử lý CLAHE nếu điều kiện thiếu sáng (< 80 pixel trung bình) trước khi đưa vào MediaPipe[cite: 1].
* [cite_start]**Thread 3 (Alert):** Phải có cơ chế **Cooldown (3 giây)** để không gây khó chịu cho tài xế khi cảnh báo lặp lại[cite: 1].

## 🐛 Yêu Cầu Debug & Kiểm Chứng

### Làm sao biết hệ thống hoạt động đúng?
1.  [cite_start]**Bật Debug Mode:** Hiển thị giá trị EAR/MAR và các góc xoay trực tiếp trên màn hình[cite: 1].
2.  **Kiểm chứng độ trễ:** Sử dụng timer để đo thời gian từ khi mắt nhắm (trên video test) đến khi loa phát tiếng kêu. [cite_start]Kết quả phải $\le$ 2 giây[cite: 1].
3.  [cite_start]**Test Night Mode:** Tắt đèn và sử dụng camera IR, kiểm tra xem CLAHE có giúp MediaPipe nhận diện được 468 điểm landmarks hay không[cite: 1].
4.  **Chụp ảnh bằng chứng:** Chụp ít nhất 4 ảnh màn hình hệ thống đang nhận diện 4 trạng thái: Tỉnh táo, Nhắm mắt, Ngáp, và Nhìn lệch hướng.

## 📚 Hướng Dẫn Dùng AI / Vibe Coding

Sinh viên có thể dùng AI hỗ trợ nhưng phải tuân thủ quy trình kiểm soát:

### Cách prompt đúng (Ví dụ cho Head Pose):
> "Tôi đang làm project phát hiện mất tập trung bằng Python và MediaPipe. Hãy viết hàm `get_head_pose` sử dụng `cv2.solvePnP`. Đầu vào là 6 điểm landmarks (mũi, cằm, mắt, miệng). Hãy giải thích cách chuyển đổi rotation vector sang góc Euler (Yaw, Pitch, Roll)."

### Kiểm chứng code AI:
1.  [cite_start]**Kiểm tra luồng:** Đảm bảo AI không đặt lệnh `cv2.imshow()` vào luồng phụ (vì sẽ gây crash trên macOS/Windows)[cite: 1].
2.  [cite_start]**Kiểm tra tọa độ:** Đảm bảo MediaPipe landmarks (giá trị 0-1) đã được nhân với chiều rộng/cao của ảnh trước khi tính toán Euclidean[cite: 1].

## 🚀 Gợi Ý Thứ Tự Làm

1.  [cite_start]**Tuần 1:** Setup môi trường, viết luồng đọc camera (Thread 1) và vẽ landmarks cơ bản lên UI[cite: 1].
2.  **Tuần 2:** Viết module `geometry.py` để tính EAR/MAR. [cite_start]Dùng dữ liệu UTA để chốt ngưỡng Threshold cho từng thành viên trong nhóm[cite: 1].
3.  [cite_start]**Tuần 3:** Triển khai Head Pose Estimation và logic nhận diện nhìn lệch hướng[cite: 1].
4.  [cite_start]**Tuần 4:** Hoàn thiện đa luồng, tích hợp âm thanh cảnh báo (Thread 3) và module xử lý ban đêm (CLAHE)[cite: 1].
5.  [cite_start]**Tuần 5:** Chạy thực nghiệm trên video test $\ge$ 30 phút, lập bảng thống kê độ chính xác và hoàn thiện báo cáo[cite: 1].

