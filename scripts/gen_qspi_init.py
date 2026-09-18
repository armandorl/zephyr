#!/usr/bin/python
"""
 Regenerate qspi_init.bin: BootROM QuadSPI Parameter Block for the S32G2 IVT.

 The original file configured the controller for Octal DTR (DDR, 8-pad,
 external DQS) boot reads, matching a MX25UW51245G in true Octal DTR mode.
 That mode was never actually entered on the flash, so at runtime the
 devicetree was changed to SDR + LOOPBACK (see s32g274ardb_zeus_s32g274a.dtsi)
 and confirmed working. This regenerates qspi_init.bin so the BootROM itself
 boots with the same working SDR/LOOPBACK single-pad Fast Read (0x0B)
 sequence, since for the XIP build the CPU fetches every instruction via
 this AHB path from the very first reset - there is no Zephyr driver
 available yet to fix a bad boot-time config.

 Only two things change vs the original file:
   - MCR: clear DDR_EN (bit7) and DQS_FA_SEL (bits 25:24) 3->1 (LOOPBACK)
   - COMMAND_SEQ (LUT sequence 0, used for AHB reads per BFGENCR SEQID=0):
     replaced with CMD(0x0B,1pad) / ADDR(24,1pad) / DUMMY(8,1pad) / READ(1pad)
 Everything else (FLSHCR, BFGENCR, DLLCR, SFACR, SMPR, DLCR, sizes, DLPR,
 SFAR, IPCR, TBDR, DLL flags, SFLASH_CLK_FREQ, FLASH_WRITE_DATA) is kept
 identical to the original qspi_init.bin.
"""

import struct

HEADER_MAGIC = 0x5A5A5A5A
OUTPUT_SIZE = 512

# LUT instruction encoding: (opcode << 10) | (pads << 8) | operand
INSTR_STOP = 0
INSTR_CMD = 1
INSTR_ADDR = 2
INSTR_DUMMY = 3
INSTR_READ = 7
PADS_1 = 0


def lut_instr(opcode, pads, operand):
    return (opcode << 10) | (pads << 8) | operand


def lut_word(instr_lo, instr_hi):
    return (instr_lo & 0xFFFF) | ((instr_hi & 0xFFFF) << 16)


with open("qspi_init.bin", "rb") as f:
    original = bytearray(f.read())

assert len(original) == OUTPUT_SIZE
assert struct.unpack_from("<I", original, 0x00)[0] == HEADER_MAGIC

# --- MCR: clear DDR_EN (bit7), change DQS_FA_SEL (bits25:24) from 3 to 1 ---
mcr = struct.unpack_from("<I", original, 0x04)[0]
mcr &= ~(1 << 7)                 # DDR_EN = 0 (SDR)
mcr &= ~(0x3 << 24)               # clear DQS_FA_SEL
mcr |= (0x1 << 24)                # DQS_FA_SEL = 1 (LOOPBACK)
struct.pack_into("<I", original, 0x04, mcr)

# --- COMMAND_SEQ (LUT sequence 0, offset 0x44): legacy Fast Read 0x0B ---
word0 = lut_word(lut_instr(INSTR_CMD, PADS_1, 0x0B),
                  lut_instr(INSTR_ADDR, PADS_1, 24))
word1 = lut_word(lut_instr(INSTR_DUMMY, PADS_1, 8),
                  lut_instr(INSTR_READ, PADS_1, 8))
word2 = lut_word(INSTR_STOP, INSTR_STOP)

struct.pack_into("<III", original, 0x44, word0, word1, word2)
# clear rest of the sequence 0 slot (up to the 320-byte COMMAND_SEQ region)
for off in range(0x44 + 12, 0x44 + 320, 4):
    struct.pack_into("<I", original, off, 0)

with open("qspi_init.bin", "wb") as f:
    f.write(original)

print("wrote qspi_init.bin: MCR=0x%08X" % mcr)
