from smbus2 import SMBus
bus = SMBus(1)

devices = [
    ("pcf8574_1", 0x20),
    ("pcf8574_2", 0x24),
    ("pcf8574_3", 0x26)
]

# Initialize the pin states for each device
pin_states = {address: 0xFF for name, address in devices}

pin_mapping = {}
pin_values = {}

def generate_pin_mapping(devices):
    pin_mapping = {}
    pin_offset = 0
    for name, address in devices:
        for pin in range(8):
            pin_mapping[pin_offset + pin] = {
                "name": name,
                "address": address,
                "pin": pin,
                "description": "",
                "direction": ""  # Default direction
            }
        pin_offset += 8
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
    pin_mapping[pin]["direction"] = direction
    print(f"Set direction for pin {pin} (device {pin_mapping[pin]['name']} pin {pin_mapping[pin]['pin']}) to '{direction}'")

def set_pin_value(pin, value):
    if pin not in pin_mapping:
        raise ValueError(f"Pin {pin} is not valid")
    pin_info = pin_mapping[pin]
    name = pin_info["name"]
    address = pin_info["address"]
    device_pin = pin_info["pin"]

    global pin_states
    if value == 1:
        pin_states[address] |= (1 << device_pin)
    else:
        pin_states[address] &= ~(1 << device_pin)

    bus.write_byte(address, pin_states[address])
    print(f"Set pin {pin} (device {name} pin {device_pin}) to {'HIGH' if value == 1 else 'LOW'}")

def get_pin(pin):
    if pin not in pin_mapping:
        raise ValueError(f"Pin {pin} is not valid")
    pin_info = pin_mapping[pin]
    name = pin_info["name"]
    address = pin_info["address"]
    device_pin = pin_info["pin"]

    global pin_states
    pin_states[address] = bus.read_byte(address)
    value = (pin_states[address] >> device_pin) & 1
    print(f"Pin {pin} (device {name} pin {device_pin}) is {'HIGH' if value == 1 else 'LOW'}")
    return value

def get_all_pins():
    return pin_mapping

def get_all_pin_values():
    for address in pin_states:
        try:
            pin_states[address] = bus.read_byte(address)
        except OSError as e:
            print(f"Error reading from address {address}: {e}")
            continue
    for global_pin, info in pin_mapping.items():
        address = info["address"]
        device_pin = info["pin"]
        value = (pin_states[address] >> device_pin) & 1
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
        configure_pin(15, "Senzor temperature", "input")
        set_pin_value(15, 1)
        set_pin_value(10, 1)
        pretty_print_pins()
    except KeyboardInterrupt:
        print("Program stopped")
    finally:
        cleanup()

