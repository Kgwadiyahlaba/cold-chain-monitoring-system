# backend/main.py
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Web3 imports
from web3 import Web3

# Optional Gemini import (if installed)
# import google.generativeai as genai

# --- Configuration & paths ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
HISTORY_FILE = DATA_DIR / "history.json"
ABI_FILE = BASE_DIR / "contract_abi.json"

DATA_DIR.mkdir(exist_ok=True, parents=True)
if not HISTORY_FILE.exists():
    HISTORY_FILE.write_text("[]", encoding="utf-8")

# Load environment variables (Replit uses secrets/env)
INFURA_URL = os.getenv("SEPOLIA_RPC", "")  # e.g. https://sepolia.infura.io/v3/XXXXX
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS", "")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")  # KEEP SECRET
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # optional

# Initialize Flask
app = Flask(__name__, static_folder=str(BASE_DIR.parent / "dashboard"), static_url_path="/")
CORS(app)

# Initialize web3 if available
web3 = None
contract = None
if INFURA_URL and CONTRACT_ADDRESS and ABI_FILE.exists():
    try:
        web3 = Web3(Web3.HTTPProvider(INFURA_URL))
        with open(ABI_FILE, 'r', encoding='utf-8') as f:
            abi = json.load(f)
        contract = web3.eth.contract(address=web3.to_checksum_address(CONTRACT_ADDRESS), abi=abi)
        print("Web3 initialized. Connected:", web3.is_connected())
    except Exception as e:
        print("Web3 init error:", e)

# --- Helper functions ---
def load_history():
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def append_history(record):
    history = load_history()
    history.append(record)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def compute_data_hash(payload: dict) -> str:
    j = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(j.encode("utf-8")).hexdigest()

def write_alert_to_blockchain(device_id, alert_type, timestamp, data_hash):
    """
    Signs and sends a transaction to the ColdChainProof.storeAlert function.
    Returns transaction hash (hex) or None on failure.
    """
    if not web3 or not contract or not WALLET_ADDRESS or not PRIVATE_KEY:
        print("Blockchain not configured. Skipping on-chain write.")
        return None

    try:
        nonce = web3.eth.get_transaction_count(WALLET_ADDRESS)
        txn = contract.functions.storeAlert(
            device_id,
            alert_type,
            timestamp,
            data_hash
        ).build_transaction({
            "from": WALLET_ADDRESS,
            "nonce": nonce,
            "gas": 300000,
            "gasPrice": web3.eth.gas_price
        })
        signed = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
        tx_hex = web3.to_hex(tx_hash)
        print("Stored alert on-chain:", tx_hex)
        return tx_hex
    except Exception as e:
        print("Error writing to blockchain:", e)
        return None

# --- API routes ---
@app.route("/api/data", methods=["POST"])
def receive_data():
    """
    Accepts a sensor payload, stores it to history, detects alerts,
    optionally writes alerts to blockchain, and returns status.
    """
    body = request.get_json(force=True)
    required_keys = {"device_id", "timestamp", "temperature_c", "humidity_percent", "battery_voltage", "door_state"}
    if not body or not required_keys.issubset(set(body.keys())):
        return jsonify({"status":"error", "message":"invalid payload"}), 400

    # Normalize timestamp
    try:
        # if timestamp missing/invalid, add now
        dt = body.get("timestamp")
        # If timestamp not in ISO, just set current
        # For simplicity, always set to server UTC in record
        body["timestamp"] = datetime.utcnow().isoformat() + "Z"
    except Exception:
        body["timestamp"] = datetime.utcnow().isoformat() + "Z"

    # Append to history
    append_history(body)

    # Detect alerts
    alerts = []
    temp = float(body["temperature_c"])
    if temp > 8.0:
        alerts.append("HIGH_TEMP")
    if temp < -5.0:
        alerts.append("LOW_TEMP")
    if str(body.get("door_state","")).lower() == "open":
        alerts.append("DOOR_OPEN")

    tx_hashes = []
    for alert_type in alerts:
        data_hash = compute_data_hash(body)
        tx = write_alert_to_blockchain(body["device_id"], alert_type, body["timestamp"], data_hash)
        tx_hashes.append({"alert_type": alert_type, "tx_hash": tx, "data_hash": data_hash})

    return jsonify({"status":"ok", "message":"data received", "alerts": tx_hashes}), 200

