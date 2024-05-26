EXPANDER_BOARD_TYPE = "PCF8574"

def setPin(bus, address, value):
    if EXPANDER_BOARD_TYPE == "PCF8547"
        bus.write_byte(address, value)
    elif EXPANDER_BOARD_TYPE == "MCP23017"
        pass
