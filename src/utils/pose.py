import cv2
import numpy as np

def get_head_pose(landmarks, frame_width, frame_height):
    """
    Tính 3 góc xoay (Pitch, Yaw, Roll) của đầu bằng cv2.solvePnP.
    landmarks: Danh sách tất cả 468 điểm mốc từ MediaPipe FaceMesh.
    frame_width, frame_height: Kích thước thật của ảnh để giải chuẩn hóa và tạo camera matrix.
    """
    # 1. Khai báo 6 điểm 3D chuẩn trên khuôn mặt người (Generic 3D face model)
    # Thứ tự: Mũi, Cằm, Mắt trái, Mắt phải, Mép trái, Mép phải
    face_3d = np.array([
        [0.0, 0.0, 0.0],            # 1. Mũi
        [0.0, -330.0, -65.0],       # 2. Cằm
        [-225.0, 170.0, -135.0],    # 3. Mắt trái
        [225.0, 170.0, -135.0],     # 4. Mắt phải
        [-150.0, -150.0, -125.0],   # 5. Mép trái
        [150.0, -150.0, -125.0]     # 6. Mép phải
    ], dtype=np.float64)

    # 2. Lấy 6 điểm 2D tương ứng từ MediaPipe Landmarks
    # Các index tương ứng:
    # 1: Mũi chóp
    # 152: Điểm thấp nhất cằm
    # 226: Mắt trái (góc trong)
    # 446: Mắt phải (góc trong)
    # 57: Mép miệng trái
    # 287: Mép miệng phải
    pose_indices = [1, 152, 226, 446, 57, 287]
    face_2d = []
    
    for idx in pose_indices:
        lm = landmarks[idx]
        # Giải chuẩn hóa: nhân với width và height
        x, y = int(lm.x * frame_width), int(lm.y * frame_height)
        face_2d.append([x, y])
        
    face_2d = np.array(face_2d, dtype=np.float64)

    # 3. Khởi tạo Camera Matrix giả định
    focal_length = frame_width
    center = (frame_width / 2, frame_height / 2)
    
    cam_matrix = np.array([
        [focal_length, 0, center[0]],
        [0, focal_length, center[1]],
        [0, 0, 1]
    ], dtype=np.float64)

    # Hệ số méo (Distortion matrix) giả định là 0
    dist_matrix = np.zeros((4, 1), dtype=np.float64)

    # 4. Tính toán pose bằng solvePnP
    success, rot_vec, trans_vec = cv2.solvePnP(face_3d, face_2d, cam_matrix, dist_matrix)
    
    if not success:
        return 0.0, 0.0, 0.0

    # 5. Chuyển đổi Rotation Vector sang Rotation Matrix
    rmat, _ = cv2.Rodrigues(rot_vec)
    
    # Lấy các góc Euler bằng RQDecomp3x3
    angles, mtxR, mtxQ, Qx, Qy, Qz = cv2.RQDecomp3x3(rmat)
    
    # 6. Lấy giá trị Pitch, Yaw, Roll (đã được RQDecomp3x3 trả về theo độ)
    # Xoay quanh trục X (Pitch) - Cúi/Ngẩng
    pitch = angles[0]
    # Chuẩn hóa để tránh lật trục 180 độ (Gimbal lock / Reverted Axis)
    if pitch > 90:
        pitch -= 180
    elif pitch < -90:
        pitch += 180
        
    # Xoay quanh trục Y (Yaw) - Quay Trái/Phải
    yaw = angles[1]
    if yaw > 90:
        yaw -= 180
    elif yaw < -90:
        yaw += 180
        
    # Xoay quanh trục Z (Roll) - Nghiêng đầu
    roll = angles[2]
    if roll > 90:
        roll -= 180
    elif roll < -90:
        roll += 180
    
    return pitch, yaw, roll
