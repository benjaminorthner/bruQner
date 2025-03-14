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

    # We chose not to implement the shutter after all. But if we do so later, we would use this
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

    @staticmethod
    def hybrid_wait(target_duration, start_time):
        """
        Combines the efficiency of the inaccurate time.sleep() function
        with the accuracy of a busy-wait loop once only 20ms are left until the target_duration
        """

        while True:
            elapsed_time = time.perf_counter() - start_time
            remaining_time = target_duration - elapsed_time

            if remaining_time <= 0:
                break

            if remaining_time > 0.02:  # Sleep only for durations > 20ms
                time.sleep(remaining_time - 0.02)


    def rotate_simulataneously(self, alice_angle, bob_angle, wait_for_completion=True, wait_for_elapsed_time=0):
        """
        Uses multithreading to rotate bob and alice simultaneously.
        
        Parameters:
            alice_angle: Target angle for Alice.
            bob_angle: Target angle for Bob.
            wait_for_completion: If True, waits for rotation to complete before returning.
            wait_for_elapsed_time: Minimum time to wait before returning (in seconds).
        """
        start_time = time.time()

        thread_a = threading.Thread(target=self.alice.set_angle, args=(alice_angle,))
        thread_b = threading.Thread(target=self.bob.set_angle, args=(bob_angle,))

        # Start both threads
        thread_a.start()
        time.sleep(0.004)
        thread_b.start()

        # Wait for both threads to complete
        if wait_for_completion:
            thread_a.join()
            thread_b.join()

        # Calculate elapsed time
        elapsed_time = time.time() - start_time

        # Wait for the remainder of the specified time
        if elapsed_time < wait_for_elapsed_time:
            time.sleep(wait_for_elapsed_time - elapsed_time)
        

    def rotate_simulataneously_metronome(self, alice_angle, bob_angle, alice_prev_angle, bob_prev_angle, wait_for_completion=True, target_duration=None):
        """
        Uses multithreading to rotate bob and alice simultaneously. 
        Allows for user set time offsets in order to synchronize clicking sounds between rotators
        
        Parameters:
            alice_angle: Target angle for Alice.
            bob_angle: Target angle for Bob.
            wait_for_completion: If True, waits for rotation to complete before returning.
                                If False, returns as soon as possible while rotators still turning in different threads
            target_duration: Code returns once this time is reached (assuming computation is done by then)
        """
        start_time = time.perf_counter()

        thread_a = threading.Thread(target=self.alice.set_angle, args=(alice_angle,))
        thread_b = threading.Thread(target=self.bob.set_angle, args=(bob_angle,))

        bob_delay = 0.008
        alice_delay = 0
        bob_cw_delay = 0.005
        bob_ccw_delay = 0
        alice_cw_delay = 0.03
        alice_ccw_delay = 0.01

        # Get total delays based on rotation direction 
        alice_total_delay = alice_delay
        if alice_angle != alice_prev_angle:
            alice_total_delay += (alice_cw_delay if alice_angle > alice_prev_angle else alice_ccw_delay)

        bob_total_delay = bob_delay 
        if bob_angle != bob_prev_angle:
            bob_total_delay += (bob_cw_delay if bob_angle > bob_prev_angle else bob_ccw_delay)


        # start bob first and delay alice 
        if alice_total_delay > bob_total_delay:
            thread_start_time = time.perf_counter()
            self.hybrid_wait(target_duration=bob_total_delay, start_time=thread_start_time)
            thread_b.start()
            self.hybrid_wait(target_duration=alice_total_delay, start_time=thread_start_time)
            thread_a.start()
        
        # start alice first and delay bob
        else:
            thread_start_time = time.perf_counter()
            self.hybrid_wait(target_duration=alice_total_delay, start_time=thread_start_time)
            thread_a.start()
            self.hybrid_wait(target_duration=bob_total_delay, start_time=thread_start_time)
            thread_b.start()

        # Wait for both threads to complete
        if wait_for_completion:
            thread_a.join()
            thread_b.join()

        # wait until target duration is reached regardless of wait_for_completion parameter
        if time.perf_counter() - start_time <=  target_duration:
            self.hybrid_wait(target_duration, start_time=start_time)



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
