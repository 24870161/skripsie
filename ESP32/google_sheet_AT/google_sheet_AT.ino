#define TINY_GSM_MODEM_SIM800 // Define the GSM modem model
#include <TinyGsmClient.h>
#include <SoftwareSerial.h>

#define MODEM_TX 43
#define MODEM_RX 44
#define PWX_PIN 14 // Define your PWX pin

// Your Google Script Web App URL (use HTTPS)
const char* googleScriptUrl = "https://script.google.com/macros/s/AKfycbwEldma6HhCQdfZxw1kImYbz3nXpQdGeVEB6ynq-jXztRBqc8kyUbnORgoqQmGZOpU/exec?value=";

// Your SIM card APN
const char apn[] = "65501";  // Adjust as necessary
const char gprsUser[] = "";
const char gprsPass[] = "";

// Initialize the GSM modem
SoftwareSerial SerialAT(MODEM_RX, MODEM_TX);
TinyGsm modem(SerialAT);
TinyGsmClient client(modem);

void setup() {
    Serial.begin(115200);
    delay(10);
    
    // Power on the module
    pinMode(PWX_PIN, OUTPUT);
    pinMode(21, OUTPUT);
    Serial.println("Powering on the module...");
    digitalWrite(PWX_PIN, LOW);
    delay(2000); // Wait for 2 seconds
    digitalWrite(PWX_PIN, HIGH);
    delay(2000); // Wait for the module to power up

    // Start the modem
    Serial.println("Starting the modem...");
    SerialAT.begin(9600);
    if (!modem.restart()) {
        Serial.println("Failed to start the modem.");
        return;
    }
    Serial.println("Modem started successfully.");

    // Connect to the GPRS network
    Serial.println("Connecting to GPRS...");
    if (modem.gprsConnect(apn, gprsUser, gprsPass)) {
        Serial.println("GPRS connected successfully!");
    } else {
        Serial.println("Failed to connect to GPRS.");
        return;
    }

    // Send value
    sendData(111); // Example value to send

    digitalWrite(PWX_PIN, LOW);
    delay(2000); // Wait for 2 seconds
    digitalWrite(PWX_PIN, HIGH);
    digitalWrite(21, HIGH);
}

void loop() {
    // Nothing to do in loop for now
}

void sendData(int value) {
    Serial.println("==========");
    Serial.print("Connecting to ");
    Serial.println("Google Script");

    // Initialize HTTP service
    sendManualATCommand("AT+HTTPINIT");

    // Set the GPRS context
    sendManualATCommand("AT+HTTPPARA=\"CID\",1");

    // Set the URL for the request
    String url = String("\"") + googleScriptUrl + String(value) + String("\"");
    String command = "AT+HTTPPARA=\"URL\"," + url; // Create the full command

    sendManualATCommand(command.c_str()); // Pass the command as a C-style string

    // Enable HTTPS
    sendManualATCommand("AT+HTTPSSL=1");

    // Start the HTTP action (GET request)
    sendManualATCommand("AT+HTTPACTION=0");

    // Read the response
    sendManualATCommand("AT+HTTPREAD");

    // Terminate HTTP service
    sendManualATCommand("AT+HTTPTERM");
}

void sendManualATCommand(const char* command) {
    SerialAT.println(command);
    delay(2500);  // Increased delay for proper response

    while (SerialAT.available()) {
        String response = SerialAT.readString();
        Serial.println("Response: " + response);
    }
}
