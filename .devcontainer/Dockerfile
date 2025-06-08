FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

# Install system dependencies for Python packages
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    libzbar0 \
    libzbar-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# The base image already has vscode user, just ensure workspace permissions
RUN mkdir -p /workspace && chown -R vscode:vscode /workspace

USER vscode