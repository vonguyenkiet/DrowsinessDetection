import numpy as np

def calculate_euclidean_distance(p1, p2):
    """
    Tính khoảng cách Euclidean giữa 2 điểm.
    p1, p2: Tuple hoặc List (x, y) - đã giải chuẩn hóa
    """
    return np.linalg.norm(np.array(p1) - np.array(p2))

def calculate_ear(eye_landmarks, frame_width, frame_height):
    """
    Tính chỉ số EAR (Eye Aspect Ratio).
    eye_landmarks: List 6 điểm mốc của mắt (đối tượng có thuộc tính x, y từ MediaPipe).
    frame_width, frame_height: Kích thước thực tế của frame để giải chuẩn hóa.
    """
    # 1. Giải chuẩn hóa tọa độ (nhân với width/height)
    pts = []
    for lm in eye_landmarks:
        x = int(lm.x * frame_width)
        y = int(lm.y * frame_height)
        pts.append((x, y))
        
    # 2. Tính toán các khoảng cách
    # pt0: góc ngoài, pt3: góc trong
    # pt1, pt5: trên dưới bên ngoài
    # pt2, pt4: trên dưới bên trong
    
    # Khoảng cách dọc
    v1 = calculate_euclidean_distance(pts[1], pts[5])
    v2 = calculate_euclidean_distance(pts[2], pts[4])
    
    # Khoảng cách ngang
    h = calculate_euclidean_distance(pts[0], pts[3])
    
    # Tránh chia cho 0
    if h == 0:
        return 0.0
        
    # Công thức EAR
    ear = (v1 + v2) / (2.0 * h)
    return ear

def calculate_mar(mouth_landmarks, frame_width, frame_height):
    """
    Tính chỉ số MAR (Mouth Aspect Ratio) dùng 8 điểm mốc vùng môi.
    mouth_landmarks: List 8 điểm mốc vùng môi.
    frame_width, frame_height: Kích thước thực tế của frame để giải chuẩn hóa.
    """
    # 1. Giải chuẩn hóa tọa độ
    pts = []
    for lm in mouth_landmarks:
        x = int(lm.x * frame_width)
        y = int(lm.y * frame_height)
        pts.append((x, y))
        
    # Điểm 0 và 4 là khoé miệng trái và phải (chiều ngang)
    # Các cặp 1-7, 2-6, 3-5 là các cặp điểm môi trên-dưới (chiều dọc)
    
    # Khoảng cách dọc
    v1 = calculate_euclidean_distance(pts[1], pts[7])
    v2 = calculate_euclidean_distance(pts[2], pts[6])
    v3 = calculate_euclidean_distance(pts[3], pts[5])
    
    # Khoảng cách ngang
    h = calculate_euclidean_distance(pts[0], pts[4])
    
    # Tránh chia cho 0
    if h == 0:
        return 0.0
        
    # Công thức MAR (dùng 8 điểm)
    mar = (v1 + v2 + v3) / (2.0 * h)
    return mar
