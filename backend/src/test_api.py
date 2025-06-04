import requests

url = "http://127.0.0.1:5000/api/analyze"
data = {
    "bank_names": ["JP Morgan", "Wells Fargo"],
    "config_path": "D:/office_Work_shennanigans/hackathon/integrated_hackathon_codebase/config/config.json",
    "base_dir": "D:/office_Work_shennanigans/hackathon/integrated_hackathon_codebase"
}

response = requests.post(url, json=data)
print(response.json())