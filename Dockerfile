FROM python:3.11-slim

# Install the project into `/opt`
WORKDIR /app

# Instalar dependências para locale
RUN apt-get update && apt-get install -y --no-install-recommends \
    locales \
 && rm -rf /var/lib/apt/lists/*

# Gerar o locale pt_BR.UTF-8
RUN sed -i '/pt_BR.UTF-8/s/^# //g' /etc/locale.gen && \
    locale-gen pt_BR.UTF-8

# Definir como padrão
ENV LANG=pt_BR.UTF-8
ENV LANGUAGE=pt_BR:pt
ENV LC_ALL=pt_BR.UTF-8

# Install uv.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency definition files into the container.
COPY pyproject.toml uv.lock ./

# Instalar dependências no /opt/venv
RUN uv sync --locked --no-install-project

COPY . .

RUN uv sync  --locked

# Reset the entrypoint, don't invoke `uv`
ENTRYPOINT []
