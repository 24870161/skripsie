import serial
import time

# Setup serial communication
ser = serial.Serial('/dev/ttyS0', baudrate=9600)

def send_at_command(command, delay=2):
    ser.write((command + '\r').encode())  # Send the command
    time.sleep(delay)  # Wait for response
    response = ser.read(ser.in_waiting).decode()  # Read the response
    print(f"Command: {command}")
    print(f"Response: {response}")
    return response

def power_on_modem():
    print("Powering on the module...")
    # Handle any GPIO power control here if needed
    time.sleep(2)

def initialize_modem():
    # Initialize modem with the correct command sequence
    send_at_command('AT')  # Test communication
    send_at_command('AT+CFUN=1')  # Set to full functionality
    send_at_command('AT+CPIN?')  # Check SIM status
    send_at_command('AT+CREG?')  # Check network registration

def wait_for_gprs_connection():
    print("Waiting for GPRS connection...")
    while True:
        response = send_at_command('AT+CGATT?', delay=2)  # Check GPRS attachment
        if '+CGATT: 1' in response:  # If attached to GPRS
            print("GPRS attached successfully.")
            break
        else:
            print("GPRS not attached yet. Retrying in 5 seconds...")
            time.sleep(5)

def connect_gprs():
    apn = '65501'  # Your APN
    gprs_user = ''
    gprs_pass = ''
    
    # Set up GPRS connection
    print("Connecting to GPRS...")
    response = send_at_command(f'AT+CSTT="{apn}","{gprs_user}","{gprs_pass}"')  # Set APN
    if "ERROR" in response:
        print("Failed to set APN.")
        return False

    response = send_at_command('AT+CIICR')  # Bring up wireless connection
    if "ERROR" in response:
        print("Failed to bring up wireless connection.")
        return False
    
    response = send_at_command('AT+CIFSR')  # Get IP address
    if "ERROR" in response or response.strip() == '':
        print("Failed to obtain IP address.")
        return False
    print(f"IP address: {response.strip()}")
    return True

def send_data(value):
    google_script_url = f"https://script.google.com/macros/s/AKfycbwEldma6HhCQdfZxw1kImYbz3nXpQdGeVEB6ynq-jXztRBqc8kyUbnORgoqQmGZOpU/exec?value={value}"
    
    # Send HTTP request to Google Script
    print("Sending data to Google Script...")
    send_at_command('AT+HTTPINIT')  # Initialize HTTP
    send_at_command('AT+HTTPPARA="CID",1')  # Set GPRS context
    send_at_command(f'AT+HTTPPARA="URL","{google_script_url}"')  # Set URL
    send_at_command('AT+HTTPSSL=1')  # Enable HTTPS
    send_at_command('AT+HTTPACTION=0')  # Start HTTP GET
    response = send_at_command('AT+HTTPREAD')  # Read response
    print(f"HTTP Response: {response}")
    send_at_command('AT+HTTPTERM')  # Terminate HTTP session

def main():
    power_on_modem()  # Power on the module (GPIO control can be added if necessary)
    initialize_modem()  # Initialize the modem with the correct command sequence
    wait_for_gprs_connection()  # Wait for GPRS connection
    
    # Connect to GPRS and check for success before proceeding
    if connect_gprs():
        send_data(111)  # Example value to send

if __name__ == "__main__":
    main()
