import requests
import sys
import getpass

# Disable SSL warnings
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass


def get_api_key(panorama_host, username, password):
    key_url = f"https://{panorama_host}/api/?type=keygen&user={username}&password={password}"
    try:
        r = requests.get(key_url, verify=False, timeout=10)
        if '<key>' not in r.text:
            return None
        return r.text.split('<key>')[1].split('</key>')[0]
    except Exception as e:
        print(f"Error connecting to Panorama: {e}")
        return None

def main():
    print("=== Panorama Login Test ===\n")
    print("This script will test your Panorama login and display basic system information.")
    panorama_host = input("Enter Panorama IP or hostname: ").strip()
    print("You will be asked for your username and password.")

    # Credential check loop
    max_attempts = 3
    for attempt in range(1, max_attempts + 1):
        username = input("Enter username: ").strip()
        print("Please enter your password. (Input will be hidden)")
        password = getpass.getpass("Enter password: ")
        api_key = get_api_key(panorama_host, username, password)
        if api_key:
            print(f"✓ Login successful! API key obtained.")
            break
        else:
            print(f"✗ Login failed. Check credentials. Attempt {attempt} of {max_attempts}.")
    else:
        print("Too many failed login attempts. Exiting.")
        sys.exit(1)

    # Test API calls
    print("\n=== Testing API Calls ===")
    
    # Get system info
    print("1. Getting system information...")
    sys_url = f"https://{panorama_host}/api/?type=op&cmd=<show><system><info></info></system></show>&key={api_key}"
    try:
        r = requests.get(sys_url, verify=False, timeout=10)
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.text)
        hostname = root.findtext('.//hostname', 'N/A')
        version = root.findtext('.//sw-version', 'N/A')
        uptime = root.findtext('.//uptime', 'N/A')
        print(f"   Hostname: {hostname}")
        print(f"   Version: {version}")
        print(f"   Uptime: {uptime}")
    except Exception as e:
        print(f"   Error getting system info: {e}")

    # Get device groups count
    print("2. Getting device groups...")
    dg_url = f"https://{panorama_host}/api/?type=config&action=get&xpath=/config/devices/entry/device-group&key={api_key}"
    try:
        r = requests.get(dg_url, verify=False, timeout=10)
        root = ET.fromstring(r.text)
        dg_count = len(root.findall('.//entry'))
        print(f"   Number of device groups: {dg_count}")
        if dg_count > 0:
            dg_names = [entry.attrib.get('name', '') for entry in root.findall('.//entry')]
            print(f"   Device groups: {', '.join(dg_names[:5])}{'...' if len(dg_names) > 5 else ''}")
    except Exception as e:
        print(f"   Error getting device groups: {e}")

    # Get address objects count
    print("3. Getting address objects...")
    addr_url = f"https://{panorama_host}/api/?type=config&action=get&xpath=/config/shared/address&key={api_key}"
    try:
        r = requests.get(addr_url, verify=False, timeout=10)
        root = ET.fromstring(r.text)
        addr_count = len(root.findall('.//entry'))
        print(f"   Number of shared address objects: {addr_count}")
    except Exception as e:
        print(f"   Error getting address objects: {e}")

    print("\n=== Test Complete ===")
    print("If you see the system information above, your login is working correctly!")

if __name__ == "__main__":
    main() 
