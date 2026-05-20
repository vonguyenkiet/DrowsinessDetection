import os
import cv2
import shutil

def label_videos(input_dir, output_dir):
    """
    Tool hỗ trợ gán nhãn video thủ công (Drowsy, Distracted, Normal).
    Nhấn 1: Drowsy (Ngáp, gật đầu)
    Nhấn 2: Distracted (Quay đầu, mất tập trung)
    Nhấn 3: Normal (Bình thường)
    Nhấn s: Bỏ qua video (Skip)
    Nhấn q: Thoát chương trình (Quit)
    """
    # Các nhãn và thư mục tương ứng
    labels = {
        ord('1'): 'Drowsy',
        ord('2'): 'Distracted',
        ord('3'): 'Normal'
    }
    
    # Tạo các thư mục đầu ra nếu chưa có
    for label in labels.values():
        os.makedirs(os.path.join(output_dir, label), exist_ok=True)
        
    # Lấy danh sách video trong thư mục đầu vào
    valid_extensions = ('.mp4', '.avi', '.mov', '.mkv')
    videos = [f for f in os.listdir(input_dir) if f.lower().endswith(valid_extensions)]
    
    if not videos:
        print(f"Không tìm thấy video nào trong thư mục {input_dir}")
        return
        
    print(f"Tìm thấy {len(videos)} video cần gán nhãn.")
    print("--------------------------------------------------")
    print("HƯỚNG DẪN:")
    print(" - Nhấn 1: Gán nhãn Drowsy (Ngáp, gật đầu)")
    print(" - Nhấn 2: Gán nhãn Distracted (Quay đầu, mất tập trung)")
    print(" - Nhấn 3: Gán nhãn Normal (Bình thường)")
    print(" - Nhấn 's': Bỏ qua video này (Skip)")
    print(" - Nhấn 'q': Lưu lại và Thoát tool (Quit)")
    print("--------------------------------------------------")
    
    for idx, video_name in enumerate(videos):
        video_path = os.path.join(input_dir, video_name)
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            print(f"Không thể mở video {video_name}. Bỏ qua.")
            continue
            
        print(f"\n[{idx + 1}/{len(videos)}] Đang phát: {video_name}")
        
        assigned_label = None
        quit_tool = False
        
        # Phát video lặp lại liên tục cho đến khi người dùng bấm phím
        while True:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Bắt đầu lại từ đầu
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break # Hết video, sẽ quay lại từ đầu vòng lặp while True
                
                # Resize để dễ nhìn nếu video quá to
                height, width = frame.shape[:2]
                max_width = 800
                if width > max_width:
                    scale = max_width / width
                    frame = cv2.resize(frame, (max_width, int(height * scale)))
                    
                # Thêm hướng dẫn lên màn hình
                cv2.putText(frame, f"Video: {video_name}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                cv2.putText(frame, "1: Drowsy | 2: Distracted | 3: Normal | s: Skip | q: Quit", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                cv2.imshow("Video Labeling Tool", frame)
                
                # Đợi phím (khoảng 30ms cho mỗi frame)
                key = cv2.waitKey(30) & 0xFF
                
                if key in labels:
                    assigned_label = labels[key]
                    break
                elif key == ord('s'):
                    assigned_label = "Skip"
                    break
                elif key == ord('q'):
                    quit_tool = True
                    break
                    
            if assigned_label or quit_tool:
                break
                
        cap.release()
        
        if quit_tool:
            print("Đã thoát công cụ gán nhãn.")
            break
            
        if assigned_label == "Skip":
            print(f"-> Đã bỏ qua {video_name}")
            continue
            
        if assigned_label:
            # Di chuyển video vào thư mục tương ứng, giữ nguyên tên
            dest_folder = os.path.join(output_dir, assigned_label)
            dest_path = os.path.join(dest_folder, video_name)
            
            # Xử lý nếu đã có file trùng tên ở đích
            if os.path.exists(dest_path):
                print(f"-> Cảnh báo: File {video_name} đã tồn tại trong {assigned_label}. Ghi đè.")
                os.remove(dest_path)
                
            shutil.move(video_path, dest_path)
            print(f"-> Đã chuyển {video_name} vào thư mục {assigned_label} (Gán đúng tên video gốc)")
            
    cv2.destroyAllWindows()
    print("\nHOÀN TẤT!")

if __name__ == "__main__":
    # ĐƯỜNG DẪN MẶC ĐỊNH - Bạn có thể sửa đường dẫn ở đây
    # Ví dụ: Nơi chứa các video chưa gán nhãn
    INPUT_DIRECTORY = r"C:\Users\Kiet\Downloads\68cs2\học kì 6\Thị giác máy tính\DMS_Project\data\raw" 
    
    # Nơi chứa các thư mục Drowsy, Distracted, Normal sau khi gán
    OUTPUT_DIRECTORY = r"C:\Users\Kiet\Downloads\68cs2\học kì 6\Thị giác máy tính\DrowsinessDetection\data\merged_videos"
    
    # Tạo thư mục input nếu chưa có để tránh lỗi
    os.makedirs(INPUT_DIRECTORY, exist_ok=True)
    
    # Chạy tool
    label_videos(INPUT_DIRECTORY, OUTPUT_DIRECTORY)
