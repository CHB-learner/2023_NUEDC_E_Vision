import sensor, image, time, pyb
import random
from pyb import UART
from pyb import LED
from pyb import Pin

sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.skip_frames(time = 2000)
sensor.set_auto_whitebal(False)
sensor.set_brightness(-3)
#sensor.set_auto_exposure(False,500)
#sensor.set_auto_gain(False,gain_db=5) #增益

clock = time.clock()
uart = UART(3,115200)
blue_led = pyb.LED(3)


# 向msp432发送两个数值 data1,data2
def send_data_to_msp(data1,data2):
    header = bytearray([0x2C, 0x12])
    data1_bytes = data1.to_bytes(2, 'big')
    data2_bytes = data2.to_bytes(2, 'big')
    footer = bytearray([0x5B])
    uart.write(header +  data1_bytes +data2_bytes+ footer)

# 求区域内rgb通道平均值
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

# Q1.设置运动目标位置复位功能  返回 红色坐标点 距离图像原点的(△x,△y)
# Q1题变量
threshold = [(75, 100, -128, 127, -128, 127)] # 阈值
x_roi = 126
y_roi = 68
w = 150
h = 120
send_len = 3 # 每隔三个send一次
ls_x=[] # 红色激光点ls
ls_y=[] # 红色激光点ls
roi_blob = []

# Q2.红色光斑能在 30 秒内沿屏幕四周边线顺时针移动一周
# Q2题变量

# Q3.红色光斑能在30 秒内沿胶带顺时针移动一周。
# Q3题变量

# Q4.上述 A4 靶纸以任意旋转角度贴在屏幕任意位置。
# Q4题变量



#-------------------------------主循环---------------------------
while(True):
    clock.tick()
    img = sensor.snapshot()
    W = img.width()
    H = img.height()
    W_C = W/2
    H_C = H/2

    subscriber_mode = 1 # 默认为0，没收到指示~
    #--------在此写个串口接受函数，把收到的值赋值给subscriber_mode--------

    #----------------------------------------------------------------
    if subscriber_mode ==0:
        print("没收到指示~")


    # ---------------------------------------------------------
    # Q1.设置运动目标位置复位功能  返回 红色坐标点 距离 图像原点的(△x,△y)
    # ---------------------------------------------------------
    if subscriber_mode ==1:
        roi_blob = []
        blob = img.find_blobs(threshold, margin=10,) # LAB检测
        img.draw_rectangle(x_roi, y_roi, w, h, color = (0,0,255), thickness = 2, fill = False)
        if blob:
            for i in blob:
                if i[5]<(x_roi+w) and i[5] >x_roi and i[6]<(y_roi + h) and i[6]>y_roi:
                    roi_blob.append(i)
                    img.draw_rectangle(i.rect(),color=(0,0,255),thickness=3)

            print('len(blob):',len(blob))
            print('-------len(roi_blob):',len(roi_blob))
            blob = roi_blob
            # 考虑到发挥部分的影响，可能 2:(红+绿) 1:(红绿重合) 1:(只有红)
            if len(blob) == 2 : # 红、绿色激光均检测到，只返回红色激光的 (△x,△y)
                for b in blob: # 区分开红、绿激光点
                    # 设置一个ROI区域，待调整。。。。
                    if b[5]<(x_roi+w) and b[5] >x_roi and b[6]<(y_roi + h) and b[6]>y_roi:
                        X_0 = b.cx()-W_C
                        Y_0 = -(b.cy()-H_C )
                        R,G,B = calculate_average_rgb(b.min_corners())
                        if (R-G)>30: # 红色激光点
                            img.draw_cross(b[5], b[6],color = (255, 0, 0), size = 50)
                            ls_x.append(X_0)
                            ls_y.append(Y_0)
                            print("红色:",X_0,Y_0)
                        if (G-R)>30: # 绿色激光点
                            img.draw_cross(b[5], b[6],color = (0, 255, 0), size = 50)
                            print("绿色:",X_0,Y_0)
                        if len(ls_x) == send_len:
                            X_send = int(sum(ls_x)/send_len)
                            Y_send = int(sum(ls_y)/send_len)
                            send_data_to_msp(X_send,Y_send)
                            print("**************发送一次  红X:",X_send,'红Y:',Y_send)
                            blue_led.toggle()
                            ls_x=[]
                            ls_y=[]

            if len(blob) == 1 : # 红、绿色激光均检测到，只返回红色激光的 (△x,△y)
                b = blob[0]
                # 设置一个ROI区域，待调整。。。。
                if b[5]<(x_roi+w) and b[5] >x_roi and b[6]<(y_roi + h) and b[6]>y_roi:
                    X_0 = b.cx()-W_C
                    Y_0 = -(b.cy()-H_C )
                    R,G,B = calculate_average_rgb(b.min_corners())
                    if (R-G)>30: # 红色激光点
                        img.draw_cross(b[5], b[6],color = (255, 0, 0), size = 50)
                        ls_x.append(X_0)
                        ls_y.append(Y_0)
                        print("红色:",X_0,Y_0)
                    if (G-R)>30: # 绿色激光点
                        img.draw_cross(b[5], b[6],color = (0, 255, 0), size = 50)
                        print("绿色:",X_0,Y_0)
                    if len(ls_x) == send_len:
                        X_send = int(sum(ls_x)/send_len)
                        Y_send = int(sum(ls_y)/send_len)
                        send_data_to_msp(X_send,Y_send)
                        print("**************发送一次  红X:",X_send,'红Y:',Y_send)
                        blue_led.toggle()
                        ls_x=[]
                        ls_y=[]
            '''
            if len(blob) == 2 or len(blob) == 1:
                for b in blob:
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
                '''


    # ---------------------------------------------------------
    # Q2.红色光斑能在 30 秒内沿屏幕四周边线顺时针移动一周
    # ---------------------------------------------------------
    if subscriber_mode ==2:
        print("222")

    # ---------------------------------------------------------
    # Q3.红色光斑能在30 秒内沿胶带顺时针移动一周。
    # ---------------------------------------------------------
    if subscriber_mode ==3:
        print("333")

    # ---------------------------------------------------------
    # Q4.上述 A4 靶纸以任意旋转角度贴在屏幕任意位置。
    # ---------------------------------------------------------
    if subscriber_mode ==4:
        print("444")

    # ---------------------Finish---------------------


