import paho.mqtt.client as mqtt
import time

broker_address = "localhost"  # Use the IP address of your broker if not running locally


def on_publish(client, userdata, result):
    print("Data published.")
    pass


client = mqtt.Client()
client.on_publish = on_publish
client.connect(broker_address, 1883, 60)

client.loop_start()

# Publish messages
while True:
    client.publish("test/set_pin_value", "set_pin_value 8 0")
    time.sleep(1)
    client.publish("test/get_pin", "get_pin 8")
    client.publish("test/get_all_pins", "get_all_pins")
    time.sleep(5)
