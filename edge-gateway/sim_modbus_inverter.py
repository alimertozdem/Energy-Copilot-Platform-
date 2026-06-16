#!/usr/bin/env python3
# =============================================================================
# edge-gateway/sim_modbus_inverter.py
# SunSpec-flavoured Modbus TCP INVERTER SIMULATOR (dry-run, no hardware).
# =============================================================================
# Serves holding registers for a single PV inverter, driven by a time-of-day
# solar curve, so the Modbus gateway can be exercised end-to-end with NO real
# device. Register map (zero_mode addresses; one 16-bit holding register each):
#
#   reg 1  AC power           kW x10   (scale 0.1 -> kW)
#   reg 2  energy today       kWh      (scale 1.0, cumulative this run)
#   reg 3  DC power           kW x10   (scale 0.1 -> kW)
#   reg 4  inverter temp      degC     (scale 1.0)
#   reg 5  POA irradiance     W/m2     (scale 1.0)
#   reg 6  building load      kW x10   (scale 0.1 -> kW; enables self-consumption)
#
# Pair with config.modbus.solar.sim.json (matching registers/scales).
#   pip install pymodbus
#   python sim_modbus_inverter.py --host 127.0.0.1 --port 15020
# =============================================================================
import argparse
import asyncio
import logging
import math
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("sim_inverter")

AC_PEAK_KW = 41.5  # nameplate-ish peak AC for the simulated inverter


def solar_fraction(now: datetime) -> float:
    """0..1 bell over the solar day (~05:00-21:00 UTC). Crude but monotone/sane."""
    h = now.hour + now.minute / 60.0
    if h < 5.0 or h > 21.0:
        return 0.0
    return max(0.0, math.sin(math.pi * (h - 5.0) / 16.0))


def current_registers(energy_kwh: float) -> list:
    frac = solar_fraction(datetime.now(timezone.utc))
    ac_kw = AC_PEAK_KW * frac
    dc_kw = ac_kw / 0.97 if frac > 0 else 0.0
    temp_c = 25.0 + 15.0 * frac
    irr = 1000.0 * frac
    load_kw = 12.0 + 10.0 * frac   # building total load: baseload + daytime use
    # registers 1..6 (clamped to 16-bit)
    def u16(x):
        return max(0, min(65535, int(round(x))))
    return [u16(ac_kw * 10), u16(energy_kwh), u16(dc_kw * 10), u16(temp_c), u16(irr), u16(load_kw * 10)]


async def _update_loop(context, tick: float):
    from datetime import datetime as _dt
    energy = 0.0
    last = _dt.now(timezone.utc)
    while True:
        now = _dt.now(timezone.utc)
        dt_h = (now - last).total_seconds() / 3600.0
        last = now
        energy += AC_PEAK_KW * solar_fraction(now) * dt_h
        regs = current_registers(energy)
        context[0].setValues(3, 1, regs)  # fc=3 holding regs, addr 1.. (zero_mode)
        logger.info("SIM regs(1..5)=%s  (AC=%.1f kW, irr=%d W/m2)",
                    regs, regs[0] / 10.0, regs[4])
        await asyncio.sleep(tick)


async def main(host: str, port: int, tick: float):
    from pymodbus.datastore import ModbusSequentialDataBlock, ModbusServerContext
    try:
        from pymodbus.datastore import ModbusDeviceContext as _DeviceCtx  # pymodbus >= 3.9
    except ImportError:
        from pymodbus.datastore import ModbusSlaveContext as _DeviceCtx   # pymodbus < 3.9
    from pymodbus.server import StartAsyncTcpServer

    block = ModbusSequentialDataBlock(0, [0] * 16)
    device = _DeviceCtx(hr=block, zero_mode=True)
    try:
        context = ModbusServerContext(devices=device, single=True)        # pymodbus >= 3.9
    except TypeError:
        context = ModbusServerContext(slaves=device, single=True)         # pymodbus < 3.9
    asyncio.create_task(_update_loop(context, tick))
    logger.info("SIM inverter Modbus TCP server on %s:%d (registers 1..6)", host, port)
    await StartAsyncTcpServer(context=context, address=(host, port))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="SunSpec-flavoured Modbus inverter simulator")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=15020)
    p.add_argument("--tick", type=float, default=1.0, help="register update interval (s)")
    a = p.parse_args()
    try:
        asyncio.run(main(a.host, a.port, a.tick))
    except KeyboardInterrupt:
        pass
