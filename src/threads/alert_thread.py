import threading
import queue
import time
import pygame
import os
import sys

# Đảm bảo có thể import cấu hình settings khi chạy file riêng lẻ
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.config.settings import ALERT_COOLDOWN

class AlertThread(threading.Thread):
    """
    Luồng độc lập đảm nhiệm việc phát âm thanh cảnh báo khi tài xế có dấu hiệu Buồn ngủ hoặc Mất tập trung.
    Việc tách luồng Alert giúp quá trình xử lý AI không bị chặn (blocking) bởi tác vụ I/O âm thanh.
    """
    def __init__(self, state_queue, sound_path="assets/sounds/alarm.wav"):
        """
        Khởi tạo luồng cảnh báo.
        state_queue: Hàng đợi nhận chuỗi trạng thái từ AI Thread (VD: 'Normal', 'Drowsy', 'Distracted')
        sound_path: Đường dẫn tới file âm thanh cảnh báo
        """
        super().__init__()
        self.state_queue = state_queue
        self.running = False
        self.sound_path = sound_path
        self.last_alert_time = 0.0

        # Khởi tạo pygame mixer để xử lý âm thanh không chặn
        pygame.mixer.init()
        try:
            self.sound = pygame.mixer.Sound(self.sound_path)
        except Exception as e:
            print(f"AlertThread: Không thể tải âm thanh từ {self.sound_path}. {e}")
            self.sound = None

    def run(self):
        self.running = True
        while self.running:
            try:
                # Đợi dữ liệu trạng thái mới (timeout 1s để duy trì việc kiểm tra cờ self.running)
                state = self.state_queue.get(timeout=1.0)
                
                if state in ["Drowsy", "Distracted"]:
                    current_time = time.time()
                    
                    # Logic Cooldown: Chỉ phát nếu khoảng cách từ lần cuối cảnh báo > ALERT_COOLDOWN (3 giây)
                    if current_time - self.last_alert_time >= ALERT_COOLDOWN:
                        if self.sound:
                            self.sound.play()
                        print(f"[{time.strftime('%H:%M:%S')}] 🚨 PHÁT ÂM THANH CẢNH BÁO: {state.upper()}!")
                        self.last_alert_time = current_time
                        
            except queue.Empty:
                # Hàng đợi trống, tiếp tục vòng lặp
                pass

    def stop(self):
        self.running = False
        pygame.mixer.quit()
