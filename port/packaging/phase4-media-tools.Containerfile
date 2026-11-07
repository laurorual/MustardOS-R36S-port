FROM localhost/muos-r35s-phase4-kernel:20261024

# Parent uses the fixed Debian snapshot; tools only, never installed on Bazzite.
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends dosfstools mtools \
    && dpkg-query -W dosfstools mtools > /usr/local/share/phase4-media-packages.txt \
    && rm -rf /var/lib/apt/lists/*
