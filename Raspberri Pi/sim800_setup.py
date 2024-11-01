import serial
import time
import RPi.GPIO as GPIO
import subprocess

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
    print(f"Sending: {command}")
    ser.write((command + "\r\n").encode())
    time.sleep(delay)
    response = ""
    while ser.in_waiting > 0:
        response += ser.read(ser.in_waiting).decode()
    print(f"Response: {response}")
    return response

def check_module_startup():
    max_retries = 3
    retries = 0
    while retries < max_retries:
        response = send_at_command("AT", 2)
        if "OK" in response:
            print("Module started successfully.")
            return True
        else:
            print("Failed to start module, retrying...")
            toggle_power()
            time.sleep(10)
            retries += 1
    print("Module failed to start after maximum retries.")
    return False

def check_network_registration():
    response = send_at_command("AT+CREG?", 2)
    if "+CREG: 0,1" in response:
        #print("Module is registered on the network.")
        return True
    else:
        print("Module is not registered.")
        return False
    
def get_datetime_from_sim800():
    response = send_at_command("AT+CCLK?", 2)
    if "+CCLK" in response:
        date_time_str = response.split('"')[1]
        print(f"SIM800 Date-Time: {date_time_str}")
        return date_time_str
    return None

def set_rpi_datetime(date_time_str):
    dt_parts = date_time_str.split(",")
    date = dt_parts[0].split("/")
    time = dt_parts[1].split("+")[0]

    formatted_date = f"20{date[0]}-{date[1]}-{date[2]}"
    formatted_time = time

    subprocess.run(["sudo", "date", "-s", f"{formatted_date} {formatted_time}"])
    print(f"Raspberry Pi Date-Time set to: {formatted_date} {formatted_time}")

def main():
    toggle_power()
    time.sleep(10)

    if check_module_startup():
        print("Module is up and running!")
        if check_network_registration():
            print("Fetching date and time from SIM800...")
            date_time_str = get_datetime_from_sim800()
            if date_time_str:
               set_rpi_datetime(date_time_str)
            else:
                print("Failed to retrieve date and time from SIM800.")
        else:
            print("SIM800 is not registered on the network.")
    else:
        print("Exiting, module could not be started.")
        
    toggle_power()

if __name__ == "__main__":
    main()
