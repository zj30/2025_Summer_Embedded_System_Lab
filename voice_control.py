import json, queue, sys, time
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import RPi.GPIO as GPIO


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


# 前进或后退（大于零前进，小于零后退）
def goForward(speed):
    if(speed>=0):
        GPIO.output(BIN1,GPIO.LOW)
        GPIO.output(BIN2,GPIO.HIGH)
        pwmb.start(speed)
        time.sleep(0.02)
    else:
        GPIO.output(BIN2,GPIO.LOW)
        GPIO.output(BIN1,GPIO.HIGH)
        pwmb.start(-speed)
        time.sleep(0.02)

def motorStop():
    GPIO.output(BIN1,GPIO.LOW)
    GPIO.output(BIN2,GPIO.LOW)

GPIO.output(STBY,GPIO.HIGH)
# ===== 基本配置 =====
MODEL_PATH   = "./vosk-model-small-cn-0.22"
SAMPLE_RATE  = 16000
BLOCK_BYTES  = 4000
DEVICE_INDEX = None
LOOP_DURATION = 2.0  # 每次循环的时长(秒)
WAKE_WORD = "你好"  # 唤醒词

# 定义指令到数字的映射
COMMAND_MAPPING = {
    "关闭": 0,
    "低速": 1,
    "中速": 2,
    "高速": 3,
    "泥塑": 1,
    "东西": 2,
    "低": 1,
    "中": 2,
    "高": 3,
    "丰富": 2,
    "因素": 1
}

print("Loading model ...")
model = Model(MODEL_PATH)
rec = KaldiRecognizer(model, SAMPLE_RATE)
rec.SetWords(True)

audio_q = queue.Queue()

def audio_cb(indata, frames, t, status):
    if status:
        print("Audio status:", status, file=sys.stderr)
    audio_q.put(bytes(indata))

def detect_command(text, wake_word_detected):
    """检测文本中是否包含预定义指令"""
    # 如果唤醒词尚未检测到，先检查唤醒词
    if not wake_word_detected:
        if WAKE_WORD in text:
            print(f"\n检测到唤醒词: '{WAKE_WORD}'")
            return None, True  # 返回None表示没有指令，但唤醒词已检测到
    
    # 如果唤醒词已检测到，检查速度指令
    if wake_word_detected:
        for command, number in COMMAND_MAPPING.items():
            if command in text:
                print(f"\n检测到指令: '{command}' -> 输出: {number}")
                return number, True  # 返回指令数字，唤醒状态保持True
    
    return None, wake_word_detected  # 没有检测到指令，返回当前的唤醒状态

def main():
    # 创建并保持录音流开启
    stream = sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=0,
        device=DEVICE_INDEX,
        dtype="int16",
        channels=1,
        callback=audio_cb
    )
    stream.start()
    
    print(f"开始循环识别，每{LOOP_DURATION}秒进行一次识别")
    print(f"请先说唤醒词'{WAKE_WORD}'，然后说：关闭、低速、中速或高速")
    
    try:
        wake_word_detected = False  # 唤醒词检测状态
        
        while True:  # 无限循环
            final_lines = []
            partial_last = ""
            start_time = time.time()  # 记录本次循环开始时间
            detected_command = None  # 存储检测到的指令
            
            print(f"\n开始新的识别周期...")
            if wake_word_detected:
                print("当前状态: 已唤醒，等待指令")
            else:
                print("当前状态: 等待唤醒词")
            
            # 重置识别器状态
            rec.Reset()
            
            buf = b""
            try:
                while True:
                    # 检查是否达到本次循环时长
                    elapsed = time.time() - start_time
                    if elapsed >= LOOP_DURATION:
                        print(f"\n本次识别周期结束")
                        break
                    
                    # 显示剩余时间
                    remaining = max(0, LOOP_DURATION - elapsed)
                    print(f"剩余时间: {remaining:.1f}s", end="\r", flush=True)
                    
                    # 处理音频数据
                    data = audio_q.get()
                    buf += data
                    while len(buf) >= BLOCK_BYTES:
                        chunk = buf[:BLOCK_BYTES]
                        buf = buf[BLOCK_BYTES:]

                        if rec.AcceptWaveform(chunk):
                            # 处理最终识别结果
                            res = json.loads(rec.Result())
                            text = res.get("text", "").strip()
                            if text:
                                print("\n【最终】", text)
                                final_lines.append(text)
                                partial_last = ""
                                
                                # 检测指令或唤醒词
                                cmd, wake_word_detected = detect_command(text, wake_word_detected)
                                if cmd is not None:
                                    detected_command = cmd
                                    break  # 检测到指令，跳出内层循环
                        
                        else:
                            # 处理部分识别结果
                            pres = json.loads(rec.PartialResult())
                            p = pres.get("partial", "").strip()
                            if p and p != partial_last:
                                print("… " + p + "     ", end="\r", flush=True)
                                partial_last = p
                                
                                # 在部分结果中检测指令或唤醒词
                                cmd, wake_word_detected = detect_command(p, wake_word_detected)
                                if cmd is not None:
                                    detected_command = cmd
                                    break  # 检测到指令，跳出内层循环
                    
                    # 如果检测到指令，提前结束本次循环
                    if detected_command is not None:
                        print("检测到有效指令，提前结束本次识别")
                        break
                        
            finally:
                # 处理缓冲区剩余数据
                if len(buf) > 0:
                    rec.AcceptWaveform(buf)
                
                # 获取最终结果
                last = json.loads(rec.FinalResult()).get("text", "").strip()
                if last:
                    print("【最终】", last)
                    final_lines.append(last)
                    
                    # 最后尝试检测指令或唤醒词
                    cmd, wake_word_detected = detect_command(last, wake_word_detected)
                    if cmd is not None:
                        detected_command = cmd
                
                # 直接打印指令数字
                if detected_command is not None:
                    if detected_command == 0 :
                        motorStop()
                        time.sleep(0.02)
                    elif detected_command == 1 :
                        goForward(33)
                        time.sleep(0.02)
                    elif detected_command == 2 :
                        goForward(66)
                    elif detected_command == 3 :
                        goForward(100)
                else:
                    print("未检测到有效指令")
                    print("-1")  # 输出-1表示无效指令
                
                # 等待一小段时间，避免连续识别过于密集
                time.sleep(0.5)
                
    except KeyboardInterrupt:
        print("\n用户中断，收尾中…")
    finally:
        # 关闭录音流
        stream.stop()
        stream.close()
        print("录音流已关闭")

if __name__ == "__main__":
    main()
