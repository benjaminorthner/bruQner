from pythonosc import udp_client, dispatcher, osc_server
import threading
import time
import signal
import pandas as pd
from ipywidgets import Output
import logging



class OSCTarget:
    def __init__(self, ip, port, name):
        self.ip = ip
        self.port = port
        self.client = udp_client.SimpleUDPClient(self.ip, self.port)
        self.name = name
        
class OSCCommunicator:
    def __init__(self, my_ip, my_port):
        
        self.currently_selected_state = 'Q_all'

        self.my_ip = my_ip
        self.my_port = my_port

        # import Johannes' data
        self.QuantumData = pd.read_csv("../data/Quantum_Music_2.8.csv", header=None, names=['setting_a', 'setting_b', 'result_a', 'result_b'])
        self.ClassicalData = pd.read_csv("../data/Quantum_Music_1.4.csv", header=None, names=['setting_a', 'setting_b', 'result_a', 'result_b'])

        self.dispatcher = dispatcher.Dispatcher()
        self.server = None
        self.server_thread = None

        self.measurement_address = "/bruQner/measurement_result"
        self.test_request_address = "/bruQner/connection_test/request"
        self.test_response_address = "/bruQner/connection_test/response"

        self.set_state_address = "/bruQner/set/state"

        # handle received messages
        self.dispatcher.set_default_handler(self._default_handler)
        self.dispatcher.map(self.test_response_address, self._handle_test_response)
        self.dispatcher.map(self.measurement_address, self._handle_measurement)
        self.dispatcher.map(self.set_state_address, self._handle_set_state)


        # Configure logging
        logging.basicConfig(
            filename='osc_log.txt',  # Log file name
            level=logging.INFO,      # Logging level (INFO, DEBUG, etc.)
            format='%(asctime)s - %(levelname)s - %(message)s'  # Log message format
        )

        # Interrupt Signal handling
        signal.signal(signal.SIGINT, lambda *args : self.shutdown())
        signal.signal(signal.SIGTERM, lambda *args : self.shutdown())

    # log both to file and to terminal
    def log(self, message:str):
        logging.info(message)
        print(message)

    def start_server(self):
        # only start if not already running
        if self.server is None:
            
            # create server (to receive responses)
            self.server = osc_server.ThreadingOSCUDPServer((self.my_ip, self.my_port), self.dispatcher)

            started_string = f"OSC Server Started. Serving on {self.server.server_address}"
            self.log(started_string)
            self.log('-' * len(started_string))
            
            # start server in thread to always be receiving in background
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.start()

    def shutdown(self):
        if self.server:
            self.server.shutdown()
            self.server_thread.join()
            self.log("Shutdown completed")

            # delete server 
            delattr(self, 'server')
            self.server = None
            self.log("Shutting down OSC server...")

    def send_measurement(self, target:OSCTarget, measurement_results):
        target.client.send_message("/bruQner/measurement_result", measurement_results)
        self.log(f'Measurement {measurement_results} sent to {target.name}')
    
    def send_visuals(self, target:OSCTarget, measurement_results):
        target.client.send_message("/bruQner/visuals/manual", measurement_results)
        self.log(f'Measurement {measurement_results} sent to {target.name}')

    def send_test_request(self, target:OSCTarget):
        target.client.send_message(self.test_request_address, '1')
        self.log(f'Test request sent to "{target.name}"')

    # mainly for testing because I will never have to actually send test responses
    def send_test_response(self, target:OSCTarget):
        target.client.send_message(self.test_response_address, '1')

    # Handlers for received messages
    def _default_handler(self, address, *args):
        self.log(f"Received OSC_message: {args}")

    def _handle_test_response(self, address, *args):
        self.log("Test successful")

    def _handle_measurement(self, address, *args):
        self.log(f"Received measurement: {args}")

    def _handle_set_state(self, address, *args):
        self.currently_selected_state = args[0]
        self.log(f"State Changed to: {self.currently_selected_state}")