@app.route("/api/latest", methods=["GET"])
def api_latest():
    history = load_history()
    if not history:
        return jsonify({}), 200
    return jsonify(history[-1]), 200

@app.route("/api/history", methods=["GET"])
def api_history():
    return jsonify(load_history()), 200

@app.route("/api/devices", methods=["GET"])
def api_devices():
    history = load_history()
    devices = {}
    for rec in history:
        dev = rec.get("device_id")
        devices[dev] = rec
    # return list of latest per device
    result = [{"device_id": k, "latest": v} for k,v in devices.items()]
    return jsonify(result), 200

@app.route("/api/blockchain/alerts", methods=["GET"])
def api_blockchain_alerts():
    """
    Reads alerts from on-chain contract using getAlertCount/getAlert.
    Returns a JSON array of alerts with optional txlink if tx hash known in history.
    """
    if not web3 or not contract:
        return jsonify({"status":"error","message":"blockchain not configured"}), 500

    try:
        count = contract.functions.getAlertCount().call()
        out = []
        for i in range(count):
            deviceId, alertType, timestamp, dataHash = contract.functions.getAlert(i).call()
            out.append({
                "index": i,
                "device_id": deviceId,
                "alert_type": alertType,
                "timestamp": timestamp,
                "data_hash": dataHash
            })
        return jsonify(out), 200
    except Exception as e:
        return jsonify({"status":"error","message":str(e)}), 500

@app.route("/api/ai", methods=["POST"])
def api_ai():
    """
    Simple AI agent wrapper. Accepts JSON: { "question": "..." }
    Reads local history and on-chain alerts and returns a summary.
    If GEMINI_API_KEY available, you may plug in google.generativeai calls.
    """
    body = request.get_json(force=True)
    question = body.get("question", "").strip()
    if not question:
        return jsonify({"status":"error","message":"no question provided"}), 400

    # Build a small context
    history = load_history()[-50:]  # last 50 readings
    blockchain_alerts = []
    if web3 and contract:
        try:
            count = contract.functions.getAlertCount().call()
            for i in range(max(0, count-20), count):
                a = contract.functions.getAlert(i).call()
                blockchain_alerts.append({
                    "device_id": a[0],
                    "alert_type": a[1],
                    "timestamp": a[2],
                    "data_hash": a[3]
                })
        except Exception:
            pass

    # Build a short answer locally (fallback) - basic rule-based
    answer = "I examined the recent data. "
    if "temperature" in question.lower() or "above" in question.lower():
        # simple check
        high = [r for r in history if float(r.get("temperature_c", -999)) > 8.0]
        if high:
            answer += f"Yes — there are {len(high)} recent readings above 8°C. "
        else:
            answer += "No recent readings above 8°C. "
    else:
        answer += "I can provide summary, list alerts, or verify blockchain proofs."

    # If Gemini key is available, you can call the model here (left as instruction)
    # Example (unexecuted):
    # if GEMINI_API_KEY:
    #     genai.configure(api_key=GEMINI_API_KEY)
    #     prompt = f"Question: {question}\nHistory: {history}\nOn-chain alerts: {blockchain_alerts}\nAnswer succinctly."
    #     model_response = genai.predict(model="models/text-bison-001", input=prompt)
    #     return jsonify({"answer": model_response.text}), 200

    return jsonify({
        "status":"ok",
        "answer": answer,
        "history_count": len(history),
        "blockchain_alerts_count": len(blockchain_alerts),
        "blockchain_alerts": blockchain_alerts
    }), 200

# Serve dashboard root
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_dashboard(path):
    # leave dashboard static files intact
    if path != "" and (BASE_DIR.parent / "dashboard" / path).exists():
        return send_from_directory(str(BASE_DIR.parent / "dashboard"), path)
    return send_from_directory(str(BASE_DIR.parent / "dashboard"), "index.html")

@app.route("/health")
def health():
    return jsonify({"status":"ok", "time": datetime.utcnow().isoformat()+"Z"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
