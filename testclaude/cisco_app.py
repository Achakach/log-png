from flask import Flask, render_template, request, jsonify
import json

app = Flask(__name__)


def get_cisco_config(host, username, password, enable_password=None):
    """
    Connect to Cisco switch via netmiko and fetch running config.
    Returns tuple: (success, config_or_error, message)
    """
    try:
        from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

        # Device configuration
        device = {
            'device_type': 'cisco_ios',
            'host': host,
            'username': username,
            'password': password,
            'secret': enable_password or password,
            'session_timeout': 30,
            'timeout': 30,
        }

        # Connect to device
        conn = ConnectHandler(**device)

        # Enable mode
        conn.enable()

        # Get running config
        config = conn.send_command('show running-config', use_textfsm=False)

        # Disconnect
        conn.disconnect()

        if config:
            return (True, config, "Config retrieved successfully")
        else:
            return (False, "", "Empty config returned")

    except NetmikoAuthenticationException:
        return (False, "", "Authentication failed. Check username/password.")
    except NetmikoTimeoutException:
        return (False, "", "Connection timed out. Check IP address and network connectivity.")
    except Exception as e:
        error_msg = str(e)
        if 'Connection refused' in error_msg:
            return (False, "", "Connection refused. SSH may not be enabled on the device.")
        return (False, error_msg, "An error occurred while connecting to the switch")


@app.route('/', methods=['GET', 'POST'])
def index():
    """Main page - form to enter switch details and display config."""
    config = None
    error = None
    switch_info = None

    if request.method == 'POST':
        host = request.form.get('host', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        enable_password = request.form.get('enable_password', '')

        if not all([host, username, password]):
            error = "Please fill in all required fields (Host, Username, Password)"
        else:
            switch_info = {
                'host': host,
                'username': username
            }

            success, result, message = get_cisco_config(
                host, username, password, enable_password or password
            )

            if success:
                config = result
            else:
                error = f"{message}: {result}" if result else message

    return render_template('cisco_config.html',
                         config=config,
                         error=error,
                         switch_info=switch_info)


@app.route('/api/config', methods=['POST'])
def api_get_config():
    """API endpoint to get config - returns JSON."""
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'No JSON data provided'}), 400

    host = data.get('host', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    enable_password = data.get('enable_password', '')

    if not all([host, username, password]):
        return jsonify({
            'success': False,
            'error': 'Missing required fields: host, username, password'
        }), 400

    success, result, message = get_cisco_config(
        host, username, password, enable_password or password
    )

    if success:
        return jsonify({
            'success': True,
            'message': message,
            'config': result,
            'switch': {'host': host, 'username': username}
        })
    else:
        return jsonify({
            'success': False,
            'error': message,
            'details': result
        }), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    # Check if netmiko is available
    try:
        import netmiko
        netmiko_version = netmiko.__version__
        netmiko_installed = True
    except ImportError:
        netmiko_installed = False
        netmiko_version = 'Not installed'
    except Exception as e:
        netmiko_installed = False
        netmiko_version = str(e)

    return jsonify({
        'status': 'healthy',
        'netmiko_installed': netmiko_installed,
        'netmiko_version': netmiko_version
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
