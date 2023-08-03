import sensor, image, time, pyb
import random
from pyb import UART
from pyb import LED
from pyb import Pin
threshold = [(75, 100, -128, 127, -128, 127)]
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 2000)
sensor.set_auto_whitebal(False)
sensor.set_brightness(-3)
clock = time.clock()
uart = UART(3,115200)
blue_led = pyb.LED(3)
send_len = 3
def send_data_to_msp(data1,data2):
    header = bytearray([0x2C, 0x12])
    data1_bytes = data1.to_bytes(2, 'big')
    data2_bytes = data2.to_bytes(2, 'big')
    footer = bytearray([0x5B])
    uart.write(header +  data1_bytes +data2_bytes+ footer)
def calculate_average_rgb(region):
    img = sensor.snapshot()
    r_total = 0
    g_total = 0
    b_total = 0
    for x, y in region:
        r, g, b = img.get_pixel(x, y)
        r_total += r
        g_total += g
        b_total += b
    num_pixels = len(region)
    r_avg = r_total // num_pixels
    g_avg = g_total // num_pixels
    b_avg = b_total // num_pixels
    return r_avg, g_avg, b_avg
ls_x=[]
ls_y=[]
while(True):
    clock.tick()
    img = sensor.snapshot()
    blob = img.find_blobs(threshold, margin=3)
    W = img.width()
    H = img.height()
    W_C = W/2
    H_C = H/2
    data1 = 230
    data2 = 250
    if blob:
        if len(blob) == 2 or len(blob) == 1:
            for b in blob:
#                print(b)
                if b[5]<315 and b[5] >10 and b[6]<200 and b[6]>10  :

                    img.draw_rectangle(b.rect(),color=(0,0,255),thickness=3)
                    X_0 = b.cx()-W_C
                    Y_0 = -(b.cy()-H_C )
                    R,G,B = calculate_average_rgb(b.min_corners())
                    print(X_0,Y_0)
                    if (R-G)>10:
                        print(b[4])
                        img.draw_cross(b[5], b[6],color = (255, 0, 0), size = 50)
                        ls_x.append(X_0)
                        ls_y.append(Y_0)

                    if (G-R)>10:
                        img.draw_cross(b[5], b[6],color = (0, 255, 0), size = 50)
                    if len(ls_x) == send_len:
                        print(random.randint(1,10))
                        X_send = int(sum(ls_x)/send_len)
                        Y_send = int(sum(ls_y)/send_len)
                        send_data_to_msp(X_send,Y_send)
                        blue_led.toggle()
                        ls_x=[]
                        ls_y=[]
    else:
        pass
