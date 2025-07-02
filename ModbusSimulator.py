import time
from tango import AttrQuality, AttrWriteType, DevState, Attr, CmdArgType, UserDefaultAttrProp
from tango.server import Device, attribute, command, DeviceMeta
from tango.server import class_property, device_property, run
import os
import json
from json import JSONDecodeError
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.server.sync import StartTcpServer
import random
import logging

class ModbusSimulator(Device, metaclass=DeviceMeta):
    pass
    host = device_property(dtype=str, default_value="127.0.0.1")
    port = device_property(dtype=int, default_value=48123)

    @attribute
    def time(self):
        return time.time()

    def init_device(self):
        self.set_state(DevState.INIT)
        self.get_device_properties(self.get_device_class())

        # Enable logging (makes it easier to debug if something goes wrong)
        logging.basicConfig()
        log = logging.getLogger()
        log.setLevel(logging.DEBUG)
        # Define the Modbus registers
        coils = ModbusSequentialDataBlock(1, [False] * 100)
        discrete_inputs = ModbusSequentialDataBlock(1, [False] * 100)
        holding_registers = ModbusSequentialDataBlock(1, [0] * 100)
        input_registers = ModbusSequentialDataBlock(1, [0] * 100)
        temperature_values = [random.randint(4, 15) for _ in range(7)]
        holding_registers.setValues(1, temperature_values)
        print("temperature_values:", temperature_values)
        # Define the Modbus slave context
        slave_context = ModbusSlaveContext(
            di=discrete_inputs,
            co=coils,
            hr=holding_registers,
            ir=input_registers
        )
        # Define the Modbus server context
        server_context = ModbusServerContext(slaves=slave_context, single=True)
        self.set_state(DevState.ON)
        # Start the Modbus TCP server
        StartTcpServer(context=server_context, address=(self.host, self.port))

if __name__ == "__main__":
    deviceServerName = os.getenv("DEVICE_SERVER_NAME", "ModbusSimulator")
    run({deviceServerName: ModbusSimulator})