#define TINY_GSM_MODEM_SIM800
#include <SoftwareSerial.h>
#include <TinyGsmClient.h>
#include <ArduinoJson.h>

// SIM800 module pins
#define MODEM_TX 43
#define MODEM_RX 44
#define PWX_PIN 14 // Define your PWX pin

// Your Google Script Web App URL
const char* googleScriptUrl = "https://script.google.com/macros/s/AKfycbxJOS3x7Ve0DUWNXje2nL2Day7OkUhd3V-Asx8Y44on_-Zlg9_XHA1uxcnGk_j99Q/exec";

// Your SIM card APN
const char apn[] = "65501";
const char gprsUser[] = "";
const char gprsPass[] = "";

// Initialize the GSM modem
SoftwareSerial SerialAT(MODEM_RX, MODEM_TX);
TinyGsm modem(SerialAT);
TinyGsmClient client(modem); // Use TinyGsmClientSecure for HTTPS

// Function to get date and time from SIM800 module
String getDateTime() {
  SerialAT.println("AT+CCLK?");
  delay(100);
  String response = "";
  while (SerialAT.available()) {
    char c = SerialAT.read();
    response += c;
  }

  // Parse the response to extract date and time
  int index = response.indexOf("\"");
  String dateTime = response.substring(index + 1, index + 20);
  return dateTime;
}

void setup() {
  Serial.begin(115200);
  delay(10);

  // Initialize PWX pin
  pinMode(PWX_PIN, OUTPUT);

  // Power on the module
  Serial.println("Powering on the module...");
  digitalWrite(PWX_PIN, LOW);
  delay(2000); // Wait for 2 seconds
  digitalWrite(PWX_PIN, HIGH);
  //delay(10000); // Wait for the module to power up

  // Start the modem
  Serial.println("Starting the modem...");
  SerialAT.begin(9600);
  if (modem.restart()) {
    Serial.println("Modem started successfully.");
  } else {
    Serial.println("Failed to start the modem.");
  }

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

  // Check network registration
  checkNetworkRegistration();

  // Connect to the GPRS network
  Serial.println("Connecting to GPRS...");
  if (modem.gprsConnect(apn, gprsUser, gprsPass)) {
    Serial.println("GPRS connected successfully.");
  } else {
    Serial.println("Failed to connect to GPRS.");
  }

  // Wait until GPRS is connected
  while (!modem.isGprsConnected()) {
    Serial.println("Waiting for GPRS connection...");
    delay(1000); // Wait for 1 second before checking again
  }

  Serial.println("GPRS connected successfully!");

  testHTTPConnection();
  delay(10000);
}

void loop() {
  if (modem.isGprsConnected()) {
    // Get the current date and time from the SIM800 module
    String dateTime = getDateTime();
    Serial.print("Current date and time: ");
    Serial.println(dateTime);

    // Create JSON data
    StaticJsonDocument<200> jsonDoc;
    jsonDoc["timestamp"] = dateTime;
    jsonDoc["value"] = analogRead(34); // Example sensor reading
    String jsonData;
    serializeJson(jsonDoc, jsonData);

    // Send data to Google Sheets
    Serial.println("Sending data to Google Sheets...");
    if (client.connect("script.google.com", 443)) { // Use port 443 for HTTPS
      client.println("POST /macros/s/AKfycbwVqMXdCQzHeYzheLjQdfNiru9HEFHSSQFN0p8VvQ3izVt4CFsVgpbqW1nlIaGxtbo/exec HTTP/1.1");
      client.println("Host: script.google.com");
      client.println("Content-Type: application/json");
      client.println("Content-Length: " + jsonData.length());
      client.println("Connection: close");
      client.println(); // End of headers
      client.println(jsonData); // Send the JSON data
    


      // Print the request
      Serial.print("POST ");
      Serial.print("/macros/s/AKfycbwVqMXdCQzHeYzheLjQdfNiru9HEFHSSQFN0p8VvQ3izVt4CFsVgpbqW1nlIaGxtbo/exec");
      Serial.println(" HTTP/1.1");
      Serial.print("Host: script.google.com\r\n");
      Serial.print("Content-Type: application/json\r\n");
      Serial.print("Content-Length: ");
      Serial.print(jsonData.length());
      Serial.print("\r\n\r\n");
      Serial.println(jsonData);

      // Read the response from the server
      while (client.connected()) {
        String line = client.readStringUntil('\n');
        if (line == "\r") {
          break;
        }
      }
      String response = client.readString();
      Serial.print("Response: ");
      Serial.println(response);

      Serial.println("Data sent successfully.");
    } else {
      Serial.println("Failed to connect to Google Sheets.");
    }
    client.stop();
  } else {
    Serial.println("GPRS not connected.");
  }
  delay(60000); // Send data every 60 seconds
}

void checkSignalStrength() {
  SerialAT.println("AT+CSQ");
  delay(100);
  while (SerialAT.available()) {
    Serial.write(SerialAT.read());
  }
}

void checkNetworkRegistration() {
  while (true) {
    SerialAT.println("AT+CREG?");
    delay(10000);  // Increased delay for proper response

    while (SerialAT.available()) {
      String response = SerialAT.readString();
      Serial.println("Response: " + response);
      if (response.indexOf("+CREG: 0,1") != -1 || response.indexOf("+CREG: 0,5") != -1) {
        Serial.println("Modem registered on the network.");
        return;
      }
    }
    Serial.println("Waiting for network registration...");
  }
}

void checkGPRSConnection() {
  SerialAT.println("AT+CGATT?");
  delay(100);
  while (SerialAT.available()) {
    Serial.write(SerialAT.read());
  }
}

void testHTTPConnection() {
  if (client.connect("example.com", 80)) {
    Serial.println("Connected to example.com");
    client.println("GET / HTTP/1.1");
    client.println("Host: example.com");
    client.println("Connection: close");
    client.println();

    while (client.connected()) {
      String line = client.readStringUntil('\n');
      Serial.println(line);
    }
    client.stop();
  } else {
    Serial.println("Failed to connect to example.com");
  }
}

void sendManualATCommand(const char* command) {
  SerialAT.println(command);
  delay(5000);  // Increased delay for proper response

  while (SerialAT.available()) {
    String response = SerialAT.readString();
    Serial.println("Response: " + response);
  }
}