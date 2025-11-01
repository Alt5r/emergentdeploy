
import requests

# Replace 'YOUR_TOPIC' with the topic you subscribed to in the app
TOPIC = "Emergent_testing"
NOTIFICATION_URL = f"https://ntfy.sh/{TOPIC}"

# Send a notification
try:
    response = requests.post(
        NOTIFICATION_URL,
        data="EMERGENT ALERT",
        headers={
            "Title": "7.0 Magnitude Earthquake",
            "Priority": "high",
            "Tags": "exclamation",
            "Icon": "https://avatars.githubusercontent.com/u/105633859?s=200&v=4",
        },
    )
    response.raise_for_status()  # Raise an exception for bad status codes
    print("Notification sent successfully!")
except requests.exceptions.RequestException as e:
    print(f"Error sending notification: {e}")
