from pythonosc import udp_client
from pythonosc import dispatcher
from pythonosc import osc_server
import threading
import time
import signal


# make sure servers are shut down properly when forced close python
def signal_handler(sig, frame):
    print("Shutting down server...")
    server.shutdown()  # Shut down the server gracefully
    print("Shutdown completed")
    exit(0)

def default_handler(address, *args):
    print(f"Received message on {address} with arguments: {args}")

def test_message_handler(address, client, received_message):
    print("Test received")
    #print(f"Received test message on {address}: {received_message}")
    # Respond back to the sender's listen port
    client[0].send_message(test_response_address, "Acknowledged")

def measurement_message_handler(address, received_message,):
    print(f"Received measurement on {address}: {received_message}")

measurement_address = "/bruQner/measurement_result"
test_request_address = "/bruQner/connection_test/request"
test_response_address = "/bruQner/connection_test/response"

measurement_results = [1, 2, 3, 4]

if __name__ == "__main__":

    # Setup ports and IP
    target_ip = "192.168.0.10"
    target_port = 12345
    my_ip = "192.168.0.10" 
    my_port = 12347  
    
    # Setup clientside (to send out measurements and test requests)
    client = udp_client.SimpleUDPClient(target_ip, target_port)

    # Setup handling of test responses 
    disp = dispatcher.Dispatcher()
    disp.map(test_request_address, test_message_handler, client)
    disp.map(measurement_address, measurement_message_handler)
    disp.set_default_handler(default_handler)
    
    # Setup and run server to receive test responses
    server = osc_server.ThreadingOSCUDPServer((my_ip, my_port), disp)
    print(f"Serving on {server.server_address}")
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()

    # catch keyboard interrupt and shut down
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # need this so I can catch keyboard interrupts
    while True:
        time.sleep(1000)