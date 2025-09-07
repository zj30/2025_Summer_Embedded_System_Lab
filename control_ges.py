import time
import RPi.GPIO as GPIO
import cv2
import warnings 
import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
warnings.filterwarnings('ignore') 

# 导入你提供的功能模块
# get_gesture_from_frames() 函数现在被假定会自行处理图像采集并返回一个数字
from gesture_detector import get_gesture_from_frames
# goForward() 和 motorStop() 函数负责所有底层硬件操作
from motor import goForward, motorStop

# --- 控制逻辑配置 ---
# 定义手势档位到电机速度的映射关系
# 这是主控程序的核心逻辑部分
SPEED_MAPPING = {
    1: 33,   # 1档速度
    2: 67,   # 2档速度
    3: 100,   # 3档速度
}

# --- yin jiao pei zhi ---
#设置 GPIO 模式为 BCM
GPIO.setmode(GPIO.BCM)

#定义引脚
STBY = 27
PWMB = 19
BIN1 = 23
BIN2 = 24

#设置 GPIO 的工作方式
GPIO.setup(STBY, GPIO.OUT)
GPIO.setup(PWMB, GPIO.OUT)
GPIO.setup(BIN1, GPIO.OUT)
GPIO.setup(BIN2, GPIO.OUT)
pwmb = GPIO.PWM(PWMB,300)


def fan_control_logic_loop():
    """
    风扇控制逻辑主循环。
    这个函数只负责“控制”，不涉及任何具体的实现细节。
    """
    print("风扇控制逻辑已启动...")
    print("按 Ctrl+C 退出程序。")

    # 用于存储上一个手势状态，避免重复发送相同的指令
    last_gesture = -1  # -1 代表初始未知状态

    try:
        while True:
            # 1. 从手势识别模块获取当前状态
            # 我们直接调用函数，并相信它会返回一个 0-5 的数字
            current_gesture = get_gesture_from_frames()

            # 2. 检查状态是否发生变化
            if current_gesture is not None and current_gesture != last_gesture:
                
                print(f"逻辑层: 检测到状态变化，新手势: {current_gesture}")

                # 3. 根据新状态，决定并发出指令
                if current_gesture == 0:
                    print("逻辑层: 指令 -> 停止电机")
                    motorStop()
                elif current_gesture in SPEED_MAPPING:
                    speed = SPEED_MAPPING[current_gesture]
                    print(f"逻辑层: 指令 -> 设置速度为 {speed} (对应档位 {current_gesture})")
                    goForward(speed)
                else:
                    # 对于未定义的手势（如5），逻辑层决定不发出任何指令
                    print(f"逻辑层: 手势 {current_gesture} 无对应指令，已忽略。")
                
                # 4. 更新当前状态记录
                last_gesture = current_gesture

            # 控制循环的频率，避免CPU占用过高
            time.sleep(0.2)  # 每0.1秒查询一次手势状态

    except KeyboardInterrupt:
        # 优雅地处理退出
        print("\n程序被中断。正在执行清理...")
    finally:
        # 无论如何退出，都确保风扇停止，保证安全
        print("逻辑层: 发出最终停止指令。")
        motorStop()
        print("程序已安全退出。")

# --- 程序入口 ---
if __name__ == '__main__':
    # 启动控制逻辑循环
    fan_control_logic_loop()
