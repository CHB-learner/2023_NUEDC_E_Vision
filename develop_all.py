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
ls_x_R=[]
ls_y_R=[]
ls_x_G=[]
ls_y_G=[]
while(True):
	clock.tick()
	img = sensor.snapshot()
	blob = img.find_blobs(threshold, area_threshold=10, margin=1)
	W = img.width()
	H = img.height()
	W_C = W/2
	H_C = H/2
	data1 = 230
	data2 = 250
	if blob:
		if len(blob) == 2 :
			for b in blob:
				if b[5]<302 and b[5] >20 and b[6]<190 and b[6]>8  :
					img.draw_rectangle(b.rect(),color=(0,0,255),thickness=3)
					R,G,B = calculate_average_rgb(b.min_corners())
					if (R-G)>10:
						img.draw_cross(b[5], b[6],color = (255, 0, 0), size = 50)
						X_R = b[5]
						Y_R = b[6]
						ls_x_R.append(X_R)
						ls_y_R.append(Y_R)
					if (G-R)>10:
						img.draw_cross(b[5], b[6],color = (0, 255, 0), size = 50)
						X_G = b[5]
						Y_G = b[6]
						ls_x_G.append(X_G)
						ls_y_G.append(Y_G)
					if len(ls_x_R) == send_len:
						X_send = int(sum(ls_x_G)/send_len - sum(ls_x_R)/send_len)
						Y_send = -int(sum(ls_y_G)/send_len - sum(ls_y_R)/send_len)
						send_data_to_msp(X_send,Y_send)
						print(X_send,Y_send)
						blue_led.toggle()
						ls_x_R=[]
						ls_y_R=[]
						ls_x_G=[]
						ls_y_G=[]
	else:
		pass