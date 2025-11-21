# 🧊 Cold-Chain Monitoring System (IoT + Cloud + AI + Blockchain)

A complete end-to-end Cold-Chain Monitoring platform built using:

- **ESP32 IoT sensor**
- **Replit backend (Python)**
- **Live dashboard (HTML/CSS/JS)**
- **Gemini AI Agent**
- **Ethereum Sepolia blockchain (smart contract)**
- **Mock sensor simulator**

This system monitors refrigerated environments (temperature, humidity, door status, battery) and automatically sends alerts through both the dashboard and the blockchain for tamper-proof logging.

---

## 🚀 System Features

### 🔹 1. ESP32 Real-Time Sensor Data  
- Reads temperature, humidity, battery, and door state  
- Sends live data to the Replit backend

### 🔹 2. Cloud Backend (Python + Web3)  
- Stores readings  
- Detects bad conditions (high temp, low temp, door open)  
- Writes incidents to blockchain  
- Provides API for dashboard + AI agent  
- Exposes `/api/data` and `/api/blockchain/alerts`

### 🔹 3. Tamper-Proof Blockchain Logging  
Smart contract: **ColdChainProof.sol**  
Stores:
- device ID  
- alert type  
- timestamp  
- SHA-256 data hash  
- immutable on-chain record  

### 🔹 4. Dashboard (Frontend)  
- Real-time charts  
- Device table  
- Blockchain audit trail  
- Etherscan links for each alert

### 🔹 5. Mock Sensor Data  
A complete Python simulator that mimics ESP32 data.

### 🔹 6. AI Agent (Gemini)  
- Explains alerts  
- Checks blockchain integrity  
- Generates reports  
- Compares historical vs real-time data  

---

## 📦 Project Folder Structure

