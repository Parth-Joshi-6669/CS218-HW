from flask import Flask, jsonify, request, render_template, abort
import psutil
import duo_web
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import traceback

app = Flask(__name__)

# Duo configuration values (updated terminology)
DUO_CLIENT_ID = os.getenv('DUO_CLIENT_ID', 'DINXUVNAYC6Z463C06GN')       
DUO_CLIENT_SECRET = os.getenv('DUO_CLIENT_SECRET', 'GUQ596dHlbMtYtzn53jOwHvXaCLbMHzXr6E0WvCM')  
DUO_API_HOST = os.getenv('DUO_API_HOST', 'api-b3180646.duosecurity.com') 


# Setup Flask-Limiter for rate limiting
limiter = Limiter(
    get_remote_address,  # Identify users by their IP address
    app=app,
    default_limits=["200 per day", "50 per hour"]  # Global limit for all routes
)

# Example user authentication route (Step 1)
@app.route('/auth')
def auth():
    username = request.args.get('username')
    
    # Check if the username is valid in your app logic
    if not username:
        return "Username is required", 400
    
    # Generate the Duo sig_request to send to the client
    #sig_request = duo_web.sign_request(DUO_CLIENT_ID, DUO_CLIENT_SECRET, username)


    try:
        sig_request = duo_web.sign_request(DUO_CLIENT_ID, DUO_CLIENT_SECRET, username)
    except Exception as e:
        print("Error in Duo sign_request:")
        traceback.print_exc()  # This will print the full traceback of the error
        abort(500)



    # Render the Duo iframe with the sig_request and Duo host
    return render_template('duo_iframe.html', sig_request=sig_request, duo_host=DUO_API_HOST)

# Route to verify the Duo response (Step 4)
@app.route('/verify_duo', methods=['POST'])
def verify_duo():
    sig_response = request.form.get('sig_response')
    
    # Verify the response from Duo
    authenticated_user = duo_web.verify_response(DUO_CLIENT_ID, DUO_CLIENT_SECRET, sig_response)

    if authenticated_user:
        return jsonify({
            'message': 'Duo authentication successful',
            'username': authenticated_user
        })
    else:
        return jsonify({
            'message': 'Duo authentication failed'
        }), 401

# Function to verify the Duo sig_response before accessing the system stats endpoints
def check_duo_auth():
    sig_response = request.form.get('sig_response')
    authenticated_user = duo_web.verify_response(DUO_CLIENT_ID, DUO_CLIENT_SECRET, sig_response)
    
    if not authenticated_user:
        abort(401, description="Duo Authentication Failed")
    return authenticated_user

# CPU Usage Endpoint with rate limiting (10 requests per minute)
@app.route('/cpu', methods=['POST'])
@limiter.limit("10 per minute")
def get_cpu_usage():
    check_duo_auth()  # Ensure Duo 2FA authentication
    cpu_percent = psutil.cpu_percent(interval=1)
    return jsonify({'cpu_percent': cpu_percent})

# Memory Usage Endpoint with rate limiting (10 requests per minute)
@app.route('/memory', methods=['POST'])
@limiter.limit("10 per minute")
def get_memory_usage():
    check_duo_auth()  # Ensure Duo 2FA authentication
    memory_info = psutil.virtual_memory()
    return jsonify({'memory_used_percent': memory_info.percent})

# Disk Usage Endpoint with rate limiting (10 requests per minute)
@app.route('/disk', methods=['POST'])
@limiter.limit("10 per minute")
def get_disk_usage():
    check_duo_auth()  # Ensure Duo 2FA authentication
    disk_info = psutil.disk_usage('/')
    return jsonify({'disk_used_percent': disk_info.percent})

# Network Bandwidth Usage Endpoint with rate limiting (10 requests per minute)
@app.route('/network', methods=['POST'])
@limiter.limit("10 per minute")
def get_network_usage():
    check_duo_auth()  # Ensure Duo 2FA authentication
    net_io = psutil.net_io_counters()
    bandwidth_used = {
        'bytes_sent': net_io.bytes_sent,
        'bytes_received': net_io.bytes_recv
    }
    return jsonify(bandwidth_used)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)