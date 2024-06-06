from smbus2 import SMBus
import paho.mqtt.client as mqtt

bus = SMBus(1)

# MCP23017 I2C addresses (example addresses)
devices = [
    ("mcp23017_1", 0x27),
    ("mcp23017_2", 0x28),
    ("mcp23017_3", 0x29)
]

# MCP23017 Registers
IODIRA = 0x00  # I/O direction register for PORTA
IODIRB = 0x01  # I/O direction register for PORTB
GPIOA = 0x12   # Register for reading PORTA
GPIOB = 0x13   # Register for reading PORTB
OLATA = 0x14   # Register for writing to PORTA
OLATB = 0x15   # Register for writing to PORTB

# Initialize the pin states for each device
pin_states = {address: [0xFF, 0xFF] for name, address in devices}

pin_mapping = {}
pin_values = {}

def generate_pin_mapping(devices):
    pin_mapping = {}
    pin_offset = 0
    for name, address in devices:
        for pin in range(16):
            pin_mapping[pin_offset + pin] = {
                "name": name,
                "address": address,
                "pin": pin,
                "description": "",
                "direction": ""  # Default direction
            }
        pin_offset += 16
    return pin_mapping

def configure_pin(name, description, direction, level = ""):
    set_pin_description(name, description)
    set_pin_direction(name, direction) 

def set_pin_description(pin, description):
    if pin not in pin_mapping:
        raise ValueError(f"Pin {pin} is not valid")
    pin_mapping[pin]["description"] = description
    print(f"Set description for pin {pin} (device {pin_mapping[pin]['name']} pin {pin_mapping[pin]['pin']}) to '{description}'")

def set_pin_direction(pin, direction):
    if pin not in pin_mapping:
        raise ValueError(f"Pin {pin} is not valid")
    if direction not in ["input", "output"]:
        raise ValueError("Direction must be 'input' or 'output'")
    
    pin_info = pin_mapping[pin]
    address = pin_info["address"]
    device_pin = pin_info["pin"]
    register = IODIRA if device_pin < 8 else IODIRB
    pin_offset = device_pin % 8

    global pin_states
    if direction == "input":
        pin_states[address][0 if device_pin < 8 else 1] |= (1 << pin_offset)
    else:
        pin_states[address][0 if device_pin < 8 else 1] &= ~(1 << pin_offset)

    bus.write_byte(address, register, pin_states[address][0 if device_pin < 8 else 1])
    pin_mapping[pin]["direction"] = direction
    print(f"Set direction for pin {pin} (device {pin_mapping[pin]['name']} pin {device_pin}) to '{direction}'")

def set_pin_value(pin, value):
    if pin not in pin_mapping:
        raise ValueError(f"Pin {pin} is not valid")
    pin_info = pin_mapping[pin]
    address = pin_info["address"]
    device_pin = pin_info["pin"]
    register = OLATA if device_pin < 8 else OLATB
    pin_offset = device_pin % 8

    global pin_states
    if value == 1:
        pin_states[address][0 if device_pin < 8 else 1] |= (1 << pin_offset)
    else:
        pin_states[address][0 if device_pin < 8 else 1] &= ~(1 << pin_offset)
    bus.write_byte(address, register, pin_states[address][0 if device_pin < 8 else 1])
    print(f"Set pin {pin} (device {pin_mapping[pin]['name']} pin {device_pin}) to {'HIGH' if value == 1 else 'LOW'}")

def get_pin(pin):
    if pin not in pin_mapping:
        raise ValueError(f"Pin {pin} is not valid")
    pin_info = pin_mapping[pin]
    address = pin_info["address"]
    device_pin = pin_info["pin"]
    register = GPIOA if device_pin < 8 else GPIOB
    pin_offset = device_pin % 8

    pin_state = bus.read_byte(address, register)
    value = (pin_state >> pin_offset) & 1
    print(f"Pin {pin} (device {pin_mapping[pin]['name']} pin {device_pin}) is {'HIGH' if value == 1 else 'LOW'}")
    return value

def get_all_pins():
    return pin_mapping

def get_all_pin_values():
    for address in pin_states:
        try:
            pin_states[address][0] = bus.read_byte(address, GPIOA)
            pin_states[address][1] = bus.read_byte(address, GPIOB)
        except OSError as e:
            print(f"Error reading from address {address}: {e}")
            continue
    for global_pin, info in pin_mapping.items():
        address = info["address"]
        device_pin = info["pin"]
        pin_offset = device_pin % 8
        value = (pin_states[address][0 if device_pin < 8 else 1] >> pin_offset) & 1
        pin_values[global_pin] = {
            "name": info["name"],
            "address": info["address"],
            "pin": info["pin"],
            "description": info["description"],
            "direction": info["direction"],
            "value": value
        }
    return pin_values

def pretty_print_pins():
    get_all_pin_values()
    print("\nPin Values:")
    print("----------------------------------------------------------------")
    print("{:<8} {:<12} {:<8} {:<15} {:<10} {:<6}".format("GlobalPin", "DeviceName", "Address", "Description", "Direction", "Value"))
    print("----------------------------------------------------------------")
    for global_pin, info in pin_values.items():
        print("{:<8} {:<12} {:<8} {:<15} {:<10} {:<6}".format(
            global_pin,
            info["name"],
            hex(info["address"]),
            info["description"],
            info["direction"],
            "HIGH" if info["value"] == 1 else "LOW"
        ))
    print("----------------------------------------------------------------")

def cleanup():
    bus.close()

if __name__ == "__main__":
    pin_mapping = generate_pin_mapping(devices)
    try:
        set_pin_description(5, "Example Pin 5")
        set_pin_value(6, 0)
        get_pin(6)
        pretty_print_pins()
        configure_pin(15, "Temperature Sensor", "input")
        set_pin_value(15, 1)
        set_pin_value(10, 1)
        pretty_print_pins()
    except KeyboardInterrupt:
        print("Program stopped")
    finally:
        cleanup()

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("test/#")

def on_message(client, userdata, msg):
    command = msg.payload.decode().strip().split()
    response = ""
    if command[0] == "set_pin":
        pin = int(command[1])
        value = int(command[2])
        set_pin_value(pin, value)
        response = f"Set pin {pin} to {value}"
    elif command[0] == "get_pin":
        pin = int(command[1])
        pin_value = get_pin(pin)
        response = f"Pin {pin} is {'HIGH' if pin_value == 1 else 'LOW'}"
    elif command[0] == "set_description":
        pin = int(command[1])
        description = ' '.join(command[2:])
        set_pin_description(pin, description)
        response = f"Set description for pin {pin}"
    elif command[0] == "set_direction":
        pin = int(command[1])
        direction = command[2]
        set_pin_direction(pin, direction)
        response = f"Set direction for pin {pin} to {direction}"
    elif command[0] == "get_all_pins":
        pin_values = get_all_pin_values()
        response = pretty_print_pins()
    elif command[0] == "kurac":
        response = "jebem ti"
    else:
        response = f"Invalid command {msg}"
    print(response)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

broker_address = "127.0.0.1"  # Use the IP address of your broker if not running locally
client.connect(broker_address, 1883, 60)

pin_mapping = generate_pin_mapping(devices)

client.loop_forever()
