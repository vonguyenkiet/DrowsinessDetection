import os
import cv2
import sys
import numpy as np
import mediapipe as mp
import random

"""
MODULE: THRESHOLD TUNING (Tự động tinh chỉnh ngưỡng sinh trắc)
--------------------------------------------------------------
Mục đích: Khắc phục nhược điểm "Hard-coded Thresholds" (Ngưỡng cứng) bằng cách học ngưỡng từ dữ liệu thực tế (Data-driven).

Cơ sở lý thuyết:
1. Trích xuất đặc trưng (Feature Extraction): Sử dụng kỹ thuật Frame Skipping (nhảy cóc khung hình) để giảm thiểu tính toán thừa 
   trên các frame lân cận có độ tương đồng cao, sau đó dùng FaceMesh tính EAR, MAR, Pose cho mỗi nhóm nhãn.
2. Phương pháp Thống kê (Statistical Approach):
   - EAR / MAR: Sử dụng phép tính Trung bình cộng (Mean) giữa giá trị của trạng thái Bình thường (Normal) và Buồn ngủ (Drowsy) 
     để tìm ra điểm cắt (Decision Boundary) tối ưu nhất.
   - Head Pose: Dùng thuật toán Phân vị (Percentile) thứ 10 để loại bỏ nhiễu nhiễu ngoại lai (Outliers). Phân vị thứ 10 nghĩa là 
     chấp nhận sai số 10% ở nhóm Distracted để hệ thống không quá nhạy cảm, tránh False Positives.
"""

# Đảm bảo đường dẫn import tương đối
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.utils.geometry import calculate_ear, calculate_mar
from src.utils.pose import get_head_pose
from src.utils.preprocessing import preprocess_frame

def extract_features(video_path, face_mesh):
    """Trích xuất mảng các giá trị sinh trắc từ một video."""
    cap = cv2.VideoCapture(video_path)
    ears, mars, pitches, yaws = [], [], [], []
    
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        # Trích xuất 1 frame mỗi 3 frame để tối ưu tốc độ (nhảy cóc frame)
        if frame_count % 3 != 0:
            continue
            
        rgb_frame, _ = preprocess_frame(frame)
        results = face_mesh.process(rgb_frame)
        
        h, w, _ = frame.shape
        if results.multi_face_landmarks:
            landmarks = results.multi_face_landmarks[0].landmark
            
            # EAR
            left_eye = [landmarks[i] for i in [362, 385, 387, 263, 373, 380]]
            right_eye = [landmarks[i] for i in [33, 160, 158, 133, 153, 144]]
            ear = (calculate_ear(left_eye, w, h) + calculate_ear(right_eye, w, h)) / 2.0
            ears.append(ear)
            
            # MAR
            mouth = [landmarks[i] for i in [61, 81, 13, 311, 291, 402, 14, 178]]
            mar = calculate_mar(mouth, w, h)
            mars.append(mar)
            
            # Pose
            pitch, yaw, _ = get_head_pose(landmarks, w, h)
            pitches.append(pitch)
            yaws.append(yaw)
            
    cap.release()
    return ears, mars, pitches, yaws

