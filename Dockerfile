FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.6 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# 依存関係を先にインストールしてビルドキャッシュを活用する
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# アプリ本体を追加する
COPY README.md ./
COPY src ./src
COPY eval ./eval
RUN uv sync --locked --no-dev

EXPOSE 8501

CMD ["uv", "run", "streamlit", "run", "src/dx_sol_suggest/main.py", "--server.address=0.0.0.0", "--server.port=8501"]