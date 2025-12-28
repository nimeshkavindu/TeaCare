import requests

# Your Server URL
API_URL = "http://127.0.0.1:8000/add_knowledge"

# --- 1. TYPE YOUR DATA HERE ---
# You can add as many items as you want to this list.
my_tea_knowledge = [
    {
        "category": "Pruning",
        "title": "Lung Pruning Basics",
        "content": "Lung pruning is essential for low-country tea. Always leave 15-20cm of lung branches with leaves to support recovery.",
        "source": "TRI Handbook Page 42"
    },
    {
        "category": "Diseases",
        "title": "Blister Blight Control",
        "content": "To control Blister Blight in wet weather, spray copper oxychloride at a rate of 30g per 10 liters of water every 5-7 days.",
        "source": "Tea Research Institute Circular 5"
    },
    {
        "category": "Fertilizer",
        "title": "Young Tea Manuring",
        "content": "For young tea plants (T1875 series), apply T65 mixture 4 times a year. Avoid applying during heavy rains to prevent washout.",
        "source": "TRI Fertilizer Guide 2023"
    }
]

# --- 2. RUN THIS SCRIPT TO UPLOAD ---
print(f"Uploading {len(my_tea_knowledge)} facts to your AI...")

for item in my_tea_knowledge:
    try:
        response = requests.post(API_URL, json=item)
        if response.status_code == 200:
            print(f"✅ Success: {item['title']}")
        else:
            print(f"❌ Failed: {item['title']} (Error: {response.text})")
    except Exception as e:
        print(f"❌ Connection Error: Is your server running? ({e})")

print("\nDone! Now ask your chatbot about these topics.")