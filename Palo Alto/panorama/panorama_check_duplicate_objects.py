import requests
import sys
from datetime import datetime
import getpass
import csv
import ipaddress

# Disable SSL warnings
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

def prompt_with_default(prompt, default):
    value = input(f"{prompt} (default: {default}): ").strip()
    return value if value else default

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

def normalize_ip(value):
    # Normalize IPs: 1.1.1.1 and 1.1.1.1/32 are the same
    try:
        if '/' in value:
            ip = ipaddress.ip_network(value, strict=False)
            if ip.prefixlen == ip.max_prefixlen:
                return str(ip.network_address)
            return str(ip)
        else:
            return str(ipaddress.ip_address(value))
    except Exception:
        return value.strip()

def main():
    print("=== Panorama Duplicate Address Object Checker ===\n")
    print("Please enter your Panorama credentials.")
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
            break
        else:
            print(f"Login failed. Check credentials. Attempt {attempt} of {max_attempts}.")
    else:
        print("Too many failed login attempts. Exiting.")
        sys.exit(1)

    device_group = prompt_with_default(
        "Enter device group to check (or leave blank for all)", "all"
    )

    # Get device groups if needed
    if device_group == "all":
        dg_url = f"https://{panorama_host}/api/?type=config&action=get&xpath=/config/devices/entry/device-group&key={api_key}"
        r = requests.get(dg_url, verify=False)
        dgs = []
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(r.text)
            for entry in root.findall('.//entry'):
                dg_name = entry.attrib.get('name')
                if dg_name:
                    dgs.append(dg_name)
        except Exception as e:
            print(f"Failed to parse device groups: {e}")
            sys.exit(1)
    else:
        dgs = [device_group]

    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"panorama_duplicate_objects_{now}.csv"
    fieldnames = [
        'device_group', 'object_name', 'object_value', 'duplicate_type', 'duplicate_with'
    ]
    with open(filename, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for dg in dgs:
            print(f"Checking address objects for device group: {dg}")
            xpath = f"/config/devices/entry/device-group/entry[@name='{dg}']/address"
            url = f"https://{panorama_host}/api/?type=config&action=get&xpath={xpath}&key={api_key}"
            r = requests.get(url, verify=False)
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(r.text)
                objects = root.findall('.//entry')
                name_map = {}
                value_map = {}
                obj_info = {}
                for obj in objects:
                    name = obj.attrib.get('name', '')
                    value = obj.findtext('ip-netmask') or obj.findtext('fqdn') or obj.findtext('ip-range') or ''
                    norm_value = normalize_ip(value)
                    obj_info[name] = (value, norm_value)
                    # Name map
                    if name in name_map:
                        name_map[name].append(name)
                    else:
                        name_map[name] = [name]
                    # Value map
                    if norm_value in value_map:
                        value_map[norm_value].append(name)
                    else:
                        value_map[norm_value] = [name]
                # Find duplicates
                for name, (value, norm_value) in obj_info.items():
                    duplicate_type = []
                    duplicate_with = set()
                    # Name duplicates
                    if len(name_map[name]) > 1:
                        duplicate_type.append('name')
                        duplicate_with.update([n for n in name_map[name] if n != name])
                    # Value duplicates
                    if len(value_map[norm_value]) > 1:
                        duplicate_type.append('value')
                        duplicate_with.update([n for n in value_map[norm_value] if n != name])
                    if duplicate_type:
                        writer.writerow({
                            'device_group': dg,
                            'object_name': name,
                            'object_value': value,
                            'duplicate_type': ','.join(duplicate_type),
                            'duplicate_with': ','.join(sorted(duplicate_with))
                        })
            except Exception as e:
                print(f"Failed to parse address objects for {dg}: {e}")
    print(f"\nCheck complete. Duplicate objects saved to {filename}")

if __name__ == "__main__":
    main() 
