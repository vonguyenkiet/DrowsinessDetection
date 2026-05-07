import threading
import queue
import cv2
import mediapipe as mp
import sys
import os

# Đảm bảo đường dẫn import tương đối
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.config.settings import EAR_THRESHOLD, MAR_THRESHOLD, PITCH_THRESHOLD, YAW_THRESHOLD
from src.utils.geometry import calculate_ear, calculate_mar
from src.utils.pose import get_head_pose
from src.utils.preprocessing import preprocess_frame

class AIThread(threading.Thread):
    """
    Luồng AI đảm nhận tính toán nặng nhất của hệ thống: Phát hiện khuôn mặt và đánh giá chỉ số sinh trắc.
    
    YÊU CẦU LÝ THUYẾT HỌC THUẬT:
    --------------------------
    Kiến trúc AI: Tại sao chọn MediaPipe FaceMesh (kiến trúc One-Stage) thay vì Two-Stage?
    - Trong các mạng Two-Stage (như Faster R-CNN), quá trình xử lý phụ thuộc nhiều vào module 
      Region Proposal Network (hoặc Selective Search) để lọc ra các vùng ứng viên, sau đó mới 
      dùng RoI Pooling để trích xuất đặc trưng. Mặc dù cho độ chính xác cao nhưng luồng xử lý 
      hai giai đoạn này quá tốn kém và hoàn toàn không phù hợp với yêu cầu Real-time của DMS.
    - Ngược lại, MediaPipe dựa trên BlazeFace (kiến trúc One-Stage siêu nhẹ). Thuật toán này 
      hoạt động như một bộ dò tìm một chặng (single-shot detector), kết hợp dự đoán Bounding Box 
      và 468 Landmarks trực tiếp trên toàn bộ vùng ảnh mà không cần qua bước trung gian tạo Region 
      Proposals. Sự tinh giản này giúp hệ thống đạt FPS rất cao ngay cả trên CPU, lý tưởng 
      cho luồng AI phân tích thời gian thực trong ô tô.
    """
    def __init__(self, frame_queue, result_queue, state_queue, stop_event):
        super().__init__()
        self.frame_queue = frame_queue
        self.result_queue = result_queue
        self.state_queue = state_queue
        self.stop_event = stop_event
        
        # Khởi tạo MediaPipe FaceMesh
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Cơ chế Sliding Counter (Bộ đếm trượt)
        self.drowsy_counter = 0
        self.yawn_counter = 0
        self.distracted_counter = 0
        
        # Số frame vượt ngưỡng liên tiếp để đưa ra quyết định (Tuning parameters)
        self.DROWSY_FRAMES_TH = 15
        self.YAWN_FRAMES_TH = 10
        self.DISTRACTED_FRAMES_TH = 15

    def run(self):
        while not self.stop_event.is_set():
            # 1. Lấy frame từ queue (non-blocking để kiểm tra stop_event)
            try:
                frame = self.frame_queue.get(timeout=0.1)
            except queue.Empty:
                continue
                
            # Lưu lại bản copy để hiển thị (chưa bị vẽ đè bởi MediaPipe trong luồng này)
            display_frame = frame.copy()
            h, w, _ = frame.shape
            
            # 2. Tiền xử lý (Xử lý thiếu sáng bằng CLAHE và chuyển sang RGB bắt buộc)
            rgb_frame, _ = preprocess_frame(frame)
            
            # 3. Chạy MediaPipe FaceMesh
            results = self.face_mesh.process(rgb_frame)
            
            state = "Normal"
            ear, mar, pitch, yaw, roll = 0.0, 0.0, 0.0, 0.0, 0.0
            
            if results.multi_face_landmarks:
                landmarks = results.multi_face_landmarks[0].landmark
                
                # Trích xuất Landmarks cho EAR (2 mắt x 6 điểm)
                left_eye_indices = [362, 385, 387, 263, 373, 380]
                right_eye_indices = [33, 160, 158, 133, 153, 144]
                
                left_eye = [landmarks[i] for i in left_eye_indices]
                right_eye = [landmarks[i] for i in right_eye_indices]
                
                ear = (calculate_ear(left_eye, w, h) + calculate_ear(right_eye, w, h)) / 2.0
                
                # Trích xuất Landmarks cho MAR (8 điểm miệng)
                mouth_indices = [61, 81, 13, 311, 291, 402, 14, 178]
                mouth = [landmarks[i] for i in mouth_indices]
                mar = calculate_mar(mouth, w, h)
                
                # Trích xuất góc Head Pose
                pitch, yaw, roll = get_head_pose(landmarks, w, h)
                
                # 4. Cơ chế Sliding Counter
                # --- Nhắm mắt (Drowsy) ---
                if ear < EAR_THRESHOLD:
                    self.drowsy_counter += 1
                else:
                    self.drowsy_counter = 0 # Reset về 0 nếu bình thường
                
                # --- Ngáp (Yawning - Drowsy) ---
                if mar > MAR_THRESHOLD:
                    self.yawn_counter += 1
                else:
                    self.yawn_counter = 0
                    
                # --- Nhìn lệch (Distracted) ---
                if abs(yaw) > YAW_THRESHOLD or abs(pitch) > PITCH_THRESHOLD:
                    self.distracted_counter += 1
                else:
                    self.distracted_counter = 0
                
                # 5. Phân tích kết quả logic
                if self.drowsy_counter >= self.DROWSY_FRAMES_TH or self.yawn_counter >= self.YAWN_FRAMES_TH:
                    state = "Drowsy"
                elif self.distracted_counter >= self.DISTRACTED_FRAMES_TH:
                    state = "Distracted"
                else:
                    state = "Normal"
            
            # Gửi tín hiệu sang Alert Thread (Drop old, keep new)
            try:
                self.state_queue.put_nowait(state)
            except queue.Full:
                try:
                    self.state_queue.get_nowait()
                    self.state_queue.put_nowait(state)
                except queue.Empty:
                    pass
            
            # Đóng gói dữ liệu hiển thị cho UI
            result_data = {
                "frame": display_frame,
                "landmarks": results.multi_face_landmarks[0] if results.multi_face_landmarks else None,
                "ear": ear,
                "mar": mar,
                "pitch": pitch,
                "yaw": yaw,
                "state": state
            }
            
            # Đẩy vào result_queue (Drop old, keep new)
            if self.result_queue.full():
                try:
                    self.result_queue.get_nowait()
                except queue.Empty:
                    pass
            
            try:
                self.result_queue.put_nowait(result_data)
            except queue.Full:
                pass
                
        # Dọn dẹp MediaPipe khi dừng luồng
        self.face_mesh.close()
