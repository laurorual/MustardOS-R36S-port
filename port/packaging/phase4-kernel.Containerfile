FROM localhost/muos-r35s-phase3-toolchain:20261023

# The parent already pins Debian packages to the 20261023 snapshot.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       gcc:amd64 libc6-dev:amd64 bc bison flex libssl-dev:amd64 \
       device-tree-compiler kmod cpio python3 python-is-python3 \
    && dpkg-query -W > /usr/local/share/phase4-packages.txt \
    && rm -rf /var/lib/apt/lists/*

ENV PKG_CONFIG_LIBDIR=/usr/lib/x86_64-linux-gnu/pkgconfig:/usr/share/pkgconfig
ENV LC_ALL=C TZ=UTC
