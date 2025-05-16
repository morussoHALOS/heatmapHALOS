import pandas as pd
import folium
import numpy as np
import subprocess
import gspread
import hashlib
import json
from oauth2client.service_account import ServiceAccountCredentials

# === Step 1: Load Google Sheet ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("realGeocoded").sheet1

data = sheet.get_all_records()

# === Smart update: skip if sheet hasn't changed ===
def sheet_hash(data):
    json_data = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_data.encode('utf-8')).hexdigest()

new_hash = sheet_hash(data)
HASH_FILE = "last_sheet_hash.txt"

previous_hash = ""
if os.path.exists(HASH_FILE):
    with open(HASH_FILE, "r") as f:
        previous_hash = f.read().strip()

if new_hash == previous_hash:
    print("✅ Sheet has not changed. Skipping update.")
    exit()

# Save new hash
with open(HASH_FILE, "w") as f:
    f.write(new_hash)

# === Now continue converting data ===
addresses_df = pd.DataFrame(data)

# === Step 2: Sort and prep ===
addresses_df = addresses_df.sort_values(by='ARR Total')
map_center = [37.0902, -95.7129]
mymap = folium.Map(location=map_center, zoom_start=5, min_zoom=5, max_zoom=8)

def get_marker_color(arr):
    if arr <= 10000: return 'green'
    elif arr <= 25000: return 'yellow'
    elif arr <= 50000: return 'orange'
    elif arr <= 100000: return 'red'
    else: return 'purple'

arr_color_data = {c: {'count': 0, 'total': 0} for c in ['green', 'yellow', 'orange', 'red', 'purple']}
region_data = {r: {'count': 0, 'total': 0} for r in ['West', 'Central', 'East']}

for _, row in addresses_df.iterrows():
    arr_total = row['ARR Total']
    lat, lon = row['latitude'], row['longitude']
    color = get_marker_color(arr_total)
    arr_color_data[color]['count'] += 1
    arr_color_data[color]['total'] += arr_total

    region = 'West' if lon < -109 else 'Central' if lon <= -90 else 'East'
    region_data[region]['count'] += 1
    region_data[region]['total'] += arr_total

    radius = 3 + (np.log1p(arr_total) * 0.6)
    folium.CircleMarker(
        location=[lat, lon],
        radius=radius,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.6,
        popup=f"<b>{row['Name']}</b><br>{row['address']}<br>ARR: ${arr_total:,.2f}"
    ).add_to(mymap)

# === Step 3: Legends ===
legend_html = f"""
<div style="position: fixed; bottom: 10px; left: 10px; width: 300px; height: 240px;
             background-color: white; border:2px solid grey; z-index:9999; font-size:13px;
             padding: 15px 10px 10px 10px; border-radius: 5px;">
<b style="text-align: center; display: block; margin-bottom: 8px;">ARR Breakdown by Tier</b>
""" + "".join([
    f"<i style='background:{color}; width: 20px; height: 20px; display: inline-block;'></i> "
    f"{tier} — {arr_color_data[color]['count']} clients, ${arr_color_data[color]['total']:,.0f}<br>"
    for color, tier in zip(
        ['green', 'yellow', 'orange', 'red', 'purple'],
        ['< $10K', '$10K–25K', '$25K–50K', '$50K–100K', '> $100K']
    )
]) + "</div>"

mymap.get_root().html.add_child(folium.Element(legend_html))

region_html = f"""
<div style="position: fixed; top: 10px; left: 10px; width: 280px; height: 140px;
             background-color: white; border:2px solid grey; z-index:9999; font-size:13px;
             padding: 15px 10px 10px 10px; border-radius: 5px;">
<b style="text-align: center; display: block; margin-bottom: 8px;">ARR by U.S. Region</b>
""" + "".join([
    f"<b>{region}</b>: {region_data[region]['count']} clients, ${region_data[region]['total']:,.0f}<br>"
    for region in ['West', 'Central', 'East']
]) + "</div>"

mymap.get_root().html.add_child(folium.Element(region_html))

for line in [-109, -90]:
    folium.PolyLine([[25, line], [50, line]], color='black', weight=2, opacity=0.3, dash_array='5,5').add_to(mymap)

# === Step 4: Save raw output ===
mymap.save("index_raw.html")

# === Step 5: Inject SHA-256 Password Protection ===
PASSWORD_HASH = "5c86dc9f9cdb39dd68c5f7f112406f8ce987972afab08d5605d862bbb3609cd4"  # halos2025

with open("index_raw.html", "r", encoding="utf-8") as f:
    content = f.read()

security_script = f"""
<script>
async function checkPassword() {{
  const input = prompt("Enter access code:");
  const encoder = new TextEncoder();
  const data = encoder.encode(input);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  const correctHash = "{PASSWORD_HASH}";
  if (hashHex !== correctHash) {{
    document.body.innerHTML = "<h2 style='color:red; text-align:center;'>Access Denied</h2>";
    throw new Error("Access denied");
  }}
}}
window.onload = checkPassword;
</script>
"""

content = content.replace("<head>", f"<head>{security_script}", 1)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("✅ index.html created with SHA-256 password gate.")

# === Step 6: Auto Git Push ===
try:
    subprocess.run(["git", "add", "index.html"], check=True)
    subprocess.run(["git", "commit", "-m", "Auto update from Google Sheet"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("🚀 Pushed to GitHub!")
except subprocess.CalledProcessError:
    print("ℹ️ Nothing to commit (no changes).")
