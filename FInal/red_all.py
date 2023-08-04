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




# Q1.设置运动目标位置复位功能  返回 红色坐标点 距离图像原点的(△x,△y)
# Q1题变量
# 向msp432发送两个数值 data1,data2
def send_data_to_msp(data1,data2):
    header = bytearray([0x2C, 0x12])
    data1_bytes = data1.to_bytes(2, 'big')
    data2_bytes = data2.to_bytes(2, 'big')
    footer = bytearray([0x5B])
    uart.write(header +  data1_bytes +data2_bytes+ footer)
    print("串口发送:",data1,data2)

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
def send_data_to_msp_8(data1,data2,data3,data4,data5,data6,data7,data8):
    header = bytearray([0x2C, 0x12])
    data1_bytes = data1.to_bytes(1, 'big')
    data2_bytes = data2.to_bytes(1, 'big')
    data3_bytes = data3.to_bytes(1, 'big')
    data4_bytes = data4.to_bytes(1, 'big')
    data5_bytes = data5.to_bytes(1, 'big')
    data6_bytes = data6.to_bytes(1, 'big')
    data7_bytes = data7.to_bytes(1, 'big')
    data8_bytes = data8.to_bytes(1, 'big')
    footer = bytearray([0x5B])
    uart.write(header +  data1_bytes +data2_bytes +data3_bytes+data4_bytes +data5_bytes+data6_bytes +data7_bytes+data8_bytes+ footer)

    print("串口发送:",data1,data2,data3,data4,data5,data6,data7,data8)

def calculate_area(points):
    if len(points) != 4:
        return None

    # 获取矩形的左上角和右下角坐标
    x_coordinates = [point[0] for point in points]
    y_coordinates = [point[1] for point in points]
    min_x, max_x = min(x_coordinates), max(x_coordinates)
    min_y, max_y = min(y_coordinates), max(y_coordinates)

    # 计算矩形的边长
    width = abs(max_x - min_x)
    height = abs(max_y - min_y)

    # 计算矩形的面积
    area = width * height

    return area

def is_rectangle(points):
    # 获取角的余弦值
    def cosine(p1, p2, p3):
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3

        # 向量的点积
        dot_product = (x2 - x1) * (x3 - x2) + (y2 - y1) * (y3 - y2)

        # 向量的模
        length_ab = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        length_bc = ((x3 - x2) ** 2 + (y3 - y2) ** 2) ** 0.5

        # 计算余弦值
        if length_ab == 0 or length_bc == 0:
            return None
        else:
            return dot_product / (length_ab * length_bc)

    if len(points) != 4:
        return False

    # 计算四个角的余弦值
    cosines = []
    for i in range(4):
        p1 = points[i]
        p2 = points[(i + 1) % 4]
        p3 = points[(i + 2) % 4]
        cos_val = cosine(p1, p2, p3)
        if cos_val is None:
            return False
        cosines.append(cos_val)

    # 判断余弦值是否接近 0 或 1
    threshold = 0.1
    for cos_val in cosines:
        if abs(cos_val) > threshold and abs(cos_val - 1) > threshold:
            return False

    return True
def rec_avg(m):
    result_rec_avg = []
    for i in range(len(m[0])):
        column_sum = 0
        for row in m:
            column_sum += row[i]
        column_average = int(column_sum / len(m))
        result_rec_avg.append(column_average)

    return result_rec_avg
#    for i in range(len(m[0])):
#        result_rec_avg = []
#        for row in m:
#            column_values.append(row[i])
#        column_values.sort()
#        column_values = column_values[1:-1]  # 去除最大和最小值
#        column_average = int(sum(column_values) / len(column_values))
#        result_rec_avg.append(column_average)

#        return result_rec_avg


goal=()
area_min = 1000
rec_detec_times = 0
rec_detec_times_lim = 10
rec_final_ls = []

