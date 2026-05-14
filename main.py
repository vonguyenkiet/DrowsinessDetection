import threading
import queue
import time
import sys
import os

"""
MODULE CHÍNH: KHỞI CHẠY HỆ THỐNG (Main Entry Point)
---------------------------------------------------
Kiến trúc luồng (Multi-threading Architecture):
Dự án áp dụng mô hình phân tán tác vụ qua 4 luồng độc lập để tối ưu hóa hiệu năng và đạt được Real-time:
1. Camera Thread: Chỉ chịu trách nhiệm đọc frame từ Camera hoặc File Video. (I/O Bound)
2. AI Thread: Chạy MediaPipe FaceMesh và tính toán khoảng cách hình học EAR/MAR/Pose. (CPU Bound)
3. Alert Thread: Quản lý phát âm thanh cảnh báo không đồng bộ bằng Pygame, tránh làm đứng hình. (I/O Bound)
4. UI Thread (Main): Vẽ giao diện Tkinter và lấy dữ liệu từ AI Thread để hiển thị. (Event Loop)

Giao tiếp giữa các luồng:
Sử dụng cấu trúc dữ liệu `queue.Queue` với maxsize=2 kết hợp chiến lược "Drop old, keep new" 
(Bỏ frame cũ, giữ frame mới) để đảm bảo độ trễ giữa Camera và Giao diện UI luôn <= 2 giây.
"""

from src.threads.camera_thread import CameraThread
from src.threads.ai_thread import AIThread
from src.threads.alert_thread import AlertThread
from src.ui.main_window import run_main_ui

def main():
    print("==================================================")
    print(" KHỞI ĐỘNG HỆ THỐNG CẢNH BÁO LÁI XE (DMS)")
    print("==================================================")

    # 1. Khởi tạo Event điều phối luồng
    # Cờ tín hiệu chung dùng để thông báo cho tất cả các luồng phụ dừng lại khi người dùng tắt app
    stop_event = threading.Event()
    
    # 2. Khởi tạo các hàng đợi giao tiếp (Queues)
    # maxsize=2 kết hợp chiến lược "drop old, keep new" giúp giữ độ trễ luôn <= 2 giây
    frame_queue = queue.Queue(maxsize=2)
    result_queue = queue.Queue(maxsize=2)
    state_queue = queue.Queue(maxsize=2)
    
    # 3. Khởi tạo các Luồng (Threads)
    # Luồng Camera I/O: Đọc từ webcam (source=0) hoặc file video
    camera_thread = CameraThread(frame_queue=frame_queue, source=0)
    
    # Luồng xử lý AI (MediaPipe FaceMesh)
    ai_thread = AIThread(frame_queue=frame_queue, result_queue=result_queue, state_queue=state_queue, stop_event=stop_event)
    
    # Luồng cảnh báo âm thanh
    alert_thread = AlertThread(state_queue=state_queue, sound_path="assets/sounds/alarm.wav")
    
    # Bắt đầu chạy các luồng phụ ở background
    print("[INFO] Đang khởi động Camera Thread...")
    camera_thread.start()
    
    print("[INFO] Đang khởi động AI Thread...")
    ai_thread.start()
    
    print("[INFO] Đang khởi động Alert Thread...")
    alert_thread.start()
    
    time.sleep(1.0) # Đợi một chút để camera khởi động
    print("\n[SUCCESS] Hệ thống đang chạy! Nhấn phím 'q' trên cửa sổ video để THOÁT.")

    # 4. Chạy Luồng UI (Buộc phải nằm ở Main Thread)
    try:
        run_main_ui(result_queue=result_queue, stop_event=stop_event, camera_thread=camera_thread)
    except KeyboardInterrupt:
        # Xử lý khi người dùng nhấn Ctrl+C ở terminal
        stop_event.set()
        
    print("\n[INFO] Tín hiệu thoát (stop_event) đã được kích hoạt. Đang đóng hệ thống...")
    
    # 5. Dọn dẹp tài nguyên
    # Đảm bảo set cờ dừng một lần nữa đề phòng luồng UI thoát do lỗi chứ không phải do bấm 'q'
    stop_event.set()
    
    # Gọi hàm stop() thủ công cho các luồng sử dụng vòng lặp tự quản lý cờ running
    camera_thread.stop()
    alert_thread.stop()
    
    # Đợi các luồng background kết thúc an toàn
    camera_thread.join(timeout=2.0)
    ai_thread.join(timeout=2.0)
    alert_thread.join(timeout=2.0)
    
    print("[SUCCESS] Tất cả các luồng đã được dọn dẹp sạch sẽ. Tạm biệt!")

if __name__ == "__main__":
    main()
