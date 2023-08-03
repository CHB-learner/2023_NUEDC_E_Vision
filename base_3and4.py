import sensor, image, time
from pyb import UART

sensor.reset()
sensor.set_pixformat(sensor.RGB565) # 灰度更快(160x120 max on OpenMV-M7)
sensor.set_framesize(sensor.QQVGA)
sensor.skip_frames(time = 2000)
clock = time.clock()
uart = UART(3,115200)


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




goal=()
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


while(True):
    clock.tick()
    img = sensor.snapshot()
    W = img.width()
    H = img.height()
    W_C = W/2
    H_C = H/2

    # 下面的`threshold`应设置为足够高的值，以滤除在图像中检测到的具有
    # 低边缘幅度的噪声矩形。最适用与背景形成鲜明对比的矩形。

    for r in img.find_rects(threshold = 10000):
        # 判断是否围成矩形
        is_rect = is_rectangle(r.corners())
        area = calculate_area(r.corners())
        if is_rect and area>1000:
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
            X_0 = int(goal[0][0]-W_C)
            Y_0 = int(-(goal[0][1]-H_C ))

            X_1 = int(goal[1][0]-W_C)
            Y_1 = int(-(goal[1][1]-H_C ))

            X_2 = int(goal[2][0]-W_C)
            Y_2 = int(-(goal[2][1]-H_C ))

            X_3 = int(goal[3][0]-W_C)
            Y_3 = int(-(goal[3][1]-H_C ))
            send_data_to_msp_8(X_3,Y_3,X_2,Y_2,X_1,Y_1,X_0,Y_0)
            print(X_3,Y_3,X_2,Y_2,X_1,Y_1,X_0,Y_0)
        else:
            pass

