FROM mcr.microsoft.com/devcontainers/python:3.11-bullseye

# Install system packages and Node.js for Claude Code
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    sudo \
    ca-certificates \
    gnupg \
    lsb-release \
    zsh \
    build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install uv for Python package management
RUN mkdir -p /home/vscode/.local/bin && \
    chown -R vscode:vscode /home/vscode/.local && \
    echo 'export PATH="/home/vscode/.local/bin:$PATH"' >> /home/vscode/.bashrc

USER vscode
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
USER root

# Install git-delta for better diff display
RUN ARCH=$(dpkg --print-architecture) && \
    wget "https://github.com/dandavison/delta/releases/download/0.18.2/git-delta_0.18.2_${ARCH}.deb" && \
    dpkg -i "git-delta_0.18.2_${ARCH}.deb" && \
    rm "git-delta_0.18.2_${ARCH}.deb"

# Set up command history persistence
ARG USERNAME=vscode
RUN SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history" \
    && mkdir /commandhistory \
    && touch /commandhistory/.bash_history \
    && chown -R $USERNAME /commandhistory

# Create directories
RUN mkdir -p /workspace /home/$USERNAME/.claude && \
    chown -R $USERNAME:$USERNAME /workspace /home/$USERNAME/.claude

WORKDIR /workspace
USER $USERNAME

# Set up git configuration (without Claude Code for now)
RUN git config --global core.pager "delta" && \
    git config --global interactive.diffFilter "delta --color-only" && \
    git config --global delta.navigate true && \
    git config --global delta.light false

# Set up helpful aliases
RUN echo 'alias cc="claude"' >> ~/.bashrc && \
    echo 'alias strands-run="uv run python main.py"' >> ~/.bashrc && \
    echo 'alias strands-test="uv run --frozen pytest"' >> ~/.bashrc && \
    echo 'alias lint="uv run ruff check"' >> ~/.bashrc && \
    echo 'alias format="uv run ruff format"' >> ~/.bashrc && \
    echo 'alias typecheck="uv run pyright"' >> ~/.bashrc
