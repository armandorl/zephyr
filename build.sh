#!/bin/bash
set -e

#python3 -m venv ~/zephyrproject/.venv
#Activate the virtual environment:
#source ~/zephyrproject/.venv/bin/activate
#python3 -m pip install pycryptodome
####west build -p always -b s32g274ardb/s32g274a/m7 samples/basic/minimal -DCONFIG_DEBUG=y
####python3 scripts/mk_ivt.py scripts/s32g274ardb_flash_image.cfg
#echo "Sleep 5 activated!!!!!!!!!!!!!"
#sleep 5
#west build -b s32g274ardb_zeus/s32g274a/m7 project/zeus -d ../build-zeus-ram -- -DOVERLAY_CONFIG=prj_ram.conf
#echo "Sleep 5 activated!!!!!!!!!!!!!"
#sleep 5
#west build -p always -b s32g274ardb_zeus/s32g274a/m7 -d build-zeus-boards project/zeus -DCONFIG_DEBUG=y
west build -p always -b zeus/s32g274a/m7 -d build-zeus-boards project/zeus -DCONFIG_DEBUG=y
python3 scripts/dcd_gen.py
source sign_fip.sh
python3 scripts/mk_ivt.py scripts/zeus_flash_image.cfg
#echo "Sleep 5 activated!!!!!!!!!!!!!"
#sleep 5
#python3 scripts/mk_ivt.py scripts/s32g274ardb_flash_image.cfg
../bin/zephyr-sdk-0.16.8/arm-zephyr-eabi/arm-zephyr-eabi/bin/objdump -d -S build-zeus-boards/zephyr/zephyr.elf > disasm_src.txt

# For uboot load in sram
#setenv init_sram 'mw.l 0x4019C004 0x00000000; mw.l 0x4019C008 0x00007FFF; mw.l 0x4019C000 0x00000001; mw.l 0x401A0004 0x00000000; mw.l 0x401A0008 0x00007FFF; mw.l 0x401A0000 0x00000001; mw.l 0x44028004 0x00000000; mw.l 0x44028008 0x000000FF; mw.l 0x44028000 0x00000001'
#setenv boot_zeus 'run init_sram; tftpboot zephyr.elf || tftpboot zephyr.elf || tftpboot zephyr.elf; bootm7 0x80000000 0x34000000'
#run boot_zeus

dd if=/media/armandorl/ubuntu/s32g2/zephyrproject/zephyr/build/zeus_ivt_image.qspi \
   of=salida.qspi \
   bs=4096 \
   count=$((0x600000 / 4096))


SIZE=$(stat -c%s /media/armandorl/ubuntu/s32g2/zephyrproject/zephyr/build-zeus-boards/zephyr/zephyr.bin)
dd if=/media/armandorl/ubuntu/s32g2/zephyrproject/zephyr/build/zeus_ivt_image.qspi \
   of=zeus_serial_boot.bin \
   bs=1 \
   skip=$((0x01FFFC0)) \
   count=$SIZE

dd if=/media/armandorl/ubuntu/s32g2/zephyrproject/zephyr/build/zeus_ivt_image.qspi \
   of=zeus_fip.bin \
   bs=1 \
   skip=$((0x400000)) \
   count=$((0x200000))



FLASHDIR=/mnt/c/Users/bardu/Documents/Programming/
cp salida.qspi ${FLASHDIR}
cp salida.qspi /mnt/c/tftpboot/
cp build-zeus-boards/zephyr/zephyr.elf ${FLASHDIR}
cp build-zeus-boards/zephyr/zephyr.elf /mnt/c/tftpboot/
cp zeus_serial_boot.bin  /mnt/c/tftpboot/
cp build-zeus-boards/zephyr/zephyr.bin /mnt/c/tftpboot/
cp zeus_fip.bin  /mnt/c/tftpboot/
cp zeus_payload.sigblob /mnt/c/tftpboot/
cp /media/armandorl/ubuntu/s32g2/linux/arch/arm64/boot/dts/freescale/s32g274a-zeus-flasher.dtb /mnt/c/tftpboot/
cp /media/armandorl/ubuntu/s32g2/linux/arch/arm64/boot/Image /mnt/c/tftpboot/
# Compressed image
cp /media/armandorl/ubuntu/s32g2/linux/arch/arm64/boot/uImage /mnt/c/tftpboot/
cp /media/armandorl/ubuntu/s32g2/zephyrproject/zephyr/build/zeus_ivt_image.qspi /mnt/c/tftpboot/
cp /media/armandorl/ubuntu/s32g2/rootfs/uRamdisk /mnt/c/tftpboot/
