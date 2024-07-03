import requests
import xml.etree.ElementTree as ET
import re
import csv
import os
import pandas as pd
from io import StringIO
import warnings
from datetime import datetime
from tqdm import tqdm
import io


def remove_characters(text):
    cleaned_text = re.sub(r'\(�C\)|�C', '', text)
    return cleaned_text

prtg_choice = input("Enter the PRTG you want (99.100, 101.100, 99.102): ")

if prtg_choice == "99.100":
    with open("server_address-99.100.txt", "r") as file:
       server_parameters = dict(line.strip().split("=") for line in file)
elif prtg_choice == "101.100":
    with open("server_address-101.100.txt", "r") as file:
        server_parameters = dict(line.strip().split("=") for line in file)
elif prtg_choice == "99.102":
    with open("server_address-99.102.txt", "r") as file:
        server_parameters = dict(line.strip().split("=") for line in file)
else:
    print("Invalid input! Please enter either '99.100', '101.100', or '99.102'.")
    exit()

server_address = server_parameters.get("server")
username = server_parameters.get("username")
passhash = server_parameters.get("passhash")
param = server_parameters.get("day")

current_datetime = datetime.now().strftime("%d_%B_%Y_%I_%M_%p")

if "99-102" in server_address:
    file_path = f"prtg-{current_datetime}-99.102.xml"
    output_file= f"prtg-{current_datetime}-99.102.txt"
    csv_file = f"prtg-{current_datetime}-99.102.csv"
    html_file = f"prtg-{current_datetime}-99.102.html"
elif "101-100" in server_address:
    file_path = f"prtg-{current_datetime}-101.100.xml"
elif "99-100" in server_address:
    file_path = f"prtg-{current_datetime}-99.100.xml"
else:
    file_path = f"prtg-{current_datetime}-default.xml"

print(f"File path to save XML: {file_path}")

api_endpoint = f'https://{server_address}/api/table.xml?content=sensortree&username={username}&passhash={passhash}'

response = requests.get(api_endpoint)

# Check if the request was successful
if response.status_code == 200:
    print("Request successful!")
    print("Response content:")
    print(response.text)

    # Ensure the response content is not empty
    if response.text.strip():
        # Write the XML response to a file
        try:
            with open(file_path, "w") as file:
                file.write(response.text)
            print(f"XML data saved to {file_path}")
        except Exception as e:
            print(f"Error writing to file: {e}")
    else:
        print("The response text is empty. No data to save.")
else:
    print(f"Error: {response.status_code} - {response.text}")


encodings_to_try = ['utf-8', 'latin-1']

for encoding in encodings_to_try:
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            xml_content = file.read()
        break
    except UnicodeDecodeError:
        continue

cleaned_xml_content = remove_characters(xml_content)

try:
    root = ET.fromstring(cleaned_xml_content)
    tree = ET.ElementTree(root)

    # Save the modified XML back to a file
    tree.write(file_path)
    print("XML file cleaned successfully!")
except ET.ParseError as e:
    print("Error parsing XML:", e)


tree = ET.parse(file_path)
root = tree.getroot()

# Define sensor IDs
sensor_ids = []

for sensor in root.iter('sensor'):
    sensortype = sensor.find('sensortype')
    if sensortype is not None and sensortype.text == 'SNMP Traffic':
        sensor_id = sensor.find('id')
        if sensor_id is not None:
            sensor_ids.append(sensor_id.text)

with open(output_file, 'w') as file:
    for i, sensor_id in enumerate(sensor_ids, start=1):
        file.write(f"id{i}={sensor_id}\n")


print("Sensor IDs for SNMP Traffic sensors have been saved to:", output_file)

warnings.filterwarnings("ignore", category=DeprecationWarning)

flags = {}
id_prefix = 'id'
id_values = []

with open("min_max_flags.txt", "r") as file:
    for line in file:
        line = line.strip()
        if "=" in line:
            key, value = line.split("=")
            if key.startswith(id_prefix):
                id_values.append(value)
            else:
                flags[key] = value

with open(output_file, "r") as file:
    for line in file:
        line = line.strip()
        if "=" in line:
            key, value = line.split("=")
            if key.startswith(id_prefix):
                id_values.append(value)

upper_warning_limits = {}

for id_value in tqdm(id_values, desc="Getting upper warning for Each IDs"):
    try:
        api_endpoint_upper_warning = f'https://{server_address}/api/getobjectproperty.htm?subtype=channel&id={id_value}&subid=-1&name=limitmaxwarning&show=nohtmlencode&username={username}&passhash={passhash}'
        response_upper_warning = requests.get(api_endpoint_upper_warning)
        
        if response_upper_warning.status_code != 200:
            print(f"Check parameters for: {id_value}")
            continue
            
        match_upper_warning = re.search(r'<result>(\d+)</result>', response_upper_warning.text)
        
        if match_upper_warning is not None:
            upper_warning_limits[id_value] = float(match_upper_warning.group(1)) * 8 / 1000000
        else:
            print(f"Warning: Upper warning limit value not set for ID: {id_value}. Skipping.")
            continue
    except Exception as e:
        print(f"Error getting upper warning limit for ID {id_value}: {e}")
        continue

