import image
import lcd
import sensor
import sys
import time
import utime
import KPU as kpu
from fpioa_manager import *

import KPU as kpu

#
# Constants
#
time_playing_ms = 30000
labels = ["1", "2", "3", "4"]
path_model = "/sd/mbnet10_quant.kmodel"

#
# Initialize
#
lcd.init()
lcd.rotation(2)

try:
    from pmu import axp192
    pmu = axp192()
    pmu.enablePMICSleepMode(True)
except:
    pass

try:
    img = image.Image("/sd/startup.jpg")
    lcd.display(img)
except:
    lcd.draw_string(lcd.width()//2-100,lcd.height()//2-4, "Error: Cannot find start.jpg", lcd.WHITE, lcd.RED)


task = kpu.load(path_model)

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.set_windowing((224, 224))
sensor.run(1)

lcd.clear()

fm.register(board_info.BUTTON_A, fm.fpioa.GPIO1)
gpio_button_a = GPIO(GPIO.GPIO1, GPIO.IN, GPIO.PULL_UP)

fm.register(board_info.BUTTON_B, fm.fpioa.GPIO2)
gpio_button_b = GPIO(GPIO.GPIO2, GPIO.IN, GPIO.PULL_UP)

#
# Main routine
#
time_start_ms = utime.ticks_ms()
score = 0
target = 0
prev_button_a_pressed = False

while(True):
    # Input
    button_a_pressed = (gpio_button_a.value() == 0)
    button_b_pressed = (gpio_button_b.value() == 0)

    button_a_triggered = not prev_button_a_pressed and button_a_pressed
    prev_button_a_pressed = button_a_pressed

    if button_b_pressed:
        score = 0

    # Time
    time_now_ms = utime.ticks_ms()
    if button_b_pressed:
        time_start_ms = time_now_ms

    disp_time = (time_start_ms + time_playing_ms - time_now_ms) / 1000
    if disp_time < 0:
        disp_time = 0

    # Get image and recognition
    img = sensor.snapshot()

    fmap = kpu.forward(task, img)
    plist=fmap[:]
    pmax=max(plist)
    recognized_target = plist.index(pmax)
    is_recognized = pmax > 0.9

    if button_a_triggered and disp_time > 0:
        if is_recognized and recognized_target == target:
            score += 1
        else:
            score -= 1
        if score < 0:
            score = 0
        target = time_now_ms % len(labels)

    # Draw
    img.draw_rectangle(0, 50, 320, 1, color=(0, 144, 255), thickness=10)
    img.draw_string(10, 45, "Time:%d" % (disp_time), color=(255, 255, 255), scale=1)
    img.draw_string(120, 45, "Score:%d" % (score), color=(255, 255, 255), scale=1)
    img.draw_rectangle(0, 175, 320, 1, color=(0, 144, 255), thickness=10)
    img.draw_string(10, 170, "Search %s and press A" % (labels[target]), color=(255, 255, 255), scale=1)

    lcd.display(img)
    if is_recognized:
        lcd.draw_string(40, 60, " Recog:%s (accu:%.2f)"%(labels[recognized_target].strip(), pmax))

#
# Finalize
#
kpu.deinit(task)