def auto_tune_thresholds(data_dir):
    print(f"🔍 Bắt đầu phân tích dữ liệu từ: {data_dir}")
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )
    
    classes = ["Normal", "Drowsy", "Distracted"]
    features = {c: {"ear": [], "mar": [], "pitch": [], "yaw": []} for c in classes}
    
    # 1. Trích xuất đặc trưng
    for c in classes:
        folder = os.path.join(data_dir, c)
        if not os.path.exists(folder):
            print(f"⚠️ Cảnh báo: Không tìm thấy thư mục {folder}")
            continue
            
        videos = [f for f in os.listdir(folder) if f.lower().endswith(('.mp4', '.avi', '.mov'))]
        if not videos:
            print(f"⚠️ Cảnh báo: Không có video nào trong {folder}")
            continue
            
        print(f"▶ Đang xử lý tập {c} (Tổng cộng {len(videos)} video)...", flush=True)
        for i, video in enumerate(videos):
            if i % 10 == 0 or i == len(videos) - 1:
                print(f"  + Đang xử lý video {i+1}/{len(videos)}...", flush=True)
            path = os.path.join(folder, video)
            ears, mars, pitches, yaws = extract_features(path, face_mesh)
            features[c]["ear"].extend(ears)
            features[c]["mar"].extend(mars)
            features[c]["pitch"].extend(pitches)
            features[c]["yaw"].extend(yaws)
            
    face_mesh.close()
    
    # --- XUẤT FILE CSV ĐỂ THEO DÕI ---
    import csv
    csv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../threshold_features15s.csv'))
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Label", "EAR", "MAR", "Pitch", "Yaw"])
        for c in classes:
            # Gộp dữ liệu từng frame lại thành hàng ngang
            for e, m, p, y in zip(features[c]["ear"], features[c]["mar"], features[c]["pitch"], features[c]["yaw"]):
                writer.writerow([c, f"{e:.4f}", f"{m:.4f}", f"{p:.2f}", f"{y:.2f}"])
    print(f"\n💾 Đã lưu toàn bộ dữ liệu thô ra file CSV để theo dõi: {csv_path}")
    
    # 2. Tính toán ngưỡng tối ưu (Threshold Tuning)
    print("\n📊 --- KẾT QUẢ PHÂN TÍCH VÀ CẬP NHẬT NGƯỠNG ---")
    
    # EAR Threshold: Điểm chính giữa (Mean) của Normal và Drowsy
    normal_ear_mean = np.mean(features["Normal"]["ear"]) if features["Normal"]["ear"] else 0.3
    drowsy_ear_mean = np.mean(features["Drowsy"]["ear"]) if features["Drowsy"]["ear"] else 0.15
    ear_thresh = (normal_ear_mean + drowsy_ear_mean) / 2.0
    
    if np.isnan(ear_thresh): ear_thresh = 0.25
    
    # MAR Threshold: Điểm chính giữa (Mean) của Normal và Drowsy (hành vi ngáp)
    normal_mar_mean = np.mean(features["Normal"]["mar"]) if features["Normal"]["mar"] else 0.1
    drowsy_mar_mean = np.mean(features["Drowsy"]["mar"]) if features["Drowsy"]["mar"] else 0.6
    mar_thresh = (normal_mar_mean + drowsy_mar_mean) / 2.0
    if np.isnan(mar_thresh): mar_thresh = 0.5

    # Pose Threshold: Lấy phân vị thứ 10 (10th percentile)
    distracted_pitches = np.abs(features["Distracted"]["pitch"])
    distracted_yaws = np.abs(features["Distracted"]["yaw"])
    
    if len(distracted_pitches) > 0:
        pitch_thresh = np.percentile(distracted_pitches, 10)
    else:
        pitch_thresh = 20.0
        
    if len(distracted_yaws) > 0:
        yaw_thresh = np.percentile(distracted_yaws, 10)
    else:
        yaw_thresh = 30.0

    print(f"EAR Mới: {ear_thresh:.3f} (Tính từ Normal: {normal_ear_mean:.3f}, Drowsy: {drowsy_ear_mean:.3f})")
    print(f"MAR Mới: {mar_thresh:.3f} (Tính từ Normal: {normal_mar_mean:.3f}, Drowsy: {drowsy_mar_mean:.3f})")
    print(f"Pitch Mới: {pitch_thresh:.1f} độ")
    print(f"Yaw Mới: {yaw_thresh:.1f} độ")
    
    # 3. Ghi đè vào settings.py
    settings_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../config/settings.py'))
    with open(settings_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    import re
    content = re.sub(r'EAR_THRESHOLD\s*=\s*[\d.]+', f'EAR_THRESHOLD = {ear_thresh:.3f}', content)
    content = re.sub(r'MAR_THRESHOLD\s*=\s*[\d.]+', f'MAR_THRESHOLD = {mar_thresh:.3f}', content)
    content = re.sub(r'PITCH_THRESHOLD\s*=\s*[\d.]+', f'PITCH_THRESHOLD = {pitch_thresh:.1f}', content)
    content = re.sub(r'YAW_THRESHOLD\s*=\s*[\d.]+', f'YAW_THRESHOLD = {yaw_thresh:.1f}', content)
    
    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"\n✅ [THÀNH CÔNG] Đã tự động cập nhật các ngưỡng mới nhất vào file: {settings_path}")

if __name__ == "__main__":
    # Trỏ đúng đến thư mục data chứa merged_videos (15 giây)
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../data/merged_videos'))
    # Đặt fixed seed để kết quả ổn định qua các lần run
    random.seed(42)
    auto_tune_thresholds(data_dir)
