FROM localhost/muos-r35s-phase4-kernel:20261024

# Inherits the fixed Debian snapshot; dependencies stay inside the container.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       g++:amd64 wget curl ca-certificates patch unzip rsync bzip2 xz-utils git \
       libncurses-dev:amd64 locales qemu-user:amd64 e2fsprogs:amd64 \
    && dpkg-query -W > /usr/local/share/phase4-rootfs-packages.txt \
    && rm -rf /var/lib/apt/lists/*

ENV LC_ALL=C TZ=UTC
