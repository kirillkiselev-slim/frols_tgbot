FROM ubuntu:22.04 AS base

# Install necessary packages and dependencies for mlx
RUN apt-get update && apt-get install -y \
    xvfb \
    x11-utils \
    x11vnc \
    xauth \
    unzip \
    wget \
    curl \
    libayatana-appindicator3-dev \
    dbus-x11 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix

# Download and install mlx
RUN curl --location --fail --output mlxdeb.deb "https://mlxdists.s3.eu-west-3.amazonaws.com/mlx/1.15.0/multiloginx-amd64.deb" && \
    dpkg -i mlxdeb.deb && \
    apt-get install -f -y && \
    rm mlxdeb.deb

RUN groupadd -r myuser && useradd -r -g myuser -d /home/myuser -m myuser

# Copy your application code
COPY . /tg_bot

COPY requirements.txt /requirements.txt

RUN pip install -r requirements.txt --no-cache-dir

COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

RUN chown -R myuser:myuser /tg_bot

USER myuser

WORKDIR /tg_bot

ENTRYPOINT ["/entrypoint.sh"]
