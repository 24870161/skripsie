import serial
import time
import RPi.GPIO as GPIO

# GPIO setup
PWX_PIN = 18  # GPIO pin connected to PWX of the SIM800
GPIO.setmode(GPIO.BCM)
GPIO.setup(PWX_PIN, GPIO.OUT)

# Serial setup for UART communication
ser = serial.Serial('/dev/ttyS0', baudrate=115200, timeout=1)

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

# Function to send an SMS
def send_sms(phone_number, message):
    send_at_command('AT+CMGF=1')  # Set SMS mode to text
    send_at_command(f'AT+CMGS="{phone_number}"')  # Set recipient phone number
    ser.write((message + '\x1A').encode())  # Send the message and Ctrl+Z (ASCII 26) to end

# Main function
def main():
    # Power on the SIM800 module
    print("Powering on the module...")
    toggle_power()
    
    # Wait for the module to start
    time.sleep(10)  # Wait for the module to initialize
    
    # Test communication with the module
    send_at_command('AT')

    # Wait for network registration
    wait_for_network()

    # Send an SMS
    phone_number = "+27762156187"  # Replace with the recipient's phone number
    message = "Hello from SIM800 module! Hello!"
    send_sms(phone_number, message)

    # Wait for a few seconds to ensure the SMS is sent
    time.sleep(5)

    # Power off the module
    print("Turning off the module...")
    toggle_power()

if __name__ == "__main__":
    main()

# Clean up GPIO when the program exits
GPIO.cleanup()
