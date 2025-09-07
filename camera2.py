import mediapipe as mp
import cv2
import numpy as np
import time
import math

mp_drawing = mp.solutions.drawing_utils 
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

# cap = cv2.VideoCapture('GesDet.mp4') # 视频路径
cap = cv2.VideoCapture(0) # 0 代表电脑自带的摄像头，1代表外接摄像头
# cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
# cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

gesture = [0,1,2,3,4,5]  # 预设数字

def ges(hand_landmarks):
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
        return 4 # 未知手势


with mp_hands.Hands(
    static_image_mode = False,  # False表示为视频流检测
    max_num_hands = 2,    # 最大可检测到两只手掌
    model_complexity = 0,  # 可设为0或者1，主要跟模型复杂度有关
    min_detection_confidence = 0.5,  # 最大检测阈值
    min_tracking_confidence = 0.5    # 最小追踪阈值
    ) as hands:
    while True: # 判断相机是否打开
        success ,image = cap.read()  # 返回两个值：一个表示状态，一个是图像矩阵
        if image is None:
            break
        image.flags.writeable = False # 将图像矩阵修改为仅读模式
        image = cv2.cvtColor(image,cv2.COLOR_BGR2RGB)
        t0 = time.time()
        results =hands.process(image) # 使用API处理图像图像
        '''
        results.multi_handedness
        包括label和score,label是字符串"Left"或"Right",score是置信度
        results.multi_hand_landmarks
        results.multi_hand_landmrks:被检测/跟踪的手的集合
        其中每只手被表示为21个手部地标的列表,每个地标由x、y和z组成。
        x和y分别由图像的宽度和高度归一化为[0.0,1.0]。Z表示地标深度
        以手腕深度为原点，值越小，地标离相机越近。 
        z的大小与x的大小大致相同。
        '''
        t1 = time.time()
        fps = 1 / (t1 - t0)  # 实时帧率
        # print('++++++++++++++fps',fps)
        image.flags.writeable = True  # 将图像矩阵修改为读写模式
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)  # 将图像变回BGR形式
        dict_handnumber = {}  # 创建一个字典。保存左右手的手势情况
        if results.multi_handedness: # 判断是否检测到手掌
            if len(results.multi_handedness) == 2:  # 如果检测到两只手
                for i in range(len(results.multi_handedness)):
                    label = results.multi_handedness[i].classification[0].label  # 获得Label判断是哪几手
                    index = results.multi_handedness[i].classification[0].index  # 获取左右手的索引号
                    hand_landmarks = results.multi_hand_landmarks[index]  # 根据相应的索引号获取xyz值
                    mp_drawing.draw_landmarks(
                                image,
                                hand_landmarks,
                                mp_hands.HAND_CONNECTIONS, #用于指定地标如何在图中连接。
                                mp_drawing_styles.get_default_hand_landmarks_style(),  # 如果设置为None.则不会在图上标出关键点
                                mp_drawing_styles.get_default_hand_connections_style())  # 关键点的连接风格
                    gesresult = ges(hand_landmarks) # 传入21个关键点集合，返回数字
                    dict_handnumber[label] = gesresult # 与对应的手进行保存为字典
            else: # 如果仅检测到一只手
                label = results.multi_handedness[0].classification[0].label  # 获得Label判断是哪几手
                hand_landmarks = results.multi_hand_landmarks[0]
                mp_drawing.draw_landmarks(
                            image,
                            hand_landmarks,
                            mp_hands.HAND_CONNECTIONS, #用于指定地标如何在图中连接。
                            mp_drawing_styles.get_default_hand_landmarks_style(),  # 如果设置为None.则不会在图上标出关键点
                            mp_drawing_styles.get_default_hand_connections_style())  # 关键点的连接风格
                gesresult = ges(hand_landmarks) # 传入21个关键点集合，返回数字
                dict_handnumber[label] = gesresult # 与对应的手进行保存为字典
        if len(dict_handnumber) == 2:  # 如果有两只手，则进入
            # print(dict_handnumber)
            leftnumber = dict_handnumber['Right']  
            rightnumber = dict_handnumber['Left']
            '''
            显示实时帧率，右手值，左手值，相加值
            '''
            s = 'FPS:{0}\nLefthand Value:{1}\nRighthand Value:{2}\nAdd is:{3}'.format(int(fps),rightnumber,leftnumber,str(leftnumber+rightnumber))  # 图像上的文字内容
        elif len(dict_handnumber) == 1 :  # 如果仅有一只手则进入
            labelvalue = list(dict_handnumber.keys())[0]  # 判断检测到的是哪只手
            if labelvalue == 'Left':  # 左手,不知为何，模型总是将左右手搞反，则引入人工代码纠正
                number = list(dict_handnumber.values())[0]
                s = 'FPS:{0}\nLefthand Value:{1}\nLefthand Value:0\nAdd is:{2}'.format(int(fps),number,number)
            else:  # 右手
                number = list(dict_handnumber.values())[0]
                s = 'FPS:{0}\nRighthand Value:{1}\nRighthand Value:0\nAdd is:{2}'.format(int(fps),number,number)
        else:# 如果没有检测到则只显示帧率
            s = 'FPS:{0}\n'.format(int(fps))
            
        y0,dy = 50,25  # 文字放置初始坐标
        image = cv2.flip(image,1) # 反转图像
        for i ,txt in enumerate(s.split('\n')): # 根据\n来竖向排列文字
            y = y0 + i*dy
            cv2.putText(image,txt,(50,y),cv2.FONT_HERSHEY_SIMPLEX,1,(255,0,0),3)
        cv2.imshow('MediaPipe Gesture Recognition',image)  # 显示图像
        # cv2.imwrite('save/{0}.jpg'.format(t1),image)
        if cv2.waitKey(5) & 0xFF == 27:
            break
    cap.release()
