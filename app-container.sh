#!/bin/bash

cd "$(dirname "$0")"

if [[ "$@" =~ "--build" ]]
then
    podman rm talon
    podman rmi talon:latest

    podman build \
        -t talon:latest \
        --network host \
        --cap-add NET_ADMIN \
        --cap-add SYS_MODULE \
        --no-cache \
        -f Containerfile .

    exit 0
fi

if [[ "$@" =~ "--update" ]]
then
    podman cp --overwrite . talon:/opt/talon/
fi

if [[ ! -e root ]]
then
    mkdir root
fi

podman run \
    --replace \
    --name talon \
    --interactive \
    --tty \
    --network host \
    --cap-add NET_ADMIN \
    --cap-add SYS_MODULE \
    --volume ./root:/root \
    talon:latest
