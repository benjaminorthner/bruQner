import sys
import time

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

    def __init__(self, number_of_devices):
        
        # Search for controller and assign it
        self._print_div('\nASSIGNING CONTROLLER')
        ports_found = elliptec.find_ports()
        print(f"Ports Found: {ports_found}")
        self.controller = elliptec.Controller(ports_found[0])
        self._print_div()

        # Go through sequence of searching for and assigning devices until all devices 
        # have been assigned an address
        
        self._print_div('\nASSIGNING DEVICES')

        # Initialise list of assigned devices as empty
        assigned_devices = [None] * number_of_devices 

        # do initial check for how many devices are already assigned to somethign other than 0 
        already_assigned_devices = elliptec.scan_for_devices(self.controller, start_address=1, stop_address=number_of_devices, debug=False)
        if len(already_assigned_devices) > 0:
            for device in already_assigned_devices:
                idx = int(device['info']['Address'], 16) - 1
                assigned_devices[idx] = device
        
        # check if list is not full
        if None in assigned_devices:
            
            # check for device with address 0 (buffer address)
            try:
                buffer_address_device = elliptec.scan_for_devices(self.controller, start_address=0, stop_address=0, debug=False)            
                # Find lowest free slot
                lowest_free_index = assigned_devices.index(None)
            except:
                raise DeviceError('Less devices connected than specified')

            # assign corresponding address to this device (convert from dec to hex to str)
            device = elliptec.Motor(self.controller, address='0')
            device.change_address(str(hex(lowest_free_index+1)[2:]).upper())
            assigned_devices[lowest_free_index] = buffer_address_device[0]
        
        # if list of assigned devices is fully populated
        else:
            # check if there are more devices in the 0 slot
            if self._get_buffer_device() is not None:
                raise DeviceError('More devices connected than specified')

        for device in assigned_devices:
            print(device)



if __name__ == '__main__':
    KMC = KineticMountController(number_of_devices=2)