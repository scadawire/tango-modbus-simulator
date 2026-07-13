import time
from tango import AttrQuality, AttrWriteType, DevState, Attr, CmdArgType, UserDefaultAttrProp
from tango.server import Device, attribute, command, DeviceMeta
from tango.server import class_property, device_property, run
import os
import json
from json import JSONDecodeError
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.server.sync import ModbusTcpServer, ModbusSerialServer
from pymodbus.transaction import ModbusRtuFramer
import random
import logging
import threading

class ModbusSimulator(Device, metaclass=DeviceMeta):

    host = device_property(dtype=str, default_value="127.0.0.1")
    port = device_property(dtype=int, default_value=48123)
    protocol = device_property(dtype=str, default_value="tcp")  # "tcp" or "rtu"
    serial_port = device_property(dtype=str, default_value="/dev/ttyUSB0")
    baudrate = device_property(dtype=int, default_value=9600)
    parity = device_property(dtype=str, default_value="N")  # N, E, O
    stopbits = device_property(dtype=int, default_value=1)
    bytesize = device_property(dtype=int, default_value=8)

    _server = None
    _server_thread = None

    @attribute
    def time(self):
        return time.time()

    def init_device(self):
        self.set_state(DevState.INIT)
        self.get_device_properties(self.get_device_class())
        self._stop_server()

        logging.basicConfig()
        log = logging.getLogger()
        log.setLevel(logging.DEBUG)

        coils = ModbusSequentialDataBlock(1, [False] * 100)
        discrete_inputs = ModbusSequentialDataBlock(1, [False] * 100)
        holding_registers = ModbusSequentialDataBlock(1, [0] * 100)
        input_registers = ModbusSequentialDataBlock(1, [0] * 100)
        temperature_values = [random.randint(4, 15) for _ in range(7)]
        holding_registers.setValues(1, temperature_values)
        print("temperature_values:", temperature_values)

        slave_context = ModbusSlaveContext(
            di=discrete_inputs,
            co=coils,
            hr=holding_registers,
            ir=input_registers
        )
        server_context = ModbusServerContext(slaves=slave_context, single=True)

        if self.protocol.lower() == "tcp":
            # allow_reuse_address has to be passed to the constructor: it assigns the argument
            # (default False) to the instance, so setting the class attribute has no effect. Without
            # it a restart fails with "address already in use" for as long as the connections of the
            # previous run linger in TIME_WAIT.
            self._server = ModbusTcpServer(
                server_context,
                address=(self.host, self.port),
                allow_reuse_address=True,
            )
            self._server_thread = threading.Thread(
                target=self._server.serve_forever, daemon=True,
            )
            self._server_thread.start()
            self.info_stream(f"Modbus TCP server started on {self.host}:{self.port}")
        elif self.protocol.lower() == "rtu":
            # the serial server opens the port in its constructor and then blocks in serve_forever,
            # so it has to run in a thread: init_device must return for the device to be exported
            self._server = ModbusSerialServer(
                server_context,
                framer=ModbusRtuFramer,
                port=self.serial_port,
                baudrate=self.baudrate,
                parity=self.parity,
                stopbits=self.stopbits,
                bytesize=self.bytesize,
                timeout=1
            )
            self._server_thread = threading.Thread(
                target=self._server.serve_forever, daemon=True,
            )
            self._server_thread.start()
            self.info_stream(f"Modbus RTU server started on {self.serial_port}")

        self.set_state(DevState.ON)

    def _stop_server(self):
        if self._server is not None:
            # only the tcp server is socketserver based and has shutdown(), the serial one stops
            # serving once is_running is cleared by server_close()
            if hasattr(self._server, "shutdown"):
                self._server.shutdown()
            self._server.server_close()
            self._server = None
        if self._server_thread is not None:
            self._server_thread.join(timeout=5)
            self._server_thread = None

    def delete_device(self):
        self._stop_server()
        self.info_stream("Modbus server stopped")

if __name__ == "__main__":
    deviceServerName = os.getenv("DEVICE_SERVER_NAME", "ModbusSimulator")
    run({deviceServerName: ModbusSimulator})