from flask import Flask, render_template, request, redirect, url_for
from netmiko import ConnectHandler

app = Flask(__name__)

# Function to connect to the device
def connect_device(device):
    try:
        # Ensure the device dictionary contains a valid IP address or hostname
        if not device.get('host'):
            return "Error: Device IP (host) is missing."
        return ConnectHandler(**device)
    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    device_ip = request.form['device_ip']
    username = request.form['username']
    password = request.form['password']

    # Check if device_ip, username, and password are provided
    if not device_ip or not username or not password:
        return render_template('index.html', error="Device IP, Username, and Password are required.")

    device = {
        'device_type': 'cisco_ios',  # Change to the appropriate device type
        'host': device_ip,
        'username': username,
        'password': password,
    }

    # Attempt to connect to the device
    connection = connect_device(device)
    if isinstance(connection, str):  # If an error message is returned
        return render_template('index.html', error=connection)  # Show the error
    else:
        # Connection successful, proceed to configuration
        return redirect(url_for('configure', device_ip=device_ip, username=username, password=password))

@app.route('/configure', methods=['GET', 'POST'])
def configure():
    device_ip = request.args.get('device_ip')
    username = request.args.get('username')
    password = request.args.get('password')

    # Ensure the device_ip is passed
    if not device_ip:
        return render_template('index.html', error="Device IP is missing.")

    if request.method == 'POST':
        output = ""
        config_commands = request.form['config_commands'].splitlines()
        device = {
            'device_type': 'cisco_ios',
            'host': device_ip,
            'username': username,
            'password': password,
        }
        
        connection = connect_device(device)
        if isinstance(connection, str):  # If there was an error
            output = f"Error: {connection}"
        else:
            output = connection.send_config_set(config_commands)
            connection.disconnect()

        return render_template('configure.html', output=output)
    return render_template('configure.html')

if __name__ == '__main__':
    app.run(debug=True)
