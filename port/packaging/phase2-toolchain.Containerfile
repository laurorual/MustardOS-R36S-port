FROM localhost/muos-r35s-phase1-toolchain:20261023

RUN dpkg --add-architecture arm64 \
    && apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       libsdl2-dev:arm64 libpng-dev:arm64 pkgconf \
    && dpkg-query -W > /usr/local/share/phase2-packages.txt \
    && rm -rf /var/lib/apt/lists/*

ENV PKG_CONFIG_LIBDIR=/usr/lib/aarch64-linux-gnu/pkgconfig:/usr/share/pkgconfig
