import serial
import time
import RPi.GPIO as GPIO

# GPIO setup
PWX_PIN = 18  # GPIO pin connected to PWX of the SIM800
GPIO.setmode(GPIO.BCM)
GPIO.setup(PWX_PIN, GPIO.OUT)

# Serial setup for UART communication
ser = serial.Serial('/dev/ttyS0', baudrate=115200, timeout=3.0)

# Function to toggle the power (PWX) pin to turn the SIM800 on/off
def toggle_power():
    GPIO.output(PWX_PIN, GPIO.LOW)  # Pull the pin low
    time.sleep(2)  # Wait for 2 seconds (this will turn the module on/off)
    GPIO.output(PWX_PIN, GPIO.HIGH)  # Release the pin

# Function to send an AT command and read the response
def send_at_command(command, delay=2):
    ser.write((command + '\r').encode())
    time.sleep(delay)
    response = ser.read(ser.in_waiting).decode()
    print(f"Command: {command}")
    print(f"Response: {response}")
    return response

# Function to check if the SIM800 is connected to the network
def wait_for_network():
    print("Waiting for network connection...")
    while True:
        response = send_at_command('AT+CREG?', delay=2)  # Check network registration
        if '+CREG: 0,1' in response or '+CREG: 0,5' in response:  # Registered to home network or roaming
            print("Connected to the network.")
            break
        else:
            print("Not connected to the network. Retrying in 5 seconds...")
            time.sleep(5)

# Function to check signal strength
def check_signal_strength():
    response = send_at_command('AT+CSQ')  # Check signal strength
    # The response format is: +CSQ: <rssi>,<ber>
    # rssi values range from 0 to 31 (31 being the best), 99 = unknown/undetectable
    # ber (bit error rate) is usually ignored for basic use
    print("Signal strength response:", response)
    return response

# Function to connect to GPRS
def connect_gprs():
    apn = '65501'  # Replace with your APN
    gprs_user = ''
    gprs_pass = ''
    
    send_at_command(f'AT+CSTT="{apn}","{gprs_user}","{gprs_pass}"')  # Set APN
    response = send_at_command('AT+CIICR')  # Bring up wireless connection
    if "OK" in response:
        print("GPRS connected successfully.")
        send_at_command('AT+CIFSR')  # Get IP address
    else:
        print("Failed to connect to GPRS.")
        return False
    return True

# Function to send HTTP request and get the response
def http_request():
    send_at_command('AT+CDNSCFG="8.8.8.8","8.8.4.4"')  # Set DNS to Google's DNS
    url = "http://example.com"  # Replace with your URL
    send_at_command('AT+HTTPINIT')  # Initialize HTTP
    send_at_command('AT+HTTPPARA="CID",1')  # Set GPRS context
    send_at_command(f'AT+HTTPPARA="URL","{url}"')  # Set the URL
    send_at_command('AT+HTTPACTION=0')  # Start HTTP GET action
    time.sleep(3)  # Wait for the HTTP action to complete
    response = send_at_command('AT+HTTPREAD')  # Read the HTTP response
    print(f"HTTP Response: {response}")
    send_at_command('AT+HTTPTERM')  # Terminate HTTP session

# Main function
def main():
    # Power on the SIM800 module
    print("Powering on the module...")
    toggle_power()
    
    # Wait for the module to start
    time.sleep(10)  # Wait for the module to initialize
    
    # Test communication with the module
    send_at_command('AT')
    
    send_at_command('AT+GMR')
    # Wait for network registration
    wait_for_network()

    # Check signal strength
    check_signal_strength()

    # Connect to GPRS
    if connect_gprs():
        # Send HTTP request and get the response
        http_request()
    
    # Power off the module
    print("Turning off the module...")
    toggle_power()

if __name__ == "__main__":
    main()

# Clean up GPIO when the program exits
GPIO.cleanup()
