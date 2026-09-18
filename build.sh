#python3 -m venv ~/zephyrproject/.venv
#Activate the virtual environment:
#source ~/zephyrproject/.venv/bin/activate

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
   count=$((0x2F0000 / 4096))


FLASHDIR=/mnt/c/Users/bardu/Documents/Programming/
cp salida.qspi ${FLASHDIR}
cp build-zeus-boards/zephyr/zephyr.elf ${FLASHDIR}

