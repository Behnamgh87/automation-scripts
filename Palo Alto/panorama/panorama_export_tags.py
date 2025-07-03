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
    # Hardcoded device group list (edit this with your device group names)
    device_groups = [
        #Example "USA", "EU", "Asia"
    ]
    device_groups = sorted(device_groups, key=lambda x: x.lower())

    if not device_groups:
        print("Device group list is empty. Please edit the script and add your device groups to the 'device_groups' list.")
        sys.exit(1)

    print("\nAvailable Device Groups:")
    for idx, dg in enumerate(device_groups, 1):
        print(f"  {idx}. {dg}")
    print(f"  {len(device_groups)+1}. ALL (all listed device groups)")

    selection = input("Select device group(s) by number (comma-separated, or enter {0} for ALL): ".format(len(device_groups)+1)).strip()
    if not selection:
        print("No selection made. Exiting.")
        sys.exit(1)

    selected_indices = [s.strip() for s in selection.split(',') if s.strip().isdigit()]
    selected_indices = [int(s) for s in selected_indices if 1 <= int(s) <= len(device_groups)+1]
    if not selected_indices:
        print("Invalid selection. Exiting.")
        sys.exit(1)

    if len(device_groups)+1 in selected_indices:
        dgs = device_groups
    else:
        dgs = [device_groups[i-1] for i in selected_indices]

    # Prepare CSV file
    now = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"panorama_export_tags_from_device_groups_{now}.csv"
    fieldnames = [
        'device_group', 'tag_name', 'color', 'comments'
    ]
    with open(filename, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for dg in dgs:
            print(f"Exporting tags for device group: {dg}")
            xpath = f"/config/devices/entry/device-group/entry[@name='{dg}']/tag"
            url = f"https://{panorama_host}/api/?type=config&action=get&xpath={xpath}&key={api_key}"
            r = requests.get(url, verify=False)
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(r.text)
                tags = root.findall('.//entry')
                for tag in tags:
                    tag_name = tag.attrib.get('name', '')
                    color = tag.findtext('color', '')
                    comments = tag.findtext('comments', '')
                    writer.writerow({
                        'device_group': dg,
                        'tag_name': tag_name,
                        'color': color,
                        'comments': comments
                    })
            except Exception as e:
                print(f"Failed to parse tags for {dg}: {e}")
    print(f"\nExport complete. Tags saved to {filename}")

    # Export CSV to Excel
    try:
        import pandas as pd
        excel_filename = filename.replace('.csv', '.xlsx')
        df = pd.read_csv(filename)
        df.to_excel(excel_filename, index=False)
        print(f"Tags also saved to {excel_filename}")
    except ImportError:
        print("pandas is not installed. Skipping Excel export. To enable, run: pip install pandas openpyxl")
    except Exception as e:
        print(f"Failed to export to Excel: {e}")

if __name__ == "__main__":
    print("=== Palo Alto Panorama Tag Exporter (Device Groups) ===\n")
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
        again = input("\nDo you want to run the script again (device group selection and export)? (y/n): ").strip().lower()
        if again != 'y':
            print("Exiting.")
            break 
