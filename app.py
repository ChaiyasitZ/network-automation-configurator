from flask import Flask, render_template, request, jsonify
import paramiko
import time

app = Flask(__name__)

# Global variables to store the SSH client and connection info
ssh = None
ssh_details = {}

def connect_ssh():
    """Establishes an SSH connection using the stored details."""
    global ssh, ssh_details
    if ssh is not None:
        ssh.close()  # Close any existing session first to free up resources
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ssh_details['ip'], username=ssh_details['username'], password=ssh_details['password'])
    except Exception as e:
        raise ConnectionError(f"Failed to establish SSH connection: {e}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect', methods=['POST'])
def connect():
    global ssh_details
    data = request.json
    ip = data['ip']
    username = data['username']
    password = data['password']

    # Store SSH details for later reconnection if needed
    ssh_details = {'ip': ip, 'username': username, 'password': password}

    try:
        # Attempt to connect
        connect_ssh()
        return jsonify({"status": "Connected successfully!"}), 200
    except Exception as e:
        return jsonify({"status": f"Connection failed: {e}"}), 500

@app.route('/execute_command', methods=['POST'])
def execute_command():
    global ssh
    if ssh is None:
        return jsonify({"output": "Not connected to any device"}), 500

    # Check if the SSH transport is active, and reconnect if necessary
    try:
        if not ssh.get_transport().is_active():
            connect_ssh()  # Reconnect if the session is no longer active
    except Exception as e:
        return jsonify({"output": f"Connection error: {e}"}), 500

    data = request.json
    command = data['command']

    try:
        # Execute the command on the remote device
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode() + stderr.read().decode()
        return jsonify({"output": output}), 200
    except paramiko.ChannelException as e:
        # Handle resource shortage exception by closing and reopening the connection
        if "Resource shortage" in str(e):
            # Wait for a moment and try again
            time.sleep(2)
            try:
                connect_ssh()  # Try reconnecting
                stdin, stdout, stderr = ssh.exec_command(command)
                output = stdout.read().decode() + stderr.read().decode()
                return jsonify({"output": output}), 200
            except Exception as reconnect_error:
                return jsonify({"output": f"Reconnection failed: {reconnect_error}"}), 500
        else:
            return jsonify({"output": f"SSH Channel error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"output": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
