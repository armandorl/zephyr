#python3 -m venv ~/zephyrproject/.venv
#Activate the virtual environment:
#source ~/zephyrproject/.venv/bin/activate

west build -p always -b s32g274ardb/s32g274a/m7 samples/basic/minimal -DCONFIG_DEBUG=y
