# Zeus S32G274A Zephyr Project — Copilot Instructions

## Project Context

This is an active port of an NXP S32G274A (Cortex-M7) application from NXP S32 Design Studio
(RTD + FreeRTOS) to Zephyr RTOS. The target board is `zeus/s32g274a/m7`.

The application being ported is in `/media/armandorl/ubuntu/s32g2/rtd_app_fota/` and includes:
UDS/OTA stack, Transport Protocol (CAN/DoIP), Uptane, lwIP networking, IPC, HSE crypto, and a
bootloader that starts A53 cores.

## Build System

- **Build tool**: `west` (Zephyr meta-tool)
- **Build directory**: `build-zeus-boards/`
- **Board**: `zeus/s32g274a/m7` — local board, BOARD_ROOT set in `project/zeus/CMakeLists.txt`
- **Post-build**: `python3 scripts/mk_ivt.py scripts/zeus_flash_image.cfg` produces the QSPI image

Canonical build:
```bash
cd /media/armandorl/ubuntu/s32g2/zephyrproject/zephyr
west build -p always -b zeus/s32g274a/m7 -d build-zeus-boards project/zeus -DCONFIG_DEBUG=y
python3 scripts/mk_ivt.py scripts/zeus_flash_image.cfg
```

Both commands must exit 0. Always run both after any change.

## Application Architecture

The converted application uses a two-level Zephyr structure:

1. `main()` — platform init (watchdog, device readiness) then spawns `zeus_app_thread`
2. `zeus_app_thread` — init sequence (IPC, network, UDS) then periodic service loop

All subsystem entry points are **weak symbols** (`zeus_platform_init`, `zeus_ipc_init`,
`zeus_network_init`, `zeus_uds_stack_init`, `zeus_watchdog_kick`, `zeus_tp_mainfun`,
`zeus_ota_manage_mainfun`, `zeus_uds_server_mainfun`, `zeus_uptane_mainfun`) so modules
can be ported incrementally without rewriting the main flow.

## Key Conventions

- **Read before editing**: Always read the current file before modifying it.
- **No invented addresses**: Peripheral base addresses come from
  `modules/hal/nxp/s32/drivers/s32g2/BaseNXP/header/S32G274A_<PERIPH>.h`.
- **No invented pin names**: Pin macros come from
  `modules/hal/nxp/dts/nxp/s32/S32G274ARDB-pinctrl.h`.
- **No invented clock symbols**: Clock IDs come from
  `include/zephyr/dt-bindings/clock/nxp_s32g274a_clock.h`.
- **HAL availability check**: Before enabling any Zephyr driver that wraps RTD,
  verify `<Periph>_Ip.h` exists in `modules/hal/nxp/s32/drivers/s32g2/`.
- **Kconfig**: Use `CONFIG_WATCHDOG`, not `CONFIG_WDT`.
- **DTS brace balance**: When editing `nxp_s32g274a.dtsi`, the file must end with
  the `soc { }` close then the `/ { }` close — verify with `tail -5`.

## Porting Checklist per Peripheral

1. Find base address in NXP HAL header
2. Check if `nxp,s32-<periph>` Zephyr driver exists in `zephyr/drivers/`
3. Verify HAL IP header exists for s32g2 (if driver wraps RTD)
4. Add DTS node to `dts/arm/nxp/nxp_s32g274a.dtsi` (outside `#if 0`)
5. Add pinctrl group to `zeus_s32g274a-pinctrl.dtsi`
6. Enable with `status = "okay"` in `zeus_s32g274a.dtsi`
7. Enable Kconfig in `project/zeus/prj.conf`
8. Build and fix errors

## Known Blockers

- **QSPI flash driver**: `Qspi_Ip.h` not present in `hal_nxp` for s32g2. DTS node
  `qspi0` exists at `0x40134000` but the board enable block is commented out pending HAL port.
- **GMAC Ethernet**: Driver exists (`eth_nxp_s32_gmac.c`), DTS node not yet added to s32g274a.dtsi,
  HAL availability for s32g2 not confirmed.
- **CAN (FlexCAN)**: Nodes exist in `#if 0` block in `nxp_s32g274a.dtsi` — upstream stub.

## ADC Macro Warning (non-fatal)

The build produces `IP_ADC_0_BASE redefined` warnings from an include collision between
`soc/nxp/s32/s32g2/m7/soc.h` and `S32G274A_ADC.h`. These are warnings only and do not
affect the binary.
