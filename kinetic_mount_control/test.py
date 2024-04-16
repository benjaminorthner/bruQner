import sys
import time

sys.path.append('elliptec/src')
import elliptec


print(elliptec.find_ports())

controller = elliptec.Controller('COM9')

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