# red_x = 160 #红点坐标X
# red_y = 120 #红点坐标Y


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

    subscriber_mode = 0 # 默认为0，没收到指示~

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


    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # Q3.红色光斑能在30 秒内沿胶带顺时针移动一周。
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    if subscriber_mode ==3:
        # 下面的`threshold`应设置为足够高的值，以滤除在图像中检测到的具有
        # 低边缘幅度的噪声矩形。最适用与背景形成鲜明对比的矩形。
        # 识别矩形
        if rec_detec_times < rec_detec_times_lim:
            for r in img.find_rects(threshold = 10000):
                # 判断是否围成矩形
                is_rect = is_rectangle(r.corners())
                area = calculate_area(r.corners())
                if is_rect and area>area_min:
                    is_rect_flag = 1
                    goal = r.corners()
                    # print(goal)
                    #绘图展示
                    for i in range(len(goal)):
                        point = goal[i]
                        txt = str(i)
                        img.draw_string(point[0], point[1], txt, color = (0, 0, 255), scale = 2, mono_space = False,
                                        char_rotation = 0, char_hmirror = False, char_vflip = False,
                                        string_rotation = 0, string_hmirror = False, string_vflip = False)

                    #发送坐标 3、2、1、0
                    X_0_rec = int(goal[0][0])
                    Y_0_rec = int(goal[0][1] )

                    X_1 = int(goal[1][0])
                    Y_1 = int(goal[1][1])

                    X_2 = int(goal[2][0])
                    Y_2 = int(goal[2][1])

                    X_3 = int(goal[3][0])
                    Y_3 = int(goal[3][1])

                    # send_data_to_msp_8(X_3,Y_3,X_2,Y_2,X_1,Y_1,X_0,Y_0)
                    # print(X_3,Y_3,X_2,Y_2,X_1,Y_1,X_0,Y_0)
                    rec_detec_times = rec_detec_times + 1
                    rec_final_ls.append( [X_3,Y_3,X_2,Y_2,X_1,Y_1,X_0_rec,Y_0_rec])

                    img.draw_cross(X_3, Y_3,color = (0, 0, 255), size = 50)
                else:
                    pass


        # 识别红点 ***********************************************************
        roi_blob = []
        red_dected_flag = 0

        if rec_detec_times >= rec_detec_times_lim:
            blob = img.find_blobs(threshold, margin=10,) # LAB检测
            img.draw_rectangle(x_roi, y_roi, w, h, color = (0,0,255), thickness = 2, fill = False)
            if blob:
                for i in blob:
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
                            X_0 = b[5]
                            Y_0 = b[6]
                            R,G,B = calculate_average_rgb(b.min_corners())
                            if (R-G)>30: # 红色激光点
                                img.draw_cross(b[5], b[6],color = (255, 0, 0), size = 50)
                                ls_x.append(X_0)
                                ls_y.append(Y_0)
                                # print("红色:",X_0,Y_0)
                            if (G-R)>30: # 绿色激光点
                                img.draw_cross(b[5], b[6],color = (0, 255, 0), size = 50)
                                # print("绿色:",X_0,Y_0)
                            if len(ls_x) == send_len:
                                X_send = int(sum(ls_x)/send_len)
                                Y_send = int(sum(ls_y)/send_len)
                                red_x = X_send
                                red_y = Y_send

                                # send_data_to_msp(X_send,Y_send)
                                # print("**************发送一次  红X:",red_x,'红Y:',red_y)
                                blue_led.toggle()
                                ls_x=[]
                                ls_y=[]

                if len(blob) == 1 : # 红、绿色激光均检测到，只返回红色激光的 (△x,△y)
                    b = blob[0]
                    # 设置一个ROI区域，待调整。。。。
                    if b[5]<(x_roi+w) and b[5] >x_roi and b[6]<(y_roi + h) and b[6]>y_roi:
                        X_0 = b[5]
                        Y_0 = b[6]
                        R,G,B = calculate_average_rgb(b.min_corners())
                        if (R-G)>30: # 红色激光点
                            img.draw_cross(b[5], b[6],color = (255, 0, 0), size = 50)
                            ls_x.append(X_0)
                            ls_y.append(Y_0)
                            # print("红色:",X_0,Y_0)
                        if (G-R)>30: # 绿色激光点
                            img.draw_cross(b[5], b[6],color = (0, 255, 0), size = 50)
                            # print("绿色:",X_0,Y_0)
                        if len(ls_x) == send_len:
                            X_send = int(sum(ls_x)/send_len)
                            Y_send = int(sum(ls_y)/send_len)
                            red_x = X_send
                            red_y = Y_send
                            red_dected_flag = 1

                            # send_data_to_msp(X_send,Y_send)
                            # print("红X:",red_x,'红Y:',red_y)
                            blue_led.toggle()
                            ls_x=[]
                            ls_y=[]

        # 数据处理
        # (X_3,Y_3,X_2,Y_2,X_1,Y_1,X_0,Y_0) "红X:",red_x,'红Y:',red_y
        if rec_detec_times == rec_detec_times_lim:
            rec_detec_times = rec_detec_times + 1
            print(rec_final_ls)
            print(rec_avg(rec_final_ls))

        if red_dected_flag == 1: #识别到了红点
            # img.draw_arrow((red_x, red_y, X_3, Y_3), color = (0,0,255),size = 30, thickness = 2)
            img.draw_cross(X_3, Y_3, size=30, color=(0,0,255))

            print("---------红X:",red_x,'----------红Y:',red_y)
            red_relative_X = red_x - X_3
            red_relative_Y = red_y - Y_3

            Point_2_X = X_2 - X_3
            Point_2_Y = Y_2 - Y_3

            Point_1_X = X_1 - X_3
            Point_1_Y = Y_1 - Y_3

            Point_0_X = X_0_rec - X_3
            Point_0_Y = Y_0_rec - Y_3

            send_data_to_msp_8(red_relative_X,red_relative_Y, Point_2_X,Point_2_Y, Point_1_X,Point_1_Y, Point_0_X,Point_0_Y)
        else:
            pass
            # print()

    # ---------------------------------------------------------
    # Q4.上述 A4 靶纸以任意旋转角度贴在屏幕任意位置。
    # ---------------------------------------------------------
    if subscriber_mode ==4:
        print("444")
    # ---------------------Finish---------------------



