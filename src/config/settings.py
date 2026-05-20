import os

"""
MODULE: SYSTEM SETTINGS (Cấu hình hệ thống tập trung)
------------------------------------------------------
Mục đích: Tách biệt toàn bộ tham số Hard-coded ra khỏi logic code chính (Decoupling Configuration from Logic).

Cơ sở lý thuyết phần mềm (Software Engineering & MLOps):
1. Khả năng bảo trì (Maintainability): Việc lưu trữ EAR, MAR, Head Pose ngưỡng tập trung tại một file 
   cho phép các kỹ sư dễ dàng tinh chỉnh hệ thống mà không cần đọc và sửa đổi mã nguồn thuật toán lõi.
2. Tiền đề MLOps: Cấu trúc này mở đường cho việc triển khai tự động hóa. Khi chạy script `threshold_tuning.py`, 
   hệ thống có thể tự động ghi đè các tham số mới học được vào file này bằng Regex, biến AI tĩnh thành 
   AI thích ứng (Adaptive AI).
"""

# --- EAR & MAR THRESHOLDS ---
# Các giá trị này có thể tinh chỉnh sau quá trình Tuning Threshold trên tập UTA-RLDD
EAR_THRESHOLD = 0.22      # Ngưỡng nhắm mắt (dưới giá trị này là nhắm mắt)
MAR_THRESHOLD = 0.55       # Ngưỡng ngáp (trên giá trị này là ngáp)

# --- HEAD POSE THRESHOLDS (Distraction) ---
# Cảnh báo khi Yaw (quay trái/phải) hoặc Pitch (cúi/ngẩng) vượt ngưỡng
PITCH_THRESHOLD = 20.0    # Độ
YAW_THRESHOLD = 30.0      # Độ

# --- TIME PARAMETERS ---
ALERT_COOLDOWN = 4.0      # Giây: Thời gian đóng băng sau một cảnh báo để tránh spam

# --- QUEUE SETTINGS ---
FRAME_QUEUE_MAXSIZE = 2   # Queue size để áp dụng chiến lược "drop old, keep new"
