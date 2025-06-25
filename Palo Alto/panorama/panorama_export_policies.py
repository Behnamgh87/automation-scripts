import requests
import sys
from datetime import datetime
import getpass
import csv

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

def main():
    print("=== Palo Alto Panorama Policy Exporter ===\n")
    print("Please enter your Panorama credentials.")
    panorama_host = input("Enter Panorama IP: ").strip()
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

    # Only ask for device group and policy type after successful login
    device_group = prompt_with_default(
        "Enter device group to export (or leave blank for all)", "all"
    )
    policy_type = prompt_with_default(
        "Which policy type do you want to export? (enabled/disabled/both)", "all"
    ).lower()
    if policy_type not in {"enabled", "disabled", "all"}:
        print("Invalid policy type. Using default: all.")
        policy_type = "all"

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

    # Prepare CSV file
    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"panorama_export_policies_{now}.csv"
    fieldnames = [
        'device_group', 'rule_name', 'source', 'destination', 'application', 'service', 'action', 'enabled'
    ]
    with open(filename, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for dg in dgs:
            print(f"Exporting policies for device group: {dg}")
            xpath = f"/config/devices/entry/device-group/entry[@name='{dg}']/pre-rulebase/security/rules"
            url = f"https://{panorama_host}/api/?type=config&action=get&xpath={xpath}&key={api_key}"
            r = requests.get(url, verify=False)
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(r.text)
                rules = root.findall('.//entry')
                for rule in rules:
                    disabled_elem = rule.find('disabled')
                    enabled = not (disabled_elem is not None and (disabled_elem.text or '').strip().lower() == 'yes')
                    if policy_type == 'enabled' and not enabled:
                        continue
                    if policy_type == 'disabled' and enabled:
                        continue
                    rule_name = rule.attrib.get('name', '')
                    source = ','.join([src.text for src in rule.findall('source/member') if src.text is not None])
                    destination = ','.join([dst.text for dst in rule.findall('destination/member') if dst.text is not None])
                    application = ','.join([app.text for app in rule.findall('application/member') if app.text is not None])
                    service = ','.join([svc.text for svc in rule.findall('service/member') if svc.text is not None])
                    action = rule.findtext('action', '')
                    writer.writerow({
                        'device_group': dg,
                        'rule_name': rule_name,
                        'source': source,
                        'destination': destination,
                        'application': application,
                        'service': service,
                        'action': action,
                        'enabled': 'yes' if enabled else 'no'
                    })
            except Exception as e:
                print(f"Failed to parse policies for {dg}: {e}")
    print(f"\nExport complete. Policies saved to {filename}")

if __name__ == "__main__":
    main() 
