import network
import ntptime

import time


#
with open('wifi.cfg') as f:
    ssid = f.readline().strip() # remove trailing newlines
    password = f.readline().strip()


nic = network.WLAN(network.STA_IF)
nic.active(True)
nic.connect(ssid, password)

# wait for connection
while not nic.isconnected():
    time.sleep(1)

# set RTC clock to current time
ntptime.settime()
nic.disconnect()

with open('system.log', 'a') as f:
    f.write(f'{time.time()}: finished boot sequence\n')
