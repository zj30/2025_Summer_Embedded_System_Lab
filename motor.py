#motorTest.py
#导入 GPIO库
import RPi.GPIO as GPIO
import time

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
pwmb = GPIO.PWM(PWMB, 500)


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

motorStop()

pwmb.stop()
GPIO.cleanup()

