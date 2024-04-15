from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
import threading
import time
from random import choice
import signal


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

measurement_results = [1, 2, 3, 4]

if __name__ == "__main__":

    # Setup ports and IP
    target_ip = "172.26.48.1"  # receiving computers IP 
    target_port = 12347  # receiving computers listening port
    my_ip = "127.0.0.1"
    my_port = 12345
    
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
        client.send_message(measurement_address, choice(measurement_results))

        # send test message every 10 iterations
        if i % 10 == 0:
            client.send_message(test_request_address, "Test Message")

        i += 1 
        time.sleep(0.0001)  