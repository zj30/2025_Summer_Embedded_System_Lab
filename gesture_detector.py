import mediapipe as mp
import cv2
import numpy as np
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

mp_hands = mp.solutions.hands

def get_gesture_from_frames():
    """
    从摄像头捕获5帧图像，处理并检测手势，返回伸出的手指数量（0-5）。
    如果未检测到有效手势，返回-1。
    """
    # 初始化摄像头
    cap = cv2.VideoCapture(0)  # 使用默认摄像头
    if not cap.isOpened():
        print("错误：无法打开摄像头。")
        return -1

    # 初始化 MediaPipe Hands
    with mp_hands.Hands(
        static_image_mode=False,  # 设置为视频流检测
        max_num_hands=2,  # 最多检测两只手
        model_complexity=0,  # 模型复杂度设置为0
        min_detection_confidence=0.5,  # 最小检测置信度
        min_tracking_confidence=0.5  # 最小跟踪置信度
    ) as hands:
        frame_count = 0  # 帧计数器
        max_frames = 20  # 最大帧数
        last_gesture = -1  # 默认返回值，未检测到手势时返回-1

        while frame_count < max_frames:
            success, image = cap.read()  # 读取一帧图像
            if not success or image is None:
                print(f"警告：无法捕获第 {frame_count + 1} 帧")
                frame_count += 1
                continue

            # 处理图像
            image.flags.writeable = False  # 设置图像为只读模式
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # 转换为RGB格式
            results = hands.process(image)  # 使用 MediaPipe 处理图像
            image.flags.writeable = True  # 恢复图像为读写模式

            # 检查是否检测到手
            if results.multi_handedness and results.multi_hand_landmarks:
                # 获取第一只检测到的手的关键点
                hand_landmarks = results.multi_hand_landmarks[0]
                gesture = count_fingers(hand_landmarks)  # 计算伸出的手指数量
                if gesture in range(6):  # 确保手势有效（0-5）
                    last_gesture = gesture

            frame_count += 1

    # 释放摄像头
    cap.release()
    return last_gesture

def count_fingers(hand_landmarks):
    """
    根据手部关键点坐标识别手势。
    通过比较关键点的Y坐标来判断手指是否伸直。
    在图像坐标系中，Y值越小表示位置越靠上。
    
    参数:
        hand_landmarks: MediaPipe检测到的单只手的关键点列表。
    返回:
        一个代表手势名称的字符串。
    """
    # 获取各个手指尖端的Y坐标
    # .landmark[i] 是旧版API获取关键点的方式
    thumb_tip_y = hand_landmarks.landmark[4].y
    index_tip_y = hand_landmarks.landmark[8].y
    middle_tip_y = hand_landmarks.landmark[12].y
    ring_tip_y = hand_landmarks.landmark[16].y
    pinky_tip_y = hand_landmarks.landmark[20].y

    # 获取各个手指中间关节(PIP)的Y坐标
    index_pip_y = hand_landmarks.landmark[6].y
    middle_pip_y = hand_landmarks.landmark[10].y
    ring_pip_y = hand_landmarks.landmark[14].y
    pinky_pip_y = hand_landmarks.landmark[18].y
    
    # 获取各个手指根部关节(MCP)的Y坐标
    index_mcp_y = hand_landmarks.landmark[5].y
    middle_mcp_y = hand_landmarks.landmark[9].y
    ring_mcp_y = hand_landmarks.landmark[13].y
    pinky_mcp_y = hand_landmarks.landmark[17].y

    # --- 手指伸直状态判断 ---
    # 如果指尖的Y坐标小于(高于)中间关节的Y坐标，则认为手指是伸直的
    is_index_up = index_tip_y < index_pip_y
    is_middle_up = middle_tip_y < middle_pip_y
    is_ring_up = ring_tip_y < ring_pip_y
    is_pinky_up = pinky_tip_y < pinky_pip_y
    
    # --- 握拳状态判断 ---
    # 如果所有指尖的Y坐标都大于(低于)它们根部关节的Y坐标，则认为是握拳
    is_fist = (index_tip_y > index_mcp_y and
               middle_tip_y > middle_mcp_y and
               ring_tip_y > ring_mcp_y and
               pinky_tip_y > pinky_mcp_y)

    # --- 根据手指状态返回手势名称 ---
    if is_fist:
        return 0 # 握拳
    elif is_index_up and is_middle_up and is_ring_up and is_pinky_up:
        return 5 # 张开手掌
    elif not is_index_up and not is_middle_up and not is_ring_up and not is_pinky_up:
        return 5 # 另一种握拳的判断
    elif is_index_up and not is_middle_up and not is_ring_up and not is_pinky_up:
        return 1 # 手势 "一"
    elif is_index_up and is_middle_up and not is_ring_up and not is_pinky_up:
        return 2 # 手势 "二"
    elif is_index_up and is_middle_up and is_ring_up and not is_pinky_up:
        return 3 # 手势 "三"
    else:
        return -1 # 未知手势
    
num = get_gesture_from_frames()
print(num)

