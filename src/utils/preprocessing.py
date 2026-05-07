import cv2
import numpy as np

def preprocess_frame(frame):
    """
    Tiền xử lý ảnh đầu vào để tối ưu hóa nhận diện khuôn mặt và trích xuất landmarks.
    Hàm này chuyển đổi ảnh sang xám, kiểm tra điều kiện thiếu sáng và áp dụng CLAHE.
    
    YÊU CẦU LÝ THUYẾT HỌC THUẬT:
    --------------------------
    Trong bài toán Computer Vision kinh điển (ví dụ như kiến trúc R-CNN), để giảm tải quá trình 
    tìm kiếm đối tượng trên toàn khung hình, người ta thường kết hợp thuật toán đề xuất vùng 
    ứng viên (Selective Search) và sau đó sử dụng RoI Pooling (Region of Interest Pooling) 
    để chuẩn hóa kích thước đặc trưng, đảm bảo tính bất biến về tỷ lệ (scale invariance) 
    trước khi đưa vào bộ phân loại.
    
    Trong hệ thống Real-time DMS hiện tại, chúng ta sử dụng mạng BlazeFace (tích hợp trong 
    MediaPipe) siêu nhẹ thay cho Selective Search truyền thống. Mặc dù cấu trúc khác nhau, 
    nhưng tư duy thiết kế cốt lõi về việc giới hạn không gian tính toán và trích xuất đặc trưng 
    (Feature Extraction) tối ưu vẫn được giữ nguyên.
    
    Việc cân bằng sáng cục bộ (CLAHE) ở bước này đóng vai trò sống còn trong việc tạo ra một 
    "bản đồ đặc trưng" (feature map) rõ nét nhất (chẳng hạn làm nổi bật viền mắt, vùng khóe miệng)
    trong điều kiện camera hồng ngoại ban đêm, giúp module AI xử lý hiệu quả.
    
    Quy trình:
    1. Chuyển ảnh sang Grayscale và tính cường độ sáng trung bình.
    2. Nếu pixel trung bình < 80 (thiếu sáng), áp dụng thuật toán CLAHE trên kênh L (Lightness)
       của không gian màu LAB.
    3. Chuyển ngược lại về RGB để phù hợp với input của MediaPipe.
    """
    # 1. Tính toán độ sáng trung bình trên ảnh xám
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    avg_brightness = np.mean(gray)
    
    # Mặc định chuẩn bị ảnh hệ màu RGB cho MediaPipe
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # 2. Kiểm tra điều kiện thiếu sáng (Ngưỡng trung bình < 80)
    if avg_brightness < 80:
        # Chuyển ảnh BGR nguyên bản sang không gian màu LAB
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        
        # Áp dụng CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # Giới hạn độ tương phản để tránh làm nhiễu hình ảnh
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l_channel)
        
        # Gộp các kênh lại sau khi đã cân bằng độ sáng trên kênh L
        merged_lab = cv2.merge((cl, a_channel, b_channel))
        
        # 3. Chuyển đổi lại về RGB để cung cấp cho MediaPipe FaceMesh
        rgb_frame = cv2.cvtColor(merged_lab, cv2.COLOR_LAB2RGB)
        
    return rgb_frame, avg_brightness
