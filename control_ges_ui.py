import os
import time
import threading  # 1. 导入线程模块
import tkinter as tk # 2. 导入Tkinter模块
import RPi.GPIO as GPIO
import cv2
import warnings 
import os



# 导入你提供的功能模块
from gesture_detector import get_gesture_from_frames 
from motor import goForward, motorStop

# --- 控制逻辑配置 ---
SPEED_MAPPING = {
    1: 33.3,
    2: 66.7,
    3: 100.0
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
pwmb = GPIO.PWM(PWMB,500)


# -------------------- UI界面类 --------------------
class StatusUI:
    def __init__(self, root):
        self.root = root
        self.root.title("风扇控制状态")
        self.root.geometry("1280x720") # 设置窗口大小

        # 创建一个 StringVar 来动态更新文本
        self.status_text = tk.StringVar()
        self.status_text.set("正在初始化...")

        # 创建一个 Label 控件来显示状态文本
        self.status_label = tk.Label(
            root, 
            textvariable=self.status_text,
            font=("Helvetica", 96), # 设置字体和大小
            pady=20, # 上下边距
            padx=20  # 左右边距
        )
        self.status_label.pack(expand=True) # 让Label自动填充窗口

    def update_status(self, text, color="black"):
        """一个线程安全的方法，用于从任何线程更新UI文本"""
        if self.root.winfo_exists(): # 检查窗口是否还存在
            self.status_text.set(text)
            self.status_label.config(fg=color)

    def schedule_shutdown(self):
        self.root.after(100, self.root.destroy)
# -------------------- 修改后的风扇控制逻辑 --------------------
def fan_control_logic_loop(ui_instance):
    """
    风扇控制逻辑主循环。
    现在它接收一个UI实例作为参数，以便更新UI。
    """
    print("后台控制逻辑已启动...")

    last_gesture = -1

    try:
        while True:
            current_gesture = get_gesture_from_frames()

            if current_gesture is not None and current_gesture != last_gesture:
                message = ""
                color = "black"

                if current_gesture == 0:
                    message = "风扇已关闭"
                    color = "red"
                    motorStop()
                elif current_gesture in SPEED_MAPPING:
                    speed = SPEED_MAPPING[current_gesture]
                    message = f"风扇 {current_gesture} 档 | 速度: {speed}"
                    color = "green"
                    goForward(speed)
                elif current_gesture == 5:
                    message = "检测到退出手势 (5)，程序正在关闭..."
                    color = "blue"
                    ui_instance.update_status(message, color)
                    print(f"逻辑层: {message}")
                    # ui_instance.schedule_shutdown()
                    break
                else:
                    message = f"手势 {current_gesture} 无对应操作"
                    color = "orange"
                
                # 更新UI界面而不是打印到终端
                ui_instance.update_status(message, color)
                # 同时也在终端打印一份日志
                print(f"逻辑层: {message}")
                
                last_gesture = current_gesture

            time.sleep(0.1)
    except Exception as e:
        print(f"控制逻辑线程出错: {e}")
    finally:
        print("逻辑层: 发出最终停止指令。")
        motorStop()
        ui_instance.update_status("程序已停止", "gray")

# -------------------- 程序主入口 --------------------
def main():
    # 1. 创建Tkinter主窗口
    root = tk.Tk()
    
    # 2. 创建UI实例
    app_ui = StatusUI(root)

    # 3. 创建并配置后台线程
    #    - target=fan_control_logic_loop: 线程要执行的函数
    #    - args=(app_ui,): 传递给函数的参数 (注意逗号不能少)
    #    - daemon=True: 设置为守护线程，当主程序退出时，此线程也会立即退出
    control_thread = threading.Thread(
        target=fan_control_logic_loop, 
        args=(app_ui,),
        daemon=True
    )

    # 4. 启动后台线程
    control_thread.start()

    # 5. 启动UI主循环 (这会阻塞主线程，直到窗口关闭)
    #    当窗口关闭时，因为control_thread是守护线程，整个程序会干净地退出
    root.mainloop()

if __name__ == "__main__":
    main()
