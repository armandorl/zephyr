---
description: "Use when editing devicetree source files (.dts, .dtsi), pinctrl headers, Kconfig files, or prj.conf for the S32G274A Zeus board. Covers correct node placement, pinmux macro naming, clock references, and peripheral enable conventions."
applyTo:
  - "**/*.dts"
  - "**/*.dtsi"
  - "**/prj.conf"
  - "**/*pinctrl*.h"
  - "**/Kconfig*"
---

# S32G274A Zephyr Devicetree Conventions

## SoC DTS Node Placement (`nxp_s32g274a.dtsi`)

- All new peripheral nodes go **inside** `soc { }` and **outside** the `#if 0` block.
- Never modify or remove the `#if 0 … #endif` block — it contains upstream stubs.
- Place new nodes before the final `};` that closes `soc { }`.
- Use tabs (not spaces) for indentation, matching the surrounding file style.

```dts
/* Correct placement — after #endif, inside soc { } */
        myperiph: myperiph@40001000 {
            compatible = "nxp,s32-myperiph";
            reg = <0x40001000 0x4000>;
            status = "disabled";
        };
    };  /* closes soc */
};      /* closes / */
```

## Pinctrl Groups (`zeus_s32g274a-pinctrl.dtsi`)

- Include `<nxp/s32/S32G274ARDB-pinctrl.h>` at the top (already present).
- Group names must match exactly what the driver node references via `pinctrl-0`.
- Use `output-enable`, `input-enable`, and `bias-pull-up` as needed.
- Bidirectional data pins need **both** `output-enable` and `input-enable`.

```dts
myperiph_default: myperiph_default {
    group1 {
        pinmux = <PA0_MYPERIPH_TX>;
        output-enable;
    };
    group2 {
        pinmux = <PA1_MYPERIPH_RX>;
        input-enable;
    };
};
```

## Pin Macro Naming Convention

All macros are in `modules/hal/nxp/dts/nxp/s32/S32G274ARDB-pinctrl.h`.
Format: `P<port><pin>_<signal_name>`

Search with:
```bash
grep "QUADSPI\|GMAC\|LINFLEXD\|<SIGNAL>" modules/hal/nxp/dts/nxp/s32/S32G274ARDB-pinctrl.h
```

## Board Enable (`zeus_s32g274a.dtsi`)

- Add `&<node> { status = "okay"; };` for each peripheral to enable.
- Add `pinctrl-0 = <&<group>_default>; pinctrl-names = "default";` when the driver requires it.
- Flash/storage child nodes go inside the controller node with `reg = <0>;`.

## Clock References

Use the constants from `include/zephyr/dt-bindings/clock/nxp_s32g274a_clock.h`:

| Peripheral | Clock symbol |
|-----------|-------------|
| LINFlexD | `NXP_S32_LINFLEXD_CLK` |
| QSPI (controller) | `NXP_S32_QSPI0_CLK` |
| QSPI 2x | `NXP_S32_QSPI_2X_CLK` |
| SWT0 | `NXP_S32_SWT0_CLK` |
| PIT0 | `NXP_S32_PIT0_CLK` |
| LPI2C0 | `NXP_S32_LPI2C0_CLK` |

## Kconfig (`prj.conf`)

| Feature | Correct Symbol |
|---------|----------------|
| Watchdog | `CONFIG_WATCHDOG=y` (not `CONFIG_WDT`) |
| Serial/UART | `CONFIG_SERIAL=y` |
| GPIO | `CONFIG_GPIO=y` |
| Flash | `CONFIG_FLASH=y` |
| Memory controller | `CONFIG_MEMC=y` |
| Ethernet | `CONFIG_NETWORKING=y` + `CONFIG_NET_L2_ETHERNET=y` |

## Common Pitfalls

- **Wrong Kconfig symbol**: `CONFIG_WDT` does not exist; use `CONFIG_WATCHDOG`.
- **LED/button aliases are not devices**: `DEVICE_DT_GET(DT_ALIAS(led0))` fails at link time — `led0` is a `gpio-leds` child, not a standalone device. Use `DEVICE_DT_GET(DT_NODELABEL(gpio0))` for the GPIO controller.
- **QSPI blocked**: `CONFIG_MEMC=y` + `CONFIG_FLASH=y` will fail to compile because `Qspi_Ip.h` is not provided by `modules/hal/nxp` for s32g2. Leave the board `&qspi0` block commented out until the HAL is ported.
- **DTS brace balance**: After adding a node to `nxp_s32g274a.dtsi`, confirm the file ends with `\t};\n};` (soc close + root close). Missing braces produce a cryptic `parse error` in `nxp_s32g274a_m7.dtsi`.
