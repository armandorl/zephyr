#python3 -m venv ~/zephyrproject/.venv
#Activate the virtual environment:
#source ~/zephyrproject/.venv/bin/activate

west build -p always -b s32g274ardb/s32g274a/m7 project/zeus -DCONFIG_DEBUG=y
python3 scripts/mk_ivt.py scripts/s32g274ardb_flash_image.cfg
