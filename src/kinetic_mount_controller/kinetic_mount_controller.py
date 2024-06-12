import sys
import time
import threading
import src.elliptec as elliptec

class DeviceError(Exception):
    """raised when there is an error regarding the setup of the kinetic devices"""
    def __init__(self, message):
        super().__init__(message)
        self.message = message

class KineticMountControl:
    
    def _print_div(self, title=None):
        if title is not None: print(title)
        print('---------------------------------------------------------------') 

    def _get_connected_device(self, controller, stop_address=3):
        """
        Scan for device with address 0 and return info dictionary or None
        """
        try:
            return elliptec.scan_for_devices(controller, start_address=0, stop_address=stop_address, debug=False)[0]
        except:
            return None

    def _print_successfull_connection(self, device_info):
        motor_type = device_info['info']['Motor Type']
        description = elliptec.devices[motor_type]['description']
        print(f"Device succesfully connected ({description}) (Address: {device_info['info']['Address']})")

    def __init__(self, number_of_devices, address_search_depth=3) -> None:
        
        # initialise list of elliptec controllers
        self.controllers = []
        self.devices = []

        # placeholders for Alice and Bobs rotation mount and the linear polariser shutter
        self.alice = None
        self.bob = None
        self.shutter = None

        # Search for controller and assign
        self._print_div('\nASSIGNING CONTROLLERS')
        ports_found = elliptec.find_ports()
        print(f"Ports Found: {ports_found}")
        
        if len(ports_found) != number_of_devices:
            raise Exception("\n\nNo ports found does not match specified number of devices\n")

        self.controllers = []
        for port in ports_found:
            self.controllers.append(elliptec.Controller(port, debug=False))
        self._print_div()

        # get devices from controllers and assign
        for controller in self.controllers:
            
            device = self._get_connected_device(controller, stop_address=address_search_depth)

            motor_type = device['info']['Motor Type']
            address = device['info']['Address']

            # Rotation Mount
            if motor_type == 14:
                rotator = elliptec.Rotator(controller, address=address, debug=False)
                self.devices.append(rotator)

                # assign rotator 
                if self.alice == None:
                    self.alice = rotator 
                else:
                    self.bob = rotator
            
            # Dual Position Slider
            elif motor_type == 6:
                new_shutter = elliptec.Shutter(controller, address=address, debug=False)
                self.devices.append(new_shutter)

                self.shutter = new_shutter

            # Raise error if anything else
            else:
                assert motor_type in [6, 14], "\n\nERROR: Unsopported Device Type\n"
            self._print_successfull_connection(device)

    # MOVEMENT FUNCTIONS

    # TODO: Shutter needs to be calibrated to open, and then only referred to as classical or quantum
    def toggle_shutter():
        pass
    
    def rotate_alice(self, angle):
        """Multithreaded rotate of Alice filter"""
        thread = threading.Thread(target=self.alice.set_angle, args=(angle,))
        thread.start()
        thread.join()

    def rotate_bob(self, angle):
        """Multithreaded rotate of Bob filter"""
        thread = threading.Thread(target=self.bob.set_angle, args=(angle,))
        thread.start()
        thread.join()

    def rotate_simulataneously(self, alice_angle, bob_angle):
        """
        Uses multithreading to rotate bob and alice simultaneously
        """
        thread_a = threading.Thread(target=self.alice.set_angle, args=(alice_angle,))
        thread_b = threading.Thread(target=self.bob.set_angle, args=(bob_angle,))

        # Start both threads
        thread_a.start()
        thread_b.start()

        # Wait for both threads to complete
        thread_a.join()
        thread_b.join()



    # TEST FUNCTIONS
    def wiggle_test(self, rotator):
        """
        Wiggle rotator back and forth a couple times
        parameters: rotator = ['alice', 'bob']
        """

        initial_alice = self.alice.get_angle()
        initial_bob = self.bob.get_angle()

        for i in range(2*3):
            wiggle_angle = (-1)*(i%2) * 45

            if rotator.lower() == "alice":
                self.rotate_alice(initial_alice + wiggle_angle)
            elif rotator.lower() == "bob":
                self.rotate_bob(initial_bob + wiggle_angle)

            time.sleep(0.3)

    def alice_check(self):
        self.wiggle_test('alice')

    def bob_check(self):
        self.wiggle_test('bob')

    def swap_alice_bob(self):
        self.alice, self.bob = self.bob, self.alice

    def home(self):
        self.rotate_simulataneously(alice_angle=0, bob_angle=0)
        #self.shutter.open()
        




class KineticMountControllerBUS:
    """
    If using the BUS board and are connecting multiple devices via 1 USB (deprected)
    """
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

    def __init__(self, number_of_devices, port=None):

        # initialise list of elliptec device objects
        self.devices = []

        # Search for controller and assign it
        self._print_div('\nASSIGNING CONTROLLER')
        ports_found = elliptec.find_ports()
        print(f"Ports Found: {ports_found}")

        if not ports_found:
            raise Exception("\n\nNo ports found. Make sure Controller is plugged in\n")

        if port == None:
            port = ports_found[0]
        elif port not in ports_found:
            raise Exception(f"\n\nSpecified port ({port}) not found\n")

        self.controller = elliptec.Controller(port, debug=False)
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
