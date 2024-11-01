import requests
import subprocess
import sys
import time

# Function to send HTTP request using WiFi
def send_http_request(vehicles_counted, date, rpi_time):
    url = f"https://script.google.com/macros/s/AKfycbzToJ2en2NCraeKdaipUhHWLWZhr3tF5hQb_dFUu3ZCz6hJoeg8u_5fSUJFEDqrkEs/exec?date={date}&time={rpi_time}&value={vehicles_counted}"
    response = requests.get(url, timeout=10)
    #try:
        #response = requests.get(url, timeout=10)
        #if response.status_code == 200:
            #print("HTTP request successful!")
        #else:
            #print(f"HTTP request failed with status code: {response.status_code}")
    #except requests.RequestException as e:
        #print(f"Error sending HTTP request: {e}")

# Function to get the current Raspberry Pi date and time
def get_rpi_datetime():
    current_time = subprocess.check_output("date +'%d/%m/%Y %H:%M'", shell=True).decode().strip()
    date, rpi_time = current_time.split(" ")
    #print(f"Raspberry Pi Date: {date}, Time: {rpi_time}")
    return date, rpi_time

# Main function
def main(vehicles_counted=0):
    # Get Raspberry Pi date and time
    date, rpi_time = get_rpi_datetime()

    # Send HTTP request
    send_http_request(vehicles_counted, date, rpi_time)

    #print("Data uploaded to Google Sheet.")

if __name__ == "__main__":
    # If vehicles counted is provided as an argument, use it; otherwise default to 0
    vehicles_counted = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    main(vehicles_counted)
