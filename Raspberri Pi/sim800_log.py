import serial
import time
import RPi.GPIO as GPIO
import subprocess
import sys

PWX_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PWX_PIN, GPIO.OUT)

ser = serial.Serial("/dev/ttyS0", 115200, timeout=3)

def toggle_power():
    GPIO.output(PWX_PIN, GPIO.LOW)
    time.sleep(2)
    GPIO.output(PWX_PIN, GPIO.HIGH)

def send_at_command(command, delay=5):
    #print(f"Sending: {command}")
    ser.write((command + "\r\n").encode())
    time.sleep(delay)
    response = ""
    while ser.in_waiting > 0:
        response += ser.read(ser.in_waiting).decode()
    #print(f"Response: {response}")
    return response

def check_module_startup():
    max_retries = 3
    retries = 0
    while retries < max_retries:
        response = send_at_command("AT", 2)
        if "OK" in response:
            #print("Module started successfully.")
            return True
        else:
            #print("Failed to start module, retrying...")
            toggle_power()
            time.sleep(10)
            retries += 1
    #print("Module failed to start after maximum retries.")
    return False

def initialize_http():
    send_at_command("AT+HTTPTERM", 1)
    max_retries = 3
    retries = 0
    while retries < max_retries:
        response = send_at_command("AT+HTTPINIT", 2)
        if "OK" in response:
            #print("HTTP service initialized successfully.")
            break
        else:
            retries += 1
            #print(f"Retry {retries}/{max_retries}: Error initializing HTTP service.")
            if retries >= max_retries:
                #print("Failed to initialize HTTP service after maximum retries.")
                return False
    
    #send_at_command('AT+HTTPPARA="CID",1', 1)
    send_at_command("AT+HTTPSSL=1", 1)
    return True

def send_http_request(vehicles_counted, date, rpi_time):
    website = f"https://script.google.com/macros/s/AKfycbzToJ2en2NCraeKdaipUhHWLWZhr3tF5hQb_dFUu3ZCz6hJoeg8u_5fSUJFEDqrkEs/exec?date={date}&time={rpi_time}&value={vehicles_counted}"
    send_at_command(f'AT+HTTPPARA="URL","{website}"', 2)
    
    response = send_at_command("AT+HTTPACTION=0", 20)
    #if "+HTTPACTION: 0,200" in response:
        #print("HTTP request successful!")
    #else:
        #print("HTTP request failed.")
        #return False
    #return True

def get_rpi_datetime():
    current_time = subprocess.check_output("date +'%d/%m/%Y %H:%M'", shell=True).decode().strip()
    date, rpi_time = current_time.split(" ")
    #print(f"Raspberry Pi Date: {date}, Time: {rpi_time}")
    return date, rpi_time

def main(vehicles_counted=0):
    date, rpi_time = get_rpi_datetime()
    
    toggle_power()
    time.sleep(10) #Give the module some time to start up and connect to the network

    if not check_module_startup():
        #print("Exiting due to startup failure.")
        return

    #send_at_command("AT+CGATT?", 1)
    send_at_command('AT+SAPBR=3,1,"CONTYPE","GPRS"', 3)
    #send_at_command('AT+SAPBR=3,1,"APN","65501"', 1)
    send_at_command("AT+SAPBR=1,1", 5)
    #send_at_command("AT+SAPBR=2,1", 1)

    if not initialize_http():
        #print("HTTP initialization failed. Exiting program.")
        return

    #if send_http_request(vehicles_counted, date, rpi_time):
        #print("Data uploaded to Google Sheet.")
    send_http_request(vehicles_counted, date, rpi_time)
    
    send_at_command("AT+HTTPTERM", 1)
    #print("HTTP session terminated.")
    toggle_power()

if __name__ == "__main__":
    # If vehicles counted is provided as an argument, use it; otherwise default to 0
    vehicles_counted = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    main(vehicles_counted)
