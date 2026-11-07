FROM localhost/muos-r35s-phase2-toolchain:20261023

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       ccache python3 libsdl2-image-dev:arm64 libsdl2-mixer-dev:arm64 \
       libsdl2-ttf-dev:arm64 libcurl4-openssl-dev:arm64 libharfbuzz-dev:arm64 \
       libavformat-dev:arm64 libavcodec-dev:arm64 libswscale-dev:arm64 \
       libswresample-dev:arm64 libavutil-dev:arm64 libarchive-dev:arm64 \
       libssl-dev:arm64 \
    && dpkg-query -W > /usr/local/share/phase3-packages.txt \
    && rm -rf /var/lib/apt/lists/*
