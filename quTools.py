import requests
import time
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup  # Make sure to install BeautifulSoup: pip install beautifulsoup4

class DeviceController:
    def __init__(self, ip_address):
        self.base_url = f"http://{ip_address}:8080"

    def send_request(self, action, param, value=None):
        url = f"{self.base_url}/?action={action}&param={param}"
        if value is not None:
            url += f"&value={value}"

        response = requests.get(url)
        return response.text

def parse_count_rates(response_text):
    soup = BeautifulSoup(response_text, 'html.parser')
    counts = soup.find_all('body')[0].get_text().split(':')[2:-1]  # Extract counts from response
    count_0 = int(counts[0].strip())
    count_1 = int(counts[1].strip())
    count_01 = int(counts[2].strip())
    return count_0, count_1, count_01

def collect_data_and_plot(controller, duration, polling_interval):
    start_time = time.time()
    end_time = start_time + duration
    timestamps = []
    count_rates_0 = []
    count_rates_1 = []
    count_rates_01 = []

    while time.time() < end_time:
        # Poll count rates
        response_get_cnt = controller.send_request(action="get", param="cnt")
        
        # Parse response and extract count rates
        count_0, count_1, count_01 = parse_count_rates(response_get_cnt)

        # Record timestamp and count rates
        timestamps.append(time.time() - start_time)
        count_rates_0.append(count_0)
        count_rates_1.append(count_1)
        count_rates_01.append(count_01)

        time.sleep(polling_interval)

    # Plot the results
    #plt.plot(timestamps, count_rates_0, label='Count 0', marker='o')
    plt.plot(timestamps, count_rates_1, label='Count 1', marker='o')
    #plt.plot(timestamps, count_rates_01, label='Count 01', marker='o')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Count Rates')
    plt.title('Count Rates Over Time')
    plt.legend()
    plt.show()

# Example usage:
if __name__ == "__main__":
    ip_address = "169.254.230.102"
    controller = DeviceController(ip_address)

    controller.send_request(action='set', param='pm1', value=60)
    # Collect data for 30 seconds with a polling interval of 1 second
    #collect_data_and_plot(controller, duration=60, polling_interval=0.1)