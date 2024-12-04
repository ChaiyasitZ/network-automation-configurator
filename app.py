from flask import Flask, render_template, request, jsonify
import paramiko

app = Flask(__name__)

# Global variable to store the SSH client
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

    ssh_details = {'ip': ip, 'username': username, 'password': password}

    try:
        connect_ssh()
        return jsonify({"status": "Connected successfully!"}), 200
    except Exception as e:
        return jsonify({"status": f"Connection failed: {e}"}), 500

@app.route('/execute_command', methods=['POST'])
def execute_command():
    global ssh
    if ssh is None:
        return jsonify({"output": "Not connected to any device"}), 500

    try:
        if not ssh.get_transport().is_active():
            connect_ssh()
    except Exception as e:
        return jsonify({"output": f"Connection error: {e}"}), 500

    data = request.json
    command = data['command']

    try:
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode() + stderr.read().decode()
        return jsonify({"output": output}), 200
    except Exception as e:
        return jsonify({"output": f"Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
