import os

# --- EAR & MAR THRESHOLDS ---
# Các giá trị này có thể tinh chỉnh sau quá trình Tuning Threshold trên tập UTA-RLDD
EAR_THRESHOLD = 0.25      # Ngưỡng nhắm mắt (dưới giá trị này là nhắm mắt)
MAR_THRESHOLD = 0.5       # Ngưỡng ngáp (trên giá trị này là ngáp)

# --- HEAD POSE THRESHOLDS (Distraction) ---
# Cảnh báo khi Yaw (quay trái/phải) hoặc Pitch (cúi/ngẩng) vượt ngưỡng
PITCH_THRESHOLD = 20.0    # Độ
YAW_THRESHOLD = 30.0      # Độ

# --- TIME PARAMETERS ---
ALERT_COOLDOWN = 3.0      # Giây: Thời gian đóng băng sau một cảnh báo để tránh spam

# --- QUEUE SETTINGS ---
FRAME_QUEUE_MAXSIZE = 2   # Queue size để áp dụng chiến lược "drop old, keep new"
