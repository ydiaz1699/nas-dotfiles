FROM debian:trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl unzip ca-certificates coreutils nodejs npm git jq \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 kiro

# 1. Instalar Kiro CLI en /opt/kiro (FUERA de /home/kiro, para que el volumen ./data no lo tape)
RUN HOME=/tmp/ki bash -c 'curl -fsSL https://cli.kiro.dev/install | bash' \
    && mkdir -p /opt/kiro \
    && cp -a /tmp/ki/.local/bin/. /opt/kiro/ \
    && rm -rf /tmp/ki \
    && chown -R kiro:kiro /opt/kiro

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

USER kiro
WORKDIR /home/kiro
ENV PATH="/opt/kiro:${PATH}"
ENTRYPOINT ["/opt/kiro/kiro-cli"]
