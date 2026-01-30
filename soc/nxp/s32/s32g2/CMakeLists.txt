# Copyright 2025 NXP
# SPDX-License-Identifier: Apache-2.0

zephyr_include_directories(.)

if(CONFIG_SOC_S32G274_M7)
  add_subdirectory(m7)
endif()

zephyr_library_sources(swt_disable.c)
