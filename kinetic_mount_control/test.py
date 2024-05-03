import sys
import time

sys.path.append('elliptec/src')
import elliptec


ports_found = elliptec.find_ports()
print(f"Ports Found: {ports_found}")

# connected to controler
controller = elliptec.Controller(ports_found[0])

# check what is connected
device_scan = elliptec.scan_for_devices(controller, start_address=0, stop_address=0, debug=False)

for device in device_scan:
    print(device)
# connect to devices
#device_1 = elliptec.Motor(controller, address='1')
#print(device_1.info)
exit()
device_1.change_address('1')

sh = elliptec.Shutter(controller, address='1')

print("device 1 connected")
time.sleep(2)
device_2 = elliptec.Motor(controller)
device_2.change_address('2')

ro1 = elliptec.Rotator(controller, address='2')

exit()
#print(elliptec.scan_for_devices(controller))
#ro = elliptec.Rotator(controller)
sh = elliptec.Shutter(controller, address='0')
sh.home() 
while True:
    sh.open()
    sh.close()
# Home the rotator before usage
#print(ro.set_home_offset(315))
#ro.home()

#time.sleep(1)



#while True:
#    for a in [40, 360-40]:
#        ro.set_angle(a)
#        print(a)
#        time.sleep(0.2)