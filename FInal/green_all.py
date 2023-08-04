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
    blue_led.toggle()  # OPENMV 闪灯

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

# 变量
threshold = [(65, 100, -128, 127, -128, 127)] # 阈值
x_roi = 135
y_roi = 75
w = 150
h = 120
send_len = 3 # 每隔三个send一次
ls_x=[] # 红色激光点ls
ls_y=[] # 红色激光点ls
roi_blob = []


ls_x_R=[]
ls_y_R=[]
ls_x_G=[]
ls_y_G=[]




#-------------------------------主循环---------------------------
while(True):
    # send_data_to_msp(12,24) 供测试串口通信
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
    # 运动跟踪 返回 绿色坐标点 距离 红色坐标点的(△x,△y)
    # ---------------------------------------------------------
    if subscriber_mode ==1:
        roi_blob = []
        blob = img.find_blobs(threshold, margin=5,) # LAB检测
        img.draw_rectangle(x_roi, y_roi, w, h, color = (0,0,255), thickness = 2, fill = False)
        if blob:
            print(len(blob))
            for i in blob: # 只在roi内做检测
                if i[5]<(x_roi+w) and i[5] >x_roi and i[6]<(y_roi + h) and i[6]>y_roi:
                    roi_blob.append(i)
                    img.draw_rectangle(i.rect(),color=(0,0,255),thickness=3)

            # print('len(blob):',len(blob))
            # print('-------len(roi_blob):',len(roi_blob))
            blob = roi_blob

            # 考虑到发挥部分的影响，可能 2:(红+绿) 1:(红绿重合) 1:(只有红)
            if len(blob) == 2 : # 红、绿色激光均检测到，只返回红色激光的 (△x,△y)
                for b in blob: # 区分开红、绿激光点

                    # 设置一个ROI区域，待调整。。。。
                    if b[5]<(x_roi+w) and b[5] >x_roi and b[6]<(y_roi + h) and b[6]>y_roi:
                        R,G,B = calculate_average_rgb(b.min_corners())
                        if (R-G)>10:
                            img.draw_cross(b[5], b[6],color = (255, 0, 0), size = 50)
                            X_R = b[5]
                            Y_R = b[6]
                            ls_x_R.append(X_R)
                            ls_y_R.append(Y_R)
                        if (G-R)>0:
                            img.draw_cross(b[5], b[6],color = (0, 255, 0), size = 50)
                            X_G = b[5]
                            Y_G = b[6]
                            ls_x_G.append(X_G)
                            ls_y_G.append(Y_G)
                        if len(ls_x_R) == send_len:
                            X_send = int(sum(ls_x_G)/send_len - sum(ls_x_R)/send_len)
                            Y_send = -int(sum(ls_y_G)/send_len - sum(ls_y_R)/send_len)
                            
                            send_data_to_msp(X_send,Y_send)
                            print('以红点为原点 △x:',X_send,',△y:',Y_send)

                            ls_x_R=[]
                            ls_y_R=[]
                            ls_x_G=[]
                            ls_y_G=[]

            if len(blob) == 1 : # 红、绿色激光均检测到，只返回红色激光的 (△x,△y)
                print("---------------重 合 了---------------")
                b = blob[0]
                send_data_to_msp(0,0)

    # ---------------------Finish---------------------


