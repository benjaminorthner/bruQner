from pythonosc import dispatcher
from pythonosc import osc_server
import threading


def handle_osc_message(address, *args):
    print(f"Received OSC message on {address} with data: {args}")

if __name__ == "__main__":
    # Set up the dispatcher to handle messages
    disp = dispatcher.Dispatcher()
    disp.map("/stream", handle_osc_message)  # Handle messages on the /stream address

    # Set up the server
    ip = "172.26.48.1"
    port = 12345
    server = osc_server.ThreadingOSCUDPServer((ip, port), disp)
    print(f"Serving on {server.server_address}")
    server.serve_forever()  # Start the server to listen indefinitely