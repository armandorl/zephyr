#!/bin/bash

set -e

FIP_IMAGE="/media/armandorl/ubuntu/s32g2/arm-trusted-firmware/build/s32g274ardb2/debug/fip.bin"
PRIVATE_KEY="/media/armandorl/ubuntu/s32g2/zeus_fip_keys/private.pem"
PAYLOAD_OFFSET=0x40

echo "Signing payload..."

openssl dgst \
    -sha256 \
    -sign "${PRIVATE_KEY}" \
    -out zeus_payload.sig \
    ${FIP_IMAGE}

IMAGE_SIZE=$(stat -c%s ${FIP_IMAGE})
SIG_SIZE=$(stat -c%s zeus_payload.sig)

echo "Image size : ${IMAGE_SIZE}"
echo "Signature size : ${SIG_SIZE}"

echo "Creating signature header..."

python3 << EOF
import struct

MAGIC = 0x31474953  # "SIG1" little-endian

image_size = ${IMAGE_SIZE}
sig_size = ${SIG_SIZE}

with open("zeus_payload.sig.hdr", "wb") as f:
    f.write(struct.pack(
        "<III",
        MAGIC,
        image_size,
        sig_size
    ))
EOF

echo "Creating final signature blob..."

cat zeus_payload.sig.hdr \
    zeus_payload.sig \
    > zeus_payload.sigblob

echo
echo "Artifacts:"
echo "  zeus_fip.bin"
echo "  zeus_payload.bin"
echo "  zeus_payload.sig"
echo "  zeus_payload.sigblob"
echo

hexdump -C zeus_payload.sig.hdr
