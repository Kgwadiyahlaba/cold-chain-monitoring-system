// esp32/esp32_coldchain.ino
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// ----- CONFIG -----
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASS";
const char* endpoint = "https://cold-chain-monitor.replit.app/api/data"; // replace if needed

String deviceId = "esp32_coldchain_01";

void setup() {
  Serial.begin(115200);
  delay(100);
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(400);
    Serial.print(".");
  }
  Serial.println(" connected");
}

void loop() {
  float temp = random(-50, 100) / 10.0; // -5.0 to +10.0
  float hum = random(60, 95);
  float batt = 3.7; // static for example
  String door = (random(0, 100) < 5) ? "open" : "closed";

  StaticJsonDocument<256> doc;
  doc["device_id"] = deviceId;
  doc["timestamp"] = "2025-11-21T00:00:00Z";
  doc["temperature_c"] = temp;
  doc["humidity_percent"] = hum;
  doc["battery_voltage"] = batt;
  doc["door_state"] = door;

  String payload;
  serializeJson(doc, payload);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(endpoint);
    http.addHeader("Content-Type", "application/json");
    int httpResponseCode = http.POST(payload);
    Serial.print("POST code: ");
    Serial.println(httpResponseCode);
    String resp = http.getString();
    Serial.print("Response: ");
    Serial.println(resp);
    http.end();
  }

  delay(15000); // wait 15 seconds
}
