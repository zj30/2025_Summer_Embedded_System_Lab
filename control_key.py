import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)

button_pin = 17

GPIO.setup(button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

STBY = 27
PWMB = 19
BIN1 = 23
BIN2 = 24

GPIO.setup(STBY, GPIO.OUT)
GPIO.setup(PWMB, GPIO.OUT)
GPIO.setup(BIN1, GPIO.OUT)
GPIO.setup(BIN2, GPIO.OUT)
pwmb = GPIO.PWM(PWMB,500)

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

counter = 0
print("start!")
print("press CTRL+C to close!")

try:
    while True:

        if GPIO.input(button_pin) == GPIO.LOW:
            print(counter)
            
            if counter == 0 :
                motorStop()
                time.sleep(0.02)
            elif counter == 1 :
                goForward(33)
                time.sleep(0.02)
            elif counter == 2 :
                goForward(67)
            elif counter == 3 :
                goForward(100)
            
            counter = (counter + 1) % 4
            
            
            while GPIO.input(button_pin) == GPIO.LOW:
                time.sleep(0.01) 


except KeyboardInterrupt:
    print("down!")


finally:
    GPIO.cleanup()