output_data = []

for id_value in id_values:
    if id_value not in upper_warning_limits:
        # Fetch device details for IDs without upper warning limits
        try:
            api_endpoint = f'https://{server_address}/api/getsensordetails.json?id={id_value}&username={username}&passhash={passhash}'
            response = requests.get(api_endpoint)
            
            if response.status_code == 200:
                device_details = response.json().get("sensordata")
                parent_device_name = device_details.get("parentdevicename", "N/A")
                sensor_device_name = device_details.get("name", "N/A")
                DeviceID = device_details.get("parentdeviceid", "N/A")
                
                output_data.append({
                    "Device Name": parent_device_name,
                    "Device ID": DeviceID,
                    "Sensor Name": sensor_device_name,
                    "Sensor ID": id_value,
                    "Date": "NA",
                    "Message":"Upper Warning Limit Not Set",
                    "Traffic Total": "N/A"
                })
            else:
                print(f"Error: Unable to get device details for ID: {id_value}")
        except Exception as e:
            print(f"Error fetching device details for ID {id_value}: {e}")

for id_value in tqdm(id_values, desc="Processing IDs"):
    parent_device_name = "N/A"
    sensor_device_name = "N/A"
    DeviceID = "N/A"
    
    try:
        # Fetch historic data CSV
        api_endpoint = f'https://{server_address}/api/historicdata.csv?id={id_value}&avg={flags.get("avg")}&sdate={flags.get("sdate")}&edate={flags.get("edate")}&username={username}&passhash={passhash}'
        response = requests.get(api_endpoint)
        df = pd.read_csv(io.StringIO(response.text))
        
        # Clean and process data
        df['Traffic Total (Speed)'] = df['Traffic Total (Speed)'].astype(str).str.replace(',', '').str.extract(r'(\d+\.*\d*)').astype(float)
        selected_data = df["Traffic Total (Speed)"]
    except KeyError:
        print(f"Traffic Total (Speed) column not found for ID: {id_value}")
        continue  
    
    if id_value not in upper_warning_limits:
        # Skip further processing if upper warning limit is not set
        continue
    
    # Filter data based on upper warning limits
    filtered_data = selected_data[selected_data > upper_warning_limits.get(id_value)]

    try:
        # Fetch sensor details
        api_endpoint = f'https://{server_address}/api/getsensordetails.json?id={id_value}&username={username}&passhash={passhash}'
        device_name_response = requests.get(api_endpoint)
        
        if device_name_response.status_code == 200:
            device_name_json = device_name_response.json()
            parent_device_name = device_name_json["sensordata"]["parentdevicename"]
            sensor_device_name = device_name_json["sensordata"]["name"]
            DeviceID = device_name_json["sensordata"]["parentdeviceid"]
        else:
            print(f"Error: Unable to get device details for ID: {id_value}")
    except Exception as e:
        print(f"Error fetching device details for ID {id_value}: {e}")
        continue
    
    # Collect data for output
    if not filtered_data.empty:
        output_data.extend([{
            "Device Name": parent_device_name,
            "Device ID": DeviceID,
            "Sensor Name": sensor_device_name,
            "Sensor ID": id_value,
            "Date": row['Date Time'] if row['Traffic Total (Speed)'] > upper_warning_limits.get(id_value) else "N/A",
            "Message":"Breach",
            "Traffic Total": row["Traffic Total (Speed)"]
            
        } for index, row in df.iterrows() if row['Traffic Total (Speed)'] > upper_warning_limits.get(id_value)])
    else:
        max_traffic = selected_data.max()
        max_traffic_date = df.loc[df['Traffic Total (Speed)'].idxmax(), 'Date Time'] if not pd.isnull(df['Traffic Total (Speed)'].max()) else "N/A"
        
        output_data.append({
            "Device Name": parent_device_name,
            "Device ID": DeviceID,
            "Sensor Name": sensor_device_name,
            "Sensor ID": id_value,
            "Date": max_traffic_date,
            "Message":"Not breach",
            "Traffic Total": max_traffic
        })

output_df = pd.DataFrame(output_data)

output_directory = "output"
os.makedirs(output_directory, exist_ok=True)

current_datetime = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
output_file_path = os.path.join(output_directory, f"output_{current_datetime}.csv")

output_df.to_csv(output_file_path, index=False)

print(f"\nOutput has been saved to {output_file_path}")