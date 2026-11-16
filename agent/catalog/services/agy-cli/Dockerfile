FROM debian:trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl unzip ca-certificates coreutils nodejs npm git jq python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 agy

# 1. Instalar Antigravity CLI (agy) en /opt/agy/bin (fuera de /home/agy para que el volumen data/ no lo tape)
RUN mkdir -p /opt/agy/bin \
    && curl -fsSL https://antigravity.google/cli/install.sh | bash -s -- --dir /opt/agy/bin \
    && ln -sf /opt/agy/bin/agy /usr/local/bin/agy \
    && chmod +x /opt/agy/bin/agy \
    && chown -R agy:agy /opt/agy

ENV PATH="/opt/agy/bin:/usr/local/bin:${PATH}"

# 2. uv + nextdns-mcp en venv aislado con Python 3.14 (módulo puro)
RUN curl -fsSL https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh \
    && UV_PYTHON_INSTALL_DIR=/opt/uv-python uv venv --python 3.14 /opt/nextdns-venv \
    && VIRTUAL_ENV=/opt/nextdns-venv UV_PYTHON_INSTALL_DIR=/opt/uv-python uv pip install \
       "nextdns-mcp @ git+https://github.com/dmeiser/nextdns-mcp.git" \
    && chmod -R a+rX /opt/uv-python /opt/nextdns-venv

# 3. JDownloader MCP (proyec_jdw2) — venv aislado con Python 3.14 (con comando instalable)
# ARG cache-bust: cambiar su valor reconstruye SOLO esta capa en ~2 min
ARG JD_MCP_REF=main
RUN UV_PYTHON_INSTALL_DIR=/opt/uv-python uv venv --python 3.14 /opt/jdownloader-venv \
    && VIRTUAL_ENV=/opt/jdownloader-venv UV_PYTHON_INSTALL_DIR=/opt/uv-python uv pip install \
       "jdownloader-mcp @ git+https://github.com/ydiaz1699/proyec_jdw2.git@main" \
    && chmod -R a+rX /opt/jdownloader-venv

USER agy
WORKDIR /home/agy
ENV HOME="/home/agy"
ENTRYPOINT ["agy"]
