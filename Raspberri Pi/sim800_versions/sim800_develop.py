import serial
import time
import RPi.GPIO as GPIO

PWX_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(PWX_PIN, GPIO.OUT)

def toggle_power():
    GPIO.output(PWX_PIN, GPIO.LOW)  # Pull the pin low
    time.sleep(2)  # Wait for 2 seconds (this will turn the module on/off)
    GPIO.output(PWX_PIN, GPIO.HIGH)  # Release the pin

# Function to send AT command and receive response
def send_at_command(command, delay=5):
    print(f"Sending: {command}")
    ser.write((command + "\r\n").encode())  # Send command to SIM800
    time.sleep(delay)  # Wait for the response
    response = ""
    while ser.in_waiting > 0:
        response += ser.read(ser.in_waiting).decode()  # Read available response
    print(f"Response: {response}")
    return response

# Set up the serial connection (adjust port if necessary)
ser = serial.Serial("/dev/ttyS0", 9600, timeout=3)  # Use /dev/serial0 for GPIO on Raspberry Pi

def initialize_http():
    # 1. Terminate any previous session
    send_at_command("AT+HTTPTERM", 1)
    
    # 2. Retry mechanism for initializing HTTP service
    max_retries = 3
    retries = 0
    while retries < max_retries:
        response = send_at_command("AT+HTTPINIT", 2)
        if "OK" in response:
            print("HTTP service initialized successfully.")
            break
        else:
            retries += 1
            print(f"Retry {retries}/{max_retries}: Error initializing HTTP service.")
            if retries >= max_retries:
                print("Failed to initialize HTTP service after maximum retries.")
                return False
    
    # 3. Set parameters for GPRS
    send_at_command('AT+HTTPPARA="CID",1', 1)

    # 4. Enable HTTPS
    send_at_command("AT+HTTPSSL=1", 1)
    
    # 5. Set URL for the HTTP request (try with a different domain)
    website = "https://script.google.com/macros/s/AKfycbzToJ2en2NCraeKdaipUhHWLWZhr3tF5hQb_dFUu3ZCz6hJoeg8u_5fSUJFEDqrkEs/exec?date=10/10/2024&time=09:17&value=306"  # You can change this to another domain for testing
    send_at_command(f'AT+HTTPPARA="URL","{website}"', 2)
    
    return True

def send_http_request():
    # 6. Send GET request
    response = send_at_command("AT+HTTPACTION=0", 10)  # 10 sec delay for possible response
    if "+HTTPACTION: 0,200" in response:
        print("HTTP request successful!")
    else:
        print("HTTP request failed.")
        return False

    return True

def read_http_response():
    # 7. Read the HTTP response body
    response = send_at_command("AT+HTTPREAD", 5)
    print(f"Response Body: {response}")

def terminate_http_session():
    # 8. Terminate the HTTP session
    send_at_command("AT+HTTPTERM", 1)
    print("HTTP session terminated.")

def main():
    toggle_power()
    time.sleep(10)
    
    # 1. Check if GPRS is attached
    send_at_command("AT+CGATT?", 1)

    # 2. Check IP status
    send_at_command("AT+CIPSTATUS", 1)

    # 3. Set up GPRS PDP context
    send_at_command('AT+SAPBR=3,1,"CONTYPE","GPRS"', 1)
    send_at_command('AT+SAPBR=3,1,"APN","65501"', 1)  # Use correct APN for your carrier
    send_at_command("AT+SAPBR=1,1", 5)
    
    # 4. Confirm PDP context activation
    send_at_command("AT+SAPBR=2,1", 1)

    # 5. Initialize HTTP service and retry if failed
    if not initialize_http():
        print("HTTP initialization failed. Exiting program.")
        return

    # 6. Send HTTP request
    if send_http_request():
        # 7. Read HTTP response
        read_http_response()

    # 8. Terminate HTTP session
    terminate_http_session()
    
    toggle_power()

if __name__ == "__main__":
    main()