import cv2
import threading
import queue

class CameraThread(threading.Thread):
    """
    Luồng độc lập đảm nhiệm việc đọc frame từ camera (webcam) hoặc video file.
    
    Trong các hệ thống Computer Vision cổ điển, để giảm tải tính toán trên toàn khung hình, 
    người ta thường kết hợp Selective Search tạo các Region Proposals. Tuy nhiên, để đảm bảo 
    tốc độ Real-time, hệ thống phân chia luồng I/O đọc ảnh ra khỏi luồng xử lý AI.
    Việc sử dụng hàng đợi với maxsize=2 giúp giới hạn không gian lưu trữ đặc trưng,
    tương tự như cách giới hạn số lượng RoI (Region of Interest) để tiết kiệm tài nguyên.
    """
    def __init__(self, frame_queue, source=0):
        """
        Khởi tạo luồng đọc camera.
        frame_queue: Hàng đợi dùng chung (queue.Queue(maxsize=2))
        source: 0 cho webcam, hoặc đường dẫn file video test (VD: 'data/raw_videos/Drowsy/video.mp4')
        """
        super().__init__()
        self.frame_queue = frame_queue
        self.source = source
        self.running = False
        self.new_source = None
        self.cap = cv2.VideoCapture(self.source)

    def change_source(self, source):
        """Yêu cầu đổi nguồn video (gọi từ UI thread)"""
        self.new_source = source

    def run(self):
        self.running = True
        while self.running:
            # Nếu có yêu cầu đổi nguồn từ UI
            if self.new_source is not None:
                if self.cap.isOpened():
                    self.cap.release()
                self.source = self.new_source
                self.cap = cv2.VideoCapture(self.source)
                self.new_source = None
                
            ret, frame = self.cap.read()
            if not ret:
                # Nếu đọc hết file video (trong quá trình test), lặp lại từ đầu
                if isinstance(self.source, str):
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    print("CameraThread: Lỗi đọc frame từ camera hoặc luồng kết thúc.")
                    break
            
            # Chiến lược "Drop old, keep new":
            # Đảm bảo hệ thống luôn xử lý khung hình mới nhất, độ trễ <= 2s.
            if self.frame_queue.full():
                try:
                    # Bắt buộc dùng get_nowait() để loại bỏ frame cũ nhất
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
            
            # Đẩy frame mới vào hàng đợi
            try:
                self.frame_queue.put_nowait(frame)
            except queue.Full:
                pass

    def stop(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()
