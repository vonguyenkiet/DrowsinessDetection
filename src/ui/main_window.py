import cv2
import time
import mediapipe as mp
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import queue

"""
MODULE: GIAO DIỆN NGƯỜI DÙNG (UI/UX) - Tkinter & Pillow
-------------------------------------------------------
Mục đích: Chuyển đổi luồng xử lý ảnh của OpenCV thành một ứng dụng Desktop hoàn chỉnh.

Cơ sở kỹ thuật:
1. Non-blocking UI Loop: Tkinter có một vòng lặp sự kiện chính (`mainloop()`). Nếu sử dụng `cv2.waitKey()` 
   như OpenCV truyền thống, giao diện sẽ bị "đóng băng" (Not Responding). Ở đây, ta dùng phương thức đệ quy 
   `self.root.after(15, self.update_frame)` để polling dữ liệu liên tục từ `result_queue` mỗi 15ms.
2. Render trung gian bằng Pillow: Tkinter không hỗ trợ mảng BGR của OpenCV. Do đó ta phải:
   OpenCV (BGR) -> RGB -> Pillow Image -> ImageTk (Tkinter tương thích) để render lên màn hình.
"""

class DMSApplication:
    def __init__(self, root, result_queue, stop_event, camera_thread):
        self.root = root
        self.result_queue = result_queue
        self.stop_event = stop_event
        self.camera_thread = camera_thread
        
        self.root.title("Hệ Thống Giám Sát Lái Xe (DMS)")
        # 1. Cố định kích thước chuẩn 1200x700
        self.root.geometry("1200x700")
        self.root.configure(bg="#2c3e50")
        # 2. Không cho phép thay đổi kích thước cửa sổ để bảo vệ layout
        self.root.resizable(False, False)
        
        # Xử lý sự kiện đóng cửa sổ (Bấm nút X)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Công cụ vẽ MediaPipe
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_face_mesh = mp.solutions.face_mesh
        # Khởi tạo custom_spec như yêu cầu (Độ dày 1, màu vàng/Cyan)
        self.custom_spec = self.mp_drawing.DrawingSpec(thickness=1, circle_radius=1, color=(0, 255, 255))
        
        self.prev_time = time.time()
        
        self.setup_ui()
        self.update_frame()
        
    def setup_ui(self):
        # Thiết lập một Frame chính (Container) bọc toàn bộ với padding xung quanh
        self.main_container = tk.Frame(self.root, bg="#2c3e50")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=20)

        # ----- FRAME TRÁI (Hiển thị Video - Chiếm 800x600) -----
        self.video_frame = tk.Frame(self.main_container, bg="#000000", width=800, height=600)
        self.video_frame.pack(side=tk.LEFT, fill=tk.BOTH)
        # Bắt buộc frame không được phình to theo kích thước nội dung bên trong
        self.video_frame.pack_propagate(False) 
        
        # Label chứa khung hình video
        self.video_label = tk.Label(self.video_frame, bg="#000000")
        self.video_label.pack(fill=tk.BOTH, expand=True)
        
        # ----- FRAME PHẢI (Control Panel - Chiếm 380x600) -----
        # (width=380 vì padding của container đã chiếm một chút)
        self.panel_frame = tk.Frame(self.main_container, bg="#34495e", width=380, height=600)
        self.panel_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(20, 0))
        # Bắt buộc frame panel không được phình to hoặc thu nhỏ
        self.panel_frame.pack_propagate(False) 
        
        # 1. Tiêu đề trạng thái
        tk.Label(self.panel_frame, text="TRẠNG THÁI TÀI XẾ", font=("Segoe UI", 16, "bold"), bg="#34495e", fg="white").pack(pady=(20, 10))
        
        self.status_label = tk.Label(self.panel_frame, text="NORMAL", font=("Segoe UI", 28, "bold"), bg="#27ae60", fg="white", width=12, pady=15)
        self.status_label.pack(pady=10)
        
        # 2. Bảng thông số sinh trắc
        self.info_frame = tk.Frame(self.panel_frame, bg="#2c3e50", highlightbackground="#1abc9c", highlightthickness=2)
        self.info_frame.pack(pady=20, fill=tk.X, padx=20)
        
        font_info = ("Consolas", 14)
        self.ear_label = tk.Label(self.info_frame, text="EAR  : 0.000", font=font_info, bg="#2c3e50", fg="white", anchor="w")
        self.ear_label.pack(fill=tk.X, pady=8, padx=15)
        
        self.mar_label = tk.Label(self.info_frame, text="MAR  : 0.000", font=font_info, bg="#2c3e50", fg="white", anchor="w")
        self.mar_label.pack(fill=tk.X, pady=8, padx=15)
        
        self.pitch_label = tk.Label(self.info_frame, text="Pitch: 0.0°", font=font_info, bg="#2c3e50", fg="white", anchor="w")
        self.pitch_label.pack(fill=tk.X, pady=8, padx=15)
        
        self.yaw_label = tk.Label(self.info_frame, text="Yaw  : 0.0°", font=font_info, bg="#2c3e50", fg="white", anchor="w")
        self.yaw_label.pack(fill=tk.X, pady=8, padx=15)
        
        self.fps_label = tk.Label(self.info_frame, text="FPS  : 0.0", font=("Consolas", 14, "bold"), bg="#2c3e50", fg="#f1c40f", anchor="w")
        self.fps_label.pack(fill=tk.X, pady=(8, 15), padx=15)
        
        # 3. Các nút điều khiển
        self.btn_toggle_cam = tk.Button(self.panel_frame, text="Mở Camera Mặc Định", font=("Segoe UI", 12, "bold"), bg="#e67e22", fg="white", activebackground="#d35400", activeforeground="white", command=self.open_camera, cursor="hand2")
        self.btn_toggle_cam.pack(fill=tk.X, padx=20, pady=(30, 10), ipady=5)
        
        self.btn_load_video = tk.Button(self.panel_frame, text="Tải Video Test (.mp4)", font=("Segoe UI", 12, "bold"), bg="#3498db", fg="white", activebackground="#2980b9", activeforeground="white", command=self.load_video, cursor="hand2")
        self.btn_load_video.pack(fill=tk.X, padx=20, pady=10, ipady=5)
        
    def update_frame(self):
        # Nếu có tín hiệu dừng thì đóng App
        if self.stop_event.is_set():
            self.root.quit()
            return
            
        try:
            # Lấy dữ liệu từ AI Thread (Non-blocking)
            data = self.result_queue.get_nowait()
            
            # Lấy các biến từ dictionary
            frame = data["frame"]
            landmarks = data["landmarks"]
            ear, mar, pitch, yaw, state = data["ear"], data["mar"], data["pitch"], data["yaw"], data["state"]
            
            # Tính FPS
            curr_time = time.time()
            fps = 1 / (curr_time - self.prev_time) if curr_time > self.prev_time else 0
            self.prev_time = curr_time
            
            # --- XỬ LÝ ẢNH QUAN TRỌNG TRƯỚC KHI HIỂN THỊ ---
            # Ép cứng kích thước frame về 800x600 để vừa khít với video_frame bên trái
            # Bất kể video gốc là bao nhiêu (1080p, 4K), nó sẽ không làm vỡ layout Tkinter.
            frame = cv2.resize(frame, (800, 600))
            
            # Vẽ FaceMesh lên frame đã resize
            # (Chú ý: Vì landmark tọa độ tỉ lệ thuận nên vẽ sau khi resize vẫn đúng vị trí)
            if landmarks:
                self.mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=landmarks,
                    connections=self.mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=self.custom_spec
                )
                
            # Đổi màu Trạng Thái & Viền Video
            if state in ["Drowsy", "Distracted"]:
                self.status_label.config(text=state.upper(), bg="#e74c3c") # Đỏ báo động
                cv2.rectangle(frame, (0, 0), (frame.shape[1], frame.shape[0]), (0, 0, 255), 15) # Viền BGR
            else:
                self.status_label.config(text="NORMAL", bg="#27ae60") # Xanh an toàn
                
            # Cập nhật Bảng số liệu
            self.ear_label.config(text=f"EAR  : {ear:.3f}")
            self.mar_label.config(text=f"MAR  : {mar:.3f}")
            self.pitch_label.config(text=f"Pitch: {pitch:.1f}°")
            self.yaw_label.config(text=f"Yaw  : {yaw:.1f}°")
            self.fps_label.config(text=f"FPS  : {fps:.1f}")
            
            # Convert BGR (OpenCV) -> RGB -> ImageTk (Pillow) để render lên Tkinter
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk # Lưu reference tránh bị Garbage Collector xóa
            self.video_label.configure(image=imgtk)
            
        except queue.Empty:
            pass
            
        # Gọi đệ quy hàm này sau mỗi 15ms (~60 FPS target) trên Main Thread
        self.root.after(15, self.update_frame)
        
    def open_camera(self):
        """Đổi sang source 0 (Webcam)"""
        self.camera_thread.change_source(0)
        self.btn_toggle_cam.config(text="Đang phát: Webcam", bg="#e67e22")
        self.btn_load_video.config(bg="#3498db")
        
    def load_video(self):
        """Mở hộp thoại chọn file video để test"""
        file_path = filedialog.askopenfilename(
            title="Chọn Video Test",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov")]
        )
        if file_path:
            self.camera_thread.change_source(file_path)
            self.btn_load_video.config(text="Đang phát: Video File", bg="#1abc9c")
            self.btn_toggle_cam.config(text="Chuyển sang Webcam", bg="#95a5a6")

    def on_close(self):
        """Hàm kích hoạt khi người dùng ấn nút X đóng cửa sổ"""
        print("[UI] Đang gửi tín hiệu đóng các luồng phụ...")
        self.stop_event.set()
        self.root.quit()

def run_main_ui(result_queue, stop_event, camera_thread):
    # Khởi tạo gốc Tkinter
    root = tk.Tk()
    # Khởi tạo App
    app = DMSApplication(root, result_queue, stop_event, camera_thread)
    # Vòng lặp Mainloop chặn Main Thread
    root.mainloop()
