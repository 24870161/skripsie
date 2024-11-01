//sheet deployment ID: AKfycbwVqMXdCQzHeYzheLjQdfNiru9HEFHSSQFN0p8VvQ3izVt4CFsVgpbqW1nlIaGxtbo
//sheet URL: https://script.google.com/macros/s/AKfycbwVqMXdCQzHeYzheLjQdfNiru9HEFHSSQFN0p8VvQ3izVt4CFsVgpbqW1nlIaGxtbo/exec

#define TINY_GSM_MODEM_SIM800
#include <TinyGsmClient.h>
#include <HardwareSerial.h>

#define MODEM_RX     44
#define MODEM_TX     43
#define MODEM_PWRKEY 14

TinyGsm modem(Serial2);

// Phone number and SMS text
const char phone_number[] = "+27730782908";  // Replace with your phone number
const char sms_text[] = "Ek maak vordering... ;)";

void setup() {
  Serial.begin(115200);
  delay(10);

  // Initialize the PWRKEY pin
  pinMode(MODEM_PWRKEY, OUTPUT);
  pinMode(21, OUTPUT);

  // Start communication with the GSM module
  Serial2.begin(9600, SERIAL_8N1, MODEM_RX, MODEM_TX);
  sendManualATCommand("AT+CPOWD=1");
  delay(3000);
  digitalWrite(MODEM_PWRKEY, LOW);
  delay(2000);  // Pull PWRKEY low for 1 second to power on the module
  digitalWrite(MODEM_PWRKEY, HIGH);

  Serial.println("Initializing modem...");

  // Turn off echo
  //sendManualATCommand("ATE0");

  // Send a basic AT command to check communication
  sendManualATCommand("AT");

  // Get module information
  sendManualATCommand("ATI");

  // Check SIM card status
  sendManualATCommand("AT+CPIN?");

  // Check signal quality
  sendManualATCommand("AT+CSQ"); 
  
  // List available networks
  sendManualATCommand("AT+COPS=?");

  // Manually select Vodacom network operator (replace "65501" with your network code)
  sendManualATCommand("AT+COPS=1,0,\"65501\"");

  // Check network registration status
  checkNetworkRegistration();

  Serial2.println("AT+CCLK?");
  delay(1000);
  // Read and parse the response
  while (Serial2.available()) {
    String response = Serial2.readString();
    Serial.println(response); // Debug output to see the response
    if (response.indexOf("+CCLK:") != -1) {
      setTimeOnESP32(response);
    }
  }

  //sendSMS();
  //digitalWrite(MODEM_PWRKEY, LOW);
  //delay(2000);  // Pull PWRKEY low for 1 second to power on the module
  //digitalWrite(MODEM_PWRKEY, HIGH);
  sendManualATCommand("AT+CPOWD=1");
  digitalWrite(21, HIGH);
}

void sendManualATCommand(const char* command) {
  Serial2.println(command);
  delay(5000);  // Increased delay for proper response

  while (Serial2.available()) {
    String response = Serial2.readString();
    Serial.println("Response: " + response);
  }
}

void setTimeOnESP32(String response) {
  int year, month, day, hour, minute, second;
  char timezone[6];
  
  // Example response: +CCLK: "23/09/26,15:30:45+08"
  int startIndex = response.indexOf("\"") + 1;
  int endIndex = response.indexOf("\"", startIndex);
  String datetime = response.substring(startIndex, endIndex);
  
  // Parse the date and time (assuming the format is correct)
  sscanf(datetime.c_str(), "%d/%d/%d,%d:%d:%d%s", &year, &month, &day, &hour, &minute, &second, timezone);

  // Adjust the year for 4 digits
  year += 2000;

  // Convert parsed values to time_t format (for keeping time on ESP32)
  struct tm t;
  t.tm_year = year - 1900;  // Years since 1900
  t.tm_mon = month - 1;     // Months since January (0-11)
  t.tm_mday = day;
  t.tm_hour = hour;
  t.tm_min = minute;
  t.tm_sec = second;
  time_t timeSinceEpoch = mktime(&t);

  // Set the internal ESP32 clock using the time from the SIM800C
  struct timeval now = { .tv_sec = timeSinceEpoch };
  settimeofday(&now, NULL);

  Serial.println("Time updated from SIM800C");
}

void checkNetworkRegistration() {
  while (true) {
    Serial2.println("AT+CREG?");
    delay(10000);  // Increased delay for proper response

    while (Serial2.available()) {
      String response = Serial2.readString();
      Serial.println("Response: " + response);
      if (response.indexOf("+CREG: 0,1") != -1 || response.indexOf("+CREG: 0,5") != -1) {
        Serial.println("Modem registered on the network.");
        return;
      }
    }
    Serial.println("Waiting for network registration...");
  }
}

void sendSMS() {
  Serial.println("Sending SMS...");
 
  // Send the SMS
  bool res = modem.sendSMS(phone_number, sms_text);
 
  if (res) {
    Serial.println("SMS sent successfully!");
  } else {
    Serial.println("Failed to send SMS.");
  }
}

void loop() {
  time_t now = time(nullptr);
  struct tm* currentTime = localtime(&now);
  Serial.printf("Current time: %02d:%02d:%02d\n", currentTime->tm_hour, currentTime->tm_min, currentTime->tm_sec);
  delay(1000);
}
