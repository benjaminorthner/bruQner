import sys
import time
import threading

sys.path.append('elliptec/src')
import elliptec

class DeviceError(Exception):
    """raised when there is an error regarding the setup of the kinetic devices"""
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class KineticMountController:

    def _print_div(self, title=None):
        if title is not None: print(title)
        print('---------------------------------------------------------------') 

    def _get_buffer_device(self):
        """
        Scan for device with address 0 and return info dictionary or None
        """
        try:
            return elliptec.scan_for_devices(self.controller, start_address=0, stop_address=0, debug=False)[0]
        except:
            return None
        
    def _print_successfull_connection(self, device_info):
        motor_type = device_info['info']['Motor Type']
        description = elliptec.devices[motor_type]['description']
        print(f"Device {sum(x is not None for x in self.assigned_device_infos)} succesfully connected ({description})")

    def __init__(self, number_of_devices):

        # initialise list of elliptec device objects
        self.devices = []

        # Search for controller and assign it
        self._print_div('\nASSIGNING CONTROLLER')
        ports_found = elliptec.find_ports()
        print(f"Ports Found: {ports_found}")
        self.controller = elliptec.Controller(ports_found[0], debug=False)
        self._print_div()

        # Go through sequence of searching for and assigning devices until all devices 
        # have been assigned an address
        
        self._print_div('\nASSIGNING DEVICES')

        # Initialise list of assigned devices as empty
        self.assigned_device_infos = [None] * number_of_devices 

        # do initial check for how many devices are already assigned to somethign other than 0 
        already_assigned_device_infos = elliptec.scan_for_devices(self.controller, start_address=1, stop_address=number_of_devices, debug=False)
        if len(already_assigned_device_infos) > 0:
            for device in already_assigned_device_infos:
                idx = int(device['info']['Address'], 16) - 1
                self.assigned_device_infos[idx] = device
                self._print_successfull_connection(device)
        
        # while the not all devices have been assigned perform this loop
        while None in self.assigned_device_infos:
            
            # check for device with address 0 (buffer address)
            try:
                buffer_address_device = self._get_buffer_device()
                assert buffer_address_device is not None

                # Find lowest free slot
                lowest_free_index = self.assigned_device_infos.index(None)
            except:
                # When buffer is empty ask user to plug in new device
                input('Connect next device (only 1) then press "Enter" to continue...')
                sys.stdout.write("\033[F")  # Move the cursor to the previous line
                sys.stdout.write("\033[K")  # clear the line
                sys.stdout.flush()
                time.sleep(6) # wait for connection to actually happen
                continue

            # assign corresponding address to this device (convert from dec to hex to str)
            device = elliptec.Motor(self.controller, address='0', debug=False)
            device.change_address(str(hex(lowest_free_index+1)[2:]).upper())
            self.assigned_device_infos[lowest_free_index] = buffer_address_device
            self._print_successfull_connection(buffer_address_device)

        
        # Now the entire list of devices must be populated
        # check if there are more devices in the 0 slot. And if yes raise exception
        # because they should have all been assigned by now
        if self._get_buffer_device() is not None:
            raise DeviceError('More devices connected than specified')

        self._print_div()

        # Initialise elliptec objects for each device (based on motor type)
        for device in self.assigned_device_infos:
            
            motor_type = device['info']['Motor Type']
            address = device['info']['Address']

            # Rotation Mount
            if motor_type == 14:
                self.devices.append(elliptec.Rotator(self.controller, address=address, debug=False))
            
            # Dual Position Slider
            elif motor_type == 6:
                self.devices.append(elliptec.Shutter(self.controller, address=address, debug=False))

            # Raise error if anything else
            else:
                assert motor_type in [6, 14], "\n\nERROR: Unsopported Device Type\n"


def set_angles_simultaneously(angle1, angle2):
    """
    Does not actually work simultaneously yet because can not handle responses from controller asynchronously without errors
    But it is still slighly faster than just running back to back
    """
    thread_a = threading.Thread(target=a_hwp.set_angle, args=(angle1,))
    thread_b = threading.Thread(target=b_hwp.set_angle, args=(angle2,))

    # Start both threads
    thread_a.start()
    thread_b.start()

    # Wait for both threads to complete
    thread_a.join()
    thread_b.join()

if __name__ == '__main__':
    KMC = KineticMountController(number_of_devices=3)
    
    shutter, a_hwp, b_hwp = KMC.devices

    a_hwp.home()
    b_hwp.home()
    time.sleep(1)

    for _ in range(10):
        set_angles_simultaneously(90, 90)
        time.sleep(0)
        set_angles_simultaneously(45, 45)
        time.sleep(0)

    #shutter.home()
    #shutter.open()

