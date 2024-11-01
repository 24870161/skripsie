import requests
import subprocess
import time

def fetch_time_from_api():
    try:
        # Send a request to the World Time API
        response = requests.get("http://worldtimeapi.org/api/ip")
        if response.status_code == 200:
            data = response.json()
            datetime_str = data['datetime']
            #print(f"Fetched datetime: {datetime_str}")
            return datetime_str
        else:
            #print("Failed to fetch time from API.")
            return None
    except Exception as e:
        #print(f"Error fetching time: {e}")
        return None

def set_rpi_datetime(date_time_str):
    # Extract date and time in a format usable by the 'date' command
    date_time_str = date_time_str.split(".")[0]  # Remove milliseconds
    formatted_datetime = date_time_str.replace("T", " ")  # Format it for `date`

    # Set the Raspberry Pi date and time
    subprocess.run(["sudo", "date", "-s", formatted_datetime])
    #print(f"Raspberry Pi date and time set to: {formatted_datetime}")

def main():
    #print("Fetching date and time from World Time API...")
    date_time_str = fetch_time_from_api()

    if date_time_str:
        set_rpi_datetime(date_time_str)
        subprocess.run(["date"])  # Verify the set date and time

if __name__ == "__main__":
    main()
