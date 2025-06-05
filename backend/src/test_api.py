import requests

url = "http://127.0.0.1:5000/api/analyze"
data = {
    "bank_names": ["Synchrony", "JPMorgan", "WellsFargo", "BankOfAmerica"],# "JPMorgan", "BankOfAmerica", "Synchrony", "Barclays", "CapitalOne", "CitiBank"],
    "quarter": "Q12025"
    }

response = requests.post(url, json=data)
print(response.json())