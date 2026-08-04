/*
 * Copyright 2025 NXP
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#ifndef ZEPHYR_SOC_NXP_S32_S32G2_PINCTRL_SOC_H_
#define ZEPHYR_SOC_NXP_S32_S32G2_PINCTRL_SOC_H_

#include <zephyr/drivers/pinctrl/pinctrl_nxp_siul2_common.h>
#include <zephyr/dt-bindings/pinctrl/nxp-siul2-pinctrl.h>
#include <zephyr/sys/util.h>

/* SIUL2 Multiplexed Signal Configuration */
#define SIUL2_MSCR_SSS_MASK	GENMASK(3, 0)
#define SIUL2_MSCR_SSS(v)	FIELD_PREP(SIUL2_MSCR_SSS_MASK, (v))
#define SIUL2_MSCR_SMC_MASK	BIT(5)
#define SIUL2_MSCR_SMC(v)	FIELD_PREP(SIUL2_MSCR_SMC_MASK, (v))
#if 0 /* Not defined for s32g274 */
#define SIUL2_MSCR_IFE_MASK	BIT(6)
#define SIUL2_MSCR_IFE(v)	FIELD_PREP(SIUL2_MSCR_IFE_MASK, (v))
#define SIUL2_MSCR_DSE_MASK	BIT(8)
#define SIUL2_MSCR_DSE(v)	FIELD_PREP(SIUL2_MSCR_DSE_MASK, (v))
#endif
#define SIUL2_MSCR_PUE_MASK	BIT(13)
#define SIUL2_MSCR_PUE(v)	FIELD_PREP(SIUL2_MSCR_PUE_MASK, (v))
#define SIUL2_MSCR_PUS_MASK	BIT(12)
#define SIUL2_MSCR_PUS(v)	FIELD_PREP(SIUL2_MSCR_PUS_MASK, (v))
/* S32G274 slew-rate control uses MSCR bits 14..16. */
#define SIUL2_MSCR_SRC_MASK	GENMASK(16, 14)
#define SIUL2_MSCR_SRC(v)	FIELD_PREP(SIUL2_MSCR_SRC_MASK, (v))
#define SIUL2_MSCR_SRC_ENUM_TO_VAL(idx) \
	((idx) == 0 ? 0U : (idx) == 1 ? 4U : (idx) == 2 ? 5U : (idx) == 3 ? 6U : 7U)
#define SIUL2_MSCR_DSE_MASK	0U
#define SIUL2_MSCR_DSE(v)	0U
#define SIUL2_MSCR_IBE_MASK	BIT(19)
#define SIUL2_MSCR_IBE(v)	FIELD_PREP(SIUL2_MSCR_IBE_MASK, (v))
#define SIUL2_MSCR_ODE_MASK	BIT(20)
#define SIUL2_MSCR_ODE(v)	FIELD_PREP(SIUL2_MSCR_ODE_MASK, (v))
#define SIUL2_MSCR_OBE_MASK	BIT(21)
#define SIUL2_MSCR_OBE(v)	FIELD_PREP(SIUL2_MSCR_OBE_MASK, (v))
#define SIUL2_MSCR_ICE_MASK	BIT(22)
#define SIUL2_MSCR_ICE(v)	FIELD_PREP(SIUL2_MSCR_ICE_MASK, (v))
#define SIUL2_MSCR_RCVR_MASK	BIT(25)
#define SIUL2_MSCR_RCVR(v)	FIELD_PREP(SIUL2_MSCR_RCVR_MASK, (v))
/* SIUL2 Input Multiplexed Signal Configuration */
#define SIUL2_IMCR_SSS_MASK	GENMASK(3, 0)
#define SIUL2_IMCR_SSS(v)	FIELD_PREP(SIUL2_IMCR_SSS_MASK, (v))

#define NXP_SIUL2_PINMUX_INIT(group, value)                                                        \
	.mscr = {                                                                                  \
		.inst = NXP_SIUL2_PINMUX_GET_MSCR_SIUL2_IDX(value),                                \
		.idx = NXP_SIUL2_PINMUX_GET_MSCR_IDX(value),                                       \
		.val = SIUL2_MSCR_SSS(NXP_SIUL2_PINMUX_GET_MSCR_SSS(value)) |                      \
		       SIUL2_MSCR_OBE(DT_PROP(group, output_enable)) |                             \
		       SIUL2_MSCR_ODE(DT_PROP_OR(group, drive_open_drain, 0) &&                    \
				      DT_PROP(group, output_enable)) |                             \
		       SIUL2_MSCR_IBE(DT_PROP(group, input_enable)) |                              \
		       SIUL2_MSCR_PUE(DT_PROP(group, bias_pull_up) ||                              \
				      DT_PROP(group, bias_pull_down)) |                            \
		       SIUL2_MSCR_PUS(DT_PROP(group, bias_pull_up)) |                              \
		       SIUL2_MSCR_SRC(SIUL2_MSCR_SRC_ENUM_TO_VAL(DT_ENUM_IDX_OR(group,            \
							    slew_rate, 1)))         \
	},                                                                                         \
	.imcr = {                                                                                  \
		.inst = NXP_SIUL2_PINMUX_GET_IMCR_SIUL2_IDX(value),                                \
		.idx = NXP_SIUL2_PINMUX_GET_IMCR_IDX(value),                                       \
		.val = SIUL2_IMCR_SSS(NXP_SIUL2_PINMUX_GET_IMCR_SSS(value)),                       \
	}

#endif /* ZEPHYR_SOC_NXP_S32_S32G2_PINCTRL_SOC_H_ */
