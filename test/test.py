# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge
from cocotb.triggers import ClockCycles
from cocotb.types import Logic
from cocotb.types import LogicArray

async def await_half_sclk(dut):
    """Wait for the SCLK signal to go high or low."""
    start_time = cocotb.utils.get_sim_time(units="ns")
    while True:
        await ClockCycles(dut.clk, 1)
        # Wait for half of the SCLK period (10 us)
        if (start_time + 100*100*0.5) < cocotb.utils.get_sim_time(units="ns"):
            break
    return

def ui_in_logicarray(ncs, bit, sclk):
    """Setup the ui_in value as a LogicArray."""
    return LogicArray(f"00000{ncs}{bit}{sclk}")

async def send_spi_transaction(dut, r_w, address, data):
    """
    Send an SPI transaction with format:
    - 1 bit for Read/Write
    - 7 bits for address
    - 8 bits for data
    
    Parameters:
    - r_w: boolean, True for write, False for read
    - address: int, 7-bit address (0-127)
    - data: LogicArray or int, 8-bit data
    """
    # Convert data to int if it's a LogicArray
    if isinstance(data, LogicArray):
        data_int = int(data)
    else:
        data_int = data
    # Validate inputs
    if address < 0 or address > 127:
        raise ValueError("Address must be 7-bit (0-127)")
    if data_int < 0 or data_int > 255:
        raise ValueError("Data must be 8-bit (0-255)")
    # Combine RW and address into first byte
    first_byte = (int(r_w) << 7) | address
    # Start transaction - pull CS low
    sclk = 0
    ncs = 0
    bit = 0
    # Set initial state with CS low
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 1)
    # Send first byte (RW + Address)
    for i in range(8):
        bit = (first_byte >> (7-i)) & 0x1
        # SCLK low, set COPI
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # SCLK high, keep COPI
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # Send second byte (Data)
    for i in range(8):
        bit = (data_int >> (7-i)) & 0x1
        # SCLK low, set COPI
        sclk = 0
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
        # SCLK high, keep COPI
        sclk = 1
        dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
        await await_half_sclk(dut)
    # End transaction - return CS high
    sclk = 0
    ncs = 1
    bit = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    await ClockCycles(dut.clk, 600)
    return ui_in_logicarray(ncs, bit, sclk)

@cocotb.test()
async def test_spi(dut):
    dut._log.info("Start SPI test")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Reset
    dut._log.info("Reset")
    dut.ena.value = 1
    ncs = 1
    bit = 0
    sclk = 0
    dut.ui_in.value = ui_in_logicarray(ncs, bit, sclk)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)

    dut._log.info("Test project behavior")
    dut._log.info("Write transaction, address 0x00, data 0xF0")
    ui_in_val = await send_spi_transaction(dut, 1, 0x00, 0xF0)  # Write transaction
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 1000) 

    dut._log.info("Write transaction, address 0x01, data 0xCC")
    ui_in_val = await send_spi_transaction(dut, 1, 0x01, 0xCC)  # Write transaction
    assert dut.uio_out.value == 0xCC, f"Expected 0xCC, got {dut.uio_out.value}"
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x30 (invalid), data 0xAA")
    ui_in_val = await send_spi_transaction(dut, 1, 0x30, 0xAA)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Read transaction (invalid), address 0x00, data 0xBE")
    ui_in_val = await send_spi_transaction(dut, 0, 0x30, 0xBE)
    assert dut.uo_out.value == 0xF0, f"Expected 0xF0, got {dut.uo_out.value}"
    await ClockCycles(dut.clk, 100)
    
    dut._log.info("Read transaction (invalid), address 0x41 (invalid), data 0xEF")
    ui_in_val = await send_spi_transaction(dut, 0, 0x41, 0xEF)
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x02, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x02, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 100)

    dut._log.info("Write transaction, address 0x04, data 0xCF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xCF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0xFF")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0xFF)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x00")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x00)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("Write transaction, address 0x04, data 0x01")
    ui_in_val = await send_spi_transaction(dut, 1, 0x04, 0x01)  # Write transaction
    await ClockCycles(dut.clk, 30000)

    dut._log.info("SPI test completed successfully")

