#!/bin/bash
set -e

echo "Running Photogrammetry Docker Pipeline on Native Linux"

xhost +local:root

docker run --rm -it \
  --net=host \
  --ipc=host \
  --privileged \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v "$(pwd):/workspace" \
  -v /dev:/dev \
  stream-capture-pipeline

xhost -local:root

echo "Pipeline completed"