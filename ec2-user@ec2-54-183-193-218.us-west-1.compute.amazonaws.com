from flask import Flask, jsonify, request, abort
import psutil
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging

app = Flask(__name__)

# Configuration
API_KEY = os.getenv('API_KEY', 'your_default_api_key')  # Replace with a secure method of API key storage

# Setup Flask-Limiter for rate limiting
limiter = Limiter(
    get_remote_address,  # Identify users by their IP address
    app=app,
    default_limits=["200 per day", "50 per hour"]  # Global limit for all routes
)

# Setup logging
logging.basicConfig(level=logging.INFO, filename='app.log',
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Helper function for API key validation
def check_api_key():
    api_key = request.headers.get('X-API-KEY')
    if api_key != API_KEY:
        abort(401, description="Invalid API Key")

# CPU Usage
@app.route('/cpu', methods=['GET'])
@limiter.limit("10 per minute")
def cpu_usage():
    check_api_key()
    cpu_percent = psutil.cpu_percent(interval=1)
    logging.info("CPU usage requested")
    return jsonify(cpu_usage=cpu_percent)

# Memory Usage
@app.route('/memory', methods=['GET'])
@limiter.limit("10 per minute")
def memory_usage():
    check_api_key()
    memory = psutil.virtual_memory()
    logging.info("Memory usage requested")
    return jsonify(memory_usage=memory.percent)

# Disk Usage
@app.route('/disk', methods=['GET'])
@limiter.limit("10 per minute")
def disk_usage():
    check_api_key()
    disk = psutil.disk_usage('/')
    logging.info("Disk usage requested")
    return jsonify(disk_usage=disk.percent)

# Bandwidth Usage (Placeholder)
@app.route('/bandwidth', methods=['GET'])
@limiter.limit("10 per minute")
def bandwidth_usage():
    check_api_key()
    net_io = psutil.net_io_counters()
    bandwidth_used = net_io.bytes_sent + net_io.bytes_recv  # Simplified measure of bandwidth usage
    logging.info("Bandwidth usage requested")
    return jsonify(bandwidth_usage=bandwidth_used)

if __name__ == '__main__':
    app.run(debug=True)
