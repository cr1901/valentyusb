import cocotb
from cocotb.triggers import RisingEdge
from cocotb.result import TestFailure, ReturnValue
from cocotb.utils import get_sim_time

from cocotb_usb.usb.pid import PID
from cocotb_usb.usb.endpoint import EndpointType, EndpointResponse
from cocotb_usb.usb.packet import crc16

from cocotb_usb.utils import grouper_tofit, parse_csr, assertEqual

from cocotb_usb.host import UsbTest


class UsbTestCDCUsb(UsbTest):
    """Class for testing ValentyUSB IP core.
    Includes functions to communicate and generate responses without a CPU,
    making use of a Wishbone bridge.

    Args:
        dut : Object under test as passed by cocotb.
        csr_file (str): Path to a CSV file containing CSR register addresses,
            generated by Litex.
        decouple_clocks (bool, optional): Indicates whether host and device
            share clock signal. If set to False, you must provide clk48_device
            clock in test.
    """
    def __init__(self, dut, csr_file, **kwargs):
        # Litex imports
        from cocotb_usb.wishbone import WishboneMaster

        self.wb = WishboneMaster(dut, "wishbone", dut.clk12, timeout=20)
        self.csrs = dict()
        self.csrs = parse_csr(csr_file)
        super().__init__(dut, **kwargs)

        # Set the signal "test_name" to match this test
        import inspect
        tn = cocotb.binary.BinaryValue(value=None, n_bits=4096)
        tn.buff = inspect.stack()[2][3]
        self.dut.test_name = tn

    @cocotb.coroutine
    def write(self, addr, val):
        yield self.wb.write(addr, val)

    @cocotb.coroutine
    def read(self, addr):
        value = yield self.wb.read(addr)
        raise ReturnValue(value)
    
    @cocotb.coroutine
    def host_recv(self, data01, addr, epnum, data, timout=100):
        self.packet_deadline = get_sim_time("us") + 100
        yield super().host_recv(data01, addr, epnum, data)
