from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
import threading
import time
from random import choice
import signal
import pandas as pd


# make sure servers are shut down properly when forced close python
def signal_handler(sig, frame):
    print("Shutting down server...")
    server.shutdown()  # Shut down the server gracefully
    print("Shutdown completed")
    exit(0)


def receive_handler(address, *args):
    print("test sccessful")
    global last_response_time
    last_response_time = time.time()

measurement_address = "/bruQner/measurement_result"
test_request_address = "/bruQner/connection_test/request"
test_response_address = "/bruQner/connection_test/response"

data_quantum = pd.read_csv("data/Quantum_Music_2.8.csv", header=None, names=['setting_a', 'setting_b', 'result_a', 'result_b'])
data_classic = pd.read_csv("data/Quantum_Music_1.4.csv", header=None, names=['setting_a', 'setting_b', 'result_a', 'result_b'])



if __name__ == "__main__":

    # Setup ports and IP
    target_ip = "192.168.0.3"  # receiving computers IP 
    target_port = 7400  # receiving computers listening port
    my_ip = "192.168.0.2"
    my_port = 7401
    
    # Setup handling of test responses 
    disp = dispatcher.Dispatcher()
    disp.map(test_response_address, receive_handler)  # Expecting responses on /response

    # Setup and run server to receive test responses
    server = osc_server.ThreadingOSCUDPServer((my_ip, my_port), disp)
    print(f"Serving on {server.server_address}")
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    # Setup clientside (to send out measurements and test requests)
    client = udp_client.SimpleUDPClient(target_ip, target_port)

    # catch keyboard interrupt and shut down
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # send test messages every 10s forever
    
    # send measurement result every 1s forever
    i = 0
    while True:

        # Random number from
        # client.send_message(measurement_address, choice([1, 2, 3, 4]))

        # loop through data row by row
        d = data_quantum.iloc[i % len(data_quantum)]
        #d = data_classic.iloc[i % len(data_classic)]
        measurement_result = d #f"{d['setting_a']} {d['setting_b']} {d['result_a']} {d['result_b']}"
        print(measurement_result)
        client.send_message(measurement_address, measurement_result)

        # send test message every 10 iterations
        if i % 1 == 0:
            client.send_message(test_request_address, "1")
            print('test')
            


        i += 1 
        time.sleep(0.1)  