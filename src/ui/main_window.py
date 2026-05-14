import cv2
import time
import mediapipe as mp

def run_main_ui(result_queue, stop_event):
    """
    Luồng UI Chính (Main Thread).
    Hiển thị giao diện người dùng và lắng nghe sự kiện phím bấm. 
    Các hàm như cv2.imshow() và cv2.waitKey() BẮT BUỘC phải nằm trong luồng này 
    để không gây crash hệ thống trên môi trường Windows và macOS.
    """
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_face_mesh = mp.solutions.face_mesh

    prev_time = time.time()
    
    # Tạo cửa sổ OpenCV
    window_name = "Driver Monitoring System (DMS)"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    
    while not stop_event.is_set():
        try:
            # Dùng timeout nhỏ (0.05s) để cửa sổ vẫn phản hồi phím nhấn khi queue rỗng
            data = result_queue.get(timeout=0.05)
        except:
            # Lắng nghe sự kiện thoát ngay cả khi chưa có data
            if cv2.waitKey(1) & 0xFF == ord('q'):
                stop_event.set()
            continue
            
        frame = data["frame"]
        landmarks = data["landmarks"]
        ear = data["ear"]
        mar = data["mar"]
        pitch = data["pitch"]
        yaw = data["yaw"]
        state = data["state"]
        
        # Tính toán FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if curr_time > prev_time else 0
        prev_time = curr_time
        
        # 1. Vẽ FaceMesh Landmarks lên khung hình
        if landmarks:
            custom_spec = mp_drawing.DrawingSpec(thickness=2, circle_radius=2, color=(0, 255, 255)) # Cyan
            mp_drawing.draw_landmarks(
                image=frame,
                landmark_list=landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=custom_spec,
                connection_drawing_spec=custom_spec
            )
        
        # 2. Xử lý logic hiển thị màu sắc và trạng thái (Xanh lá / Đỏ)
        if state in ["Drowsy", "Distracted"]:
            color = (0, 0, 255) # BGR: Đỏ
            # Viền khung cảnh báo
            cv2.rectangle(frame, (0, 0), (frame.shape[1], frame.shape[0]), color, 10)
        else:
            color = (0, 255, 0) # BGR: Xanh lá
            
        # 3. Vẽ Overlay: Trạng thái, Thông số EAR, MAR, Pitch, Yaw và FPS
        cv2.putText(frame, f"State: {state}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
        cv2.putText(frame, f"EAR: {ear:.3f}", (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"MAR: {mar:.3f}", (20, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Pitch: {pitch:.1f}", (20, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        cv2.putText(frame, f"Yaw:   {yaw:.1f}", (20, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        cv2.putText(frame, f"FPS: {fps:.1f}", (frame.shape[1] - 150, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        
        # Hiển thị
        cv2.imshow(window_name, frame)
        
        # Lắng nghe phím 'q' để dừng vòng lặp UI và báo stop_event tới các luồng khác
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_event.set()
            break
            
    cv2.destroyAllWindows()
