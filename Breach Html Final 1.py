import pandas as pd

# Replace 'your_data.csv' with the path to your actual CSV file
csv_path = 'output.csv'

# Read the CSV file into a Pandas DataFrame
df = pd.read_csv(csv_path)

# Group data by Message, Device Name, Sensor ID, and aggregate details
grouped_data = {}
for _, row in df.iterrows():
    message = row['Message']
    device_name = row['Device Name']
    sensor_id = row['Sensor ID']
    sensor_name = row['Sensor Name']
    traffic_total = row['Traffic Total']
    date = row['Date']
    
    if message not in grouped_data:
        grouped_data[message] = {}
    
    if device_name not in grouped_data[message]:
        grouped_data[message][device_name] = {}
        
    if sensor_name not in grouped_data[message][device_name]:
        grouped_data[message][device_name][sensor_name] = {}
    
    if sensor_id not in grouped_data[message][device_name][sensor_name]:
        grouped_data[message][device_name][sensor_name][sensor_id] = {
            'SensorName': sensor_name,
            'Details': []
        }
    
    grouped_data[message][device_name][sensor_name][sensor_id]['Details'].append((date, traffic_total))

# Generate HTML content
html_content = """
<!DOCTYPE html>
<html>
<head>
<title>Sensor Data Summary</title>
<style>
a:link, a:visited, a:hover, a:active {
  text-decoration: none;
}
body {
    font-family: Calibri, Arial, sans-serif;
}
ul {
    list-style-type: none;
    margin: 0;
    padding: 0;
}
li {
    padding: 10px 0;
    font-weight: bold;
}
ul ul {
    list-style-type: disc;
    margin-left: 20px;
}
ul ul ul {
    list-style-type: circle;
    margin-left: 20px;
}
ul ul ul ul {
    list-style-type: square;
    margin-left: 20px;
}
.hidden {
    display: none;
}
.red {
    color: red;
}
.green {
    color: green;
}
.brown {
    color: brown;
}
</style>
<script>
function toggleDetails(elementId) {
    var details = document.getElementById(elementId);
    details.classList.toggle('hidden');
}
</script>
</head>
<body>
<h2>Sensor Data Summary</h2>
<ul>
"""

# Loop through grouped data and create HTML structure
for message, devices in grouped_data.items():
    if "Breach" in message:
        message_class = "red"
    elif "Not breach" in message:
        message_class = "green"
    elif "Upper Warning Limit Not Set" in message:
        message_class = "brown"
    else:
        message_class = ""
    
    html_content += f"<li class='{message_class}'><a class='{message_class}' href='javascript:void(0)' onclick=\"toggleDetails('{message.replace(' ', '_')}')\" >{message} ({len(devices)})</a>"
    html_content += f"<ul id='{message.replace(' ', '_')}' class='sub-list hidden {message_class}'>"
    
    for device_name, sensors in devices.items():
        html_content += f"<li class='{message_class}'><a class='{message_class}' href='javascript:void(0)' onclick=\"toggleDetails('{message.replace(' ', '_')}_{device_name.replace(' ', '_')}')\" >Device Name: {device_name}</a>"
        html_content += f"<ul id='{message.replace(' ', '_')}_{device_name.replace(' ', '_')}' class='sub-list hidden {message_class}'>"
        
        for sensor_name, sensor_ids in sensors.items():
            html_content += f"<li class='{message_class}'><a class='{message_class}' href='javascript:void(0)' onclick=\"toggleDetails('{message.replace(' ', '_')}_{device_name.replace(' ', '_')}_{sensor_name.replace(' ', '_')}')\">Sensor Name: {sensor_name}</a>"
            html_content += f"<ul id='{message.replace(' ', '_')}_{device_name.replace(' ', '_')}_{sensor_name.replace(' ', '_')}' class='sub-list hidden {message_class}'>"
            
            for sensor_id, details in sensor_ids.items():
                html_content += f"<li class='{message_class}'><a class='{message_class}' href='javascript:void(0)' onclick=\"toggleDetails('{message.replace(' ', '_')}_{device_name.replace(' ', '_')}_{sensor_name.replace(' ', '_')}_{sensor_id}')\">Sensor ID: {sensor_id}</a>"
                html_content += f"<ul id='{message.replace(' ', '_')}_{device_name.replace(' ', '_')}_{sensor_name.replace(' ', '_')}_{sensor_id}' class='sub-list hidden {message_class}'>"
                html_content += f"<li class='{message_class}'><strong>Dates and Traffic Total:</strong><ul>"
                for date, traffic_total in details['Details']:
                    html_content += f"<li class='{message_class}'>{date} - Traffic Total: {traffic_total} Mbps</li>"
                html_content += "</ul></li>"
                html_content += "</ul></li>"
            
            html_content += "</ul></li>"
        
        html_content += "</ul></li>"
    
    html_content += "</ul></li>"

html_content += """
</ul>
</body>
</html>
"""

# Write HTML content to a file
with open('sensor_data.html', 'w') as file:
    file.write(html_content)

print("HTML file generated successfully.")
