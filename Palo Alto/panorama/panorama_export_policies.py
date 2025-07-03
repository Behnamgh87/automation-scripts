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

def main(panorama_host, api_key):
<<<<<<< Updated upstream
    # Hardcoded device group list (fill this out with your device groups)
    # Device group is case-sensitive.
    device_groups = [
        #Example "USA", "EU", "Asia"
=======
    # Hardcoded template list (edit this with your template names)
    templates = [
        'Template1', 'Template2', 'Template3', 'Shared'
>>>>>>> Stashed changes
    ]
    templates = sorted(templates, key=lambda x: x.lower())

    if not templates:
        print("Template list is empty. Please edit the script and add your templates to the 'templates' list.")
        sys.exit(1)

    print("\nAvailable Templates:")
    for idx, tpl in enumerate(templates, 1):
        print(f"  {idx}. {tpl}")
    print(f"  {len(templates)+1}. ALL (all listed templates)")

    selection = input("Select template(s) by number (comma-separated, or enter {0} for ALL): ".format(len(templates)+1)).strip()
    if not selection:
        print("No selection made. Exiting.")
        sys.exit(1)

    selected_indices = [s.strip() for s in selection.split(',') if s.strip().isdigit()]
    selected_indices = [int(s) for s in selected_indices if 1 <= int(s) <= len(templates)+1]
    if not selected_indices:
        print("Invalid selection. Exiting.")
        sys.exit(1)

    if len(templates)+1 in selected_indices:
        tpls = templates
    else:
        tpls = [templates[i-1] for i in selected_indices]

    # Prepare CSV file
    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"panorama_export_zones_from_templates_{now}.csv"
    fieldnames = [
        'template', 'zone_name', 'zone_type', 'interfaces', 'enable_user_id'
    ]
    with open(filename, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for tpl in tpls:
            print(f"Exporting zones for template: {tpl}")
            xpath = f"/config/devices/entry/template/entry[@name='{tpl}']/config/devices/entry/network/zone"
            url = f"https://{panorama_host}/api/?type=config&action=get&xpath={xpath}&key={api_key}"
            r = requests.get(url, verify=False)
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(r.text)
                zones = root.findall('.//entry')
                for zone in zones:
                    zone_name = zone.attrib.get('name', '')
                    zone_type = zone.findtext('network/type', '') or zone.findtext('type', '')
                    interfaces = ','.join([iface.text for iface in zone.findall('network/interface/member')] + [iface.text for iface in zone.findall('interface/member')] if iface.text is not None)
                    enable_user_id = zone.findtext('enable-user-identification', '')
                    writer.writerow({
                        'template': tpl,
                        'zone_name': zone_name,
                        'zone_type': zone_type,
                        'interfaces': interfaces,
                        'enable_user_id': enable_user_id
                    })
            except Exception as e:
                print(f"Failed to parse zones for {tpl}: {e}")
    print(f"\nExport complete. Zones saved to {filename}")

if __name__ == "__main__":
    print("=== Palo Alto Panorama Zone Exporter (Templates) ===\n")
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

    while True:
        main(panorama_host, api_key)
        again = input("\nDo you want to run the script again (template selection and export)? (y/n): ").strip().lower()
        if again != 'y':
            print("Exiting.")
            break 
