# Cisco Switch Config Viewer

Web application to fetch and display running configurations from Cisco switches.

## Requirements

- Python 3.10+
- Cisco IOS switches with SSH enabled

## Setup

1. Activate the virtual environment:
   ```bash
   .venv\Scripts\activate
   ```

2. Install dependencies (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python cisco_app.py
   ```

4. Open http://localhost:5000 in your browser

## Usage

1. Enter switch details:
   - **IP/Hostname**: Switch management IP address
   - **Username**: SSH username
   - **Password**: SSH password
   - **Enable Password**: (optional) Privilege escalation password

2. Click "Fetch Running Config" to retrieve the configuration

## API

### Get Config
```bash
curl -X POST http://localhost:5000/api/config \
  -H "Content-Type: application/json" \
  -d '{"host":"192.168.1.1","username":"admin","password":"secret"}'
```

### Health Check
```bash
curl http://localhost:5000/health
```
