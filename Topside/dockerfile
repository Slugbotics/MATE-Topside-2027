FROM --platform=linux/amd64 openmvs/openmvs-ubuntu:latest AS openmvs_source

FROM --platform=linux/amd64 openmvs/openmvs-ubuntu:latest AS library_collector

ENV OPENMVS_BIN=/usr/local/bin/OpenMVS
ENV OPENMVS_LIB=/usr/local/lib

ENV LD_LIBRARY_PATH=/usr/local/lib:/usr/lib/x86_64-linux-gnu:/lib/x86_64-linux-gnu:/usr/lib:/lib

RUN mkdir -p /isolated_libs

RUN echo "$OPENMVS_LIB" > /etc/ld.so.conf.d/openmvs.conf && ldconfig

SHELL ["/bin/bash", "-c"]

RUN set -euo pipefail; \
    echo "Looking through every openmvs binary."; \
    : > /tmp/queue;        \
    : > /tmp/visited;      \
    : > /tmp/missing;      \
    SKIP='^(libc\.so|libm\.so|libpthread\.so|libdl\.so|librt\.so|libstdc\+\+\.so|libgcc_s\.so|ld-linux|linux-vdso|statically)'; \
    \
    for bin in "$OPENMVS_BIN"/*; do \
        [ -f "$bin" ] && [ -x "$bin" ] && echo "$bin" >> /tmp/queue; \
    done; \
    \
    echo "Closing the passing dependencies."; \
    while [ -s /tmp/queue ]; do \
        target="$(head -n1 /tmp/queue)"; \
        sed -i '1d' /tmp/queue; \
        \
        grep -Fxq "$target" /tmp/visited && continue; \
        echo "$target" >> /tmp/visited; \
        \
        ldd "$target" 2>/dev/null | while read -r line; do \
            soname="$(echo "$line" | awk '{print $1}')"; \
            soname="$(basename "$soname")"; \
            path="$(echo "$line"   | awk '{if ($2 == "=>") print $3; else print $1}')"; \
            \
            echo "$soname" | grep -qE "$SKIP" && continue; \
            \
            if [ -z "$path" ] || [ "$path" = "not" ]; then \
                resolved="$(ldconfig -p | grep -F "$soname" | head -n1 | awk '{print $NF}')"; \
                if [ -z "$resolved" ]; then \
                    resolved="$(find / -name "$soname" 2>/dev/null | head -n1)"; \
                fi; \
                path="$resolved"; \
            fi; \
            \
            if [ -n "$path" ] && [ -e "$path" ]; then \
                cp -Lf "$path" "/isolated_libs/$soname" 2>/dev/null || true; \
                echo "$path" >> /tmp/queue; \
            else \
                echo "$soname" >> /tmp/missing; \
            fi; \
        done; \
    done; \
    \
    echo "Collected $(ls /isolated_libs | wc -l) shared libraries."; \
    if [ -s /tmp/missing ]; then \
        echo "The following sonames could not be resolved:"; \
        sort -u /tmp/missing; \
        exit 1; \
    else \
        echo "Everything is fine."; \
    fi

FROM --platform=linux/amd64 ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    colmap \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=openmvs_source    /usr/local/bin/OpenMVS /usr/local/bin/OpenMVS
COPY --from=library_collector /isolated_libs         /usr/local/lib/openmvs_libs

ENV PATH="/usr/local/bin/OpenMVS:${PATH}"

RUN echo "Verifying openmvs binaries..." && \
    miss=0; \
    for bin in /usr/local/bin/OpenMVS/*; do \
        if LD_LIBRARY_PATH=/usr/local/lib/openmvs_libs ldd "$bin" 2>/dev/null | grep -q "not found"; then \
            echo "Missing dependencies in $bin:"; \
            LD_LIBRARY_PATH=/usr/local/lib/openmvs_libs ldd "$bin" | grep "not found"; \
            miss=1; \
        fi; \
    done; \
    [ "$miss" -eq 0 ] && echo "All openmvs binaries are satisfied." || \
        (echo "Unmet dependencies remain." && exit 1)

RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel
RUN pip3 install --no-cache-dir opencv-python numpy ultralytics pygame

WORKDIR /workspace
RUN mkdir -p /workspace/workspace
COPY . /workspace

CMD ["python3", "cameras.py"]