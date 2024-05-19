from pythonosc import udp_client, dispatcher, osc_server
import threading
import time
import signal
import pandas as pd
from ipywidgets import Output



class OSCTarget:
    def __init__(self, ip, port, name):
        self.ip = ip
        self.port = port
        self.client = udp_client.SimpleUDPClient(self.ip, self.port)
        self.name = name
        
class OSCCommunicator:
    def __init__(self, my_ip, my_port):
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

        # handle received messages
        #self.dispatcher.map(self.test_response_address, self._handle_test_response)
        #self.dispatcher.map(self.measurement_address, self._handle_measurement)

        # create output so that we can avoid cell rerunning issues
        self.output = Output()

        # map handlers to output
        self._map_handlers(self.output)

    def _map_handlers(self, output):
        """
        Handlers need to be passed the output object when created because they will be locked inside a thread
        """
        self.dispatcher.map(self.test_response_address, lambda address, *args: self._handle_test_response(output, address,*args))
        self.dispatcher.map(self.measurement_address, lambda address, *args: self._handle_measurement(output, address, *args))

    def start_server(self):
        # only start if not already running
        if self.server is None:
            
            # show output in the cell where this was called
            display(self.output) 

            # create server (to receive responses)
            self.server = osc_server.ThreadingOSCUDPServer((self.my_ip, self.my_port), self.dispatcher)

            # print to output
            started_string = f"OSC Server Started. Serving on {self.server.server_address}"
            with self.output:
                print(started_string)
                print('-' * len(started_string), end='\n\n')
            
            # start server in thread to always be receiving in background
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.start()

    def shutdown(self):
        if self.server:
            self.server.shutdown()
            self.server_thread.join()
            with self.output:
                print("Shutdown completed")

            # delete server 
            delattr(self, 'server')
            self.server = None

    def send_measurement(self, target:OSCTarget, measurement_results):
        target.client.send_message("/bruQner/measurement_result", measurement_results)
        print(f'Measurement {measurement_results} sent to {target.name}')

    def send_test_request(self, target:OSCTarget):
        target.client.send_message(self.test_request_address, '1')
        print(f'Test request sent to "{target.name}"')

    # mainly for testing because I will never have to actually send test responses
    def send_test_response(self, target:OSCTarget):
        target.client.send_message(self.test_response_address, '1')

    # Handlers for received messages
    def _handle_test_response(self, output, address, *args):
        with output:
            print("Test successful")

    def _handle_measurement(self, output, address, *args):
        with output:
            print(f"Received measurement: {args}")