@cocotb.test()
async def test_pwm_freq(dut):
    # Write your test here
    dut._log.info("PWM Frequency test completed successfully")


@cocotb.test()
async def test_pwm_duty(dut):
    # Write your test here
    dut._log.info("PWM Duty Cycle test completed successfully")

@cocotb.test()
async def levelling(dut, prev_level, desired_level, max_cycles=5000):
    for i in range(max_cycles):
        await ClockCycles(dut.clk, 1)
        if (int(dut.uo_out.value) & 1) == prev_level:
            break
    else:
        stuck = int(dut.uo_out.value) & 1
        raise TestFailure(
            f"Timeout: PWM never reached prev_level={prev_level}; stuck at {stuck} after {max_cycles} cycles"
        )
    for i in range(max_cycles):
        await ClockCycles(dut.clk, 1)
        bit0 = int(dut.uo_out.value) & 1
        if bit0 == desired_level:
            return get_sim_time("ns")
    stuck = (int(dut.uo_out.value) & 1)
    raise TestFailure(f"Timeout: PWM never reached {desired_level}; stuck at {stuck} after {max_cycles} cycles")


## lets go
@cocotb.test()
async def test_pwm_freq_1khz(dut):
    clk = Clock(dut.clk, 100, units="ns")  # 10 mhz clock
    cocotb.start_soon(clk.start())

    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.ena.value = 1
    dut.ui_in.value = ui_in_logicarray(1, 0, 0)

    # configure for 1khz pwm
    await send_spi_transaction(dut, 1, 0x00, 0x01)
    await send_spi_transaction(dut, 1, 0x02, 3)  # new value for 1khz
    await send_spi_transaction(dut, 1, 0x04, 128)  # 50% duty

    await ClockCycles(dut.clk, 10000)

    first_rise = await wait_for_level(dut, 0, 1, max_cycles=5000)
    other_rise = await wait_for_level(dut, 0, 1, max_cycles=5000)

    period_ns = other_rise - first_rise
    freq_hz = 1e9 / period_ns

    assert 990 <= freq_hz <= 1010, f"Measured {freq_hz:.1f} Hz; expected 1000 Hz ±1%"
    dut._log.info(f"PWM freq OK: {freq_hz:.1f} Hz")


@cocotb.test()
async def test_pwm_duty_25_75(dut):
    clk = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clk.start())

    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 5)
    dut.ena.value = 1
    dut.ui_in.value = ui_in_logicarray(1, 0, 0)

    await send_spi_transaction(dut, 1, 0x00, 0x01)
    await send_spi_transaction(dut, 1, 0x02, 3)  # 1khz freq

    pwm_signal = dut.uo_out[0]

    # 25% duty
    await send_spi_transaction(dut, 1, 0x04, 64)  # 64/255 ≈ 25%
    await ClkCycles(dut.clk, 10000)

    p1 = await wait_for_level(dut, 0, 1, max_cycles=5000)
    pf = await wait_for_level(dut, 1, 0, max_cycles=5000)
    p2 = await wait_for_level(dut, 0, 1, max_cycles=5000)

    high_ns = pf - p1
    period_ns = p2 - p1
    duty = 100 * high_ns / period_ns
    assert 24 <= duty <= 26, f"25%: measured {duty:.1f}%, outside expected range"

    # 75% duty
    await send_spi_transaction(dut, 1, 0x04, 192)  # 192/255 ≈ 75%
    await ClockCycles(dut.clk, 10000)

    p1 = await wait_for_level(dut, 0, 1, max_cycles=5000)
    pf = await wait_for_level(dut, 1, 0, max_cycles=5000)
    p2 = await wait_for_level(dut, 0, 1, max_cycles=5000)

    high_ns = pf - p1
    period_ns = p2 - p1
    duty = 100 * high_ns / period_ns
    assert 74 <= duty <= 76, f"75%: measured {duty:.1f}%, outside expected range"

    dut._log.info("PWM duty-cycle 25% and 75% tests passed")
