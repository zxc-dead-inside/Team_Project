FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    postgresql postgresql-client \
    sqlite3 \
    gettext \
    make \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

ARG USERNAME=vscode
ARG USER_UID=1000
ARG USER_GID=$USER_UID

RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

RUN echo 'PS1="\\[\\033[0;32m\\]vscode\\[\\033[0m\\] ➜ \\[\\033[0;34m\\]\\w\\[\\033[0m\\] (\\[\\033[0;31m\\]\\$(git branch --show-current 2>/dev/null || echo \"No Branch\")\\[\\033[0m\\] ✗) $ "' >> /home/vscode/.bashrc

USER $USERNAME