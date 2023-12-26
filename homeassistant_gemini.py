import requests
import json
import base64
from urlencode import urlencode
from picochromecast import play_url
from urllib.parse import urlencode
import paho.mqtt.client as mqtt


def generate_content_with_base64(base64_image):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent?key={GEMINI_API_KEY}"

    payload = json.dumps({
        "contents": [
            {
                "parts": [
                    {
                        "text": """
                          This is my doorbell image, describe in very short answer.
                        """
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": base64_image
                        }
                    }
                ]
            }
        ]
    })

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, data=payload)

    return response.json()


def get_base64_image():
    # Replace 'http://your_home_assistant_url:8123' and 'your_long_lived_access_token' with your Home Assistant URL and token
    url ='https://your_home_assistant_url:8123/api/states/image.doorbell_event_image'
    headers = {'Authorization': 'Bearer <Home Assistant Long-lived access token>}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        image_url = response.json()['attributes']['entity_picture']
        print(f"The current state of sensor.example_sensor is: {image_url}")

        duckdns_domain = 'your_home_assistant_url:8123'
        full_url = f'https://{duckdns_domain}{image_url}'

        # Make a GET request to fetch the image
        response_img = requests.get(full_url)

        # Check if the request was successful (status code 200)
        if response_img.status_code == 200:

            base64_image = base64.b64encode(response_img.content).decode('utf-8')
            return base64_image
        else:
            print(f"Failed to fetch image. Status code: {response_img.status_code}")
            return None

    else:
        print(f"Failed to get entity state. Status code: {response.status_code}")
        return None

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to Home Assistant")
        # Subscribe to the topic where Home Assistant publishes sensor data
        client.subscribe("homeassistant/sensor/#")
    else:
        print(f"Connection failed with result code {rc}")

def on_message(client, userdata, msg):
    print(f"Received message: {msg.payload.decode()} on topic {msg.topic}")
    base64_image = get_base64_image()
    if base64_image:
        base64_image_data = base64_image
        result = generate_content_with_base64(base64_image_data)
        print(result)
        text_to_speak = result["candidates"][0]["content"]["parts"][0]["text"]
        print(text_to_speak)
        url = 'https://translate.google.com/translate_tts?client=tw-ob&' + urlencode({'q': text_to_speak, 'tl': 'en'})
        play_url(url, '<Google Home URL>')


# Replace 'your_home_assistant_address', 'your_home_assistant_port', 'your_username', and 'your_password' with your Home Assistant MQTT broker information
home_assistant_address = "your_home_assistant_url"
home_assistant_port = 1883
username = "your_home_assistant_mqtt_userid"
password = "your_home_assistant_mqtt_pwd"

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Set the username and password for authentication
client.username_pw_set(username, password)

# Connect to Home Assistant MQTT broker
client.connect(home_assistant_address, port=home_assistant_port, keepalive=60)

# Start the MQTT loop to listen for messages
client.loop_forever()
