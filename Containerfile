# Use an official Debian slim image for a smaller footprint
FROM debian:trixie-slim

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Python, pip, and a virtual environment package
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    unzip \
    zip \
    git \
    curl \
    php8.4-cli \
    php8.4-sqlite \
    links \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /root

# (Optional) Copy requirements and install Python dependencies
# Uncomment the next two lines if you have a requirements.txt file
# COPY requirements.txt .
# RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy all files from your host directory to the container's working directory
COPY . /opt/talon

RUN cd /opt/talon \
    && rm -rf venv \
    && bash -c ./venv.sh

# Run your Python program
CMD ["bash", "-c", "[[ -e ~/start.sh ]] && . ~/start.sh; /opt/talon/app.sh"]
