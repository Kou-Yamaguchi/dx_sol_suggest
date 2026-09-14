FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.6 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PORT=8501

WORKDIR /app

# 依存関係を先にインストールしてビルドキャッシュを活用する
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# アプリ本体を追加する
COPY src ./src

RUN uv sync --locked --no-dev

ENV UV_NO_SYNC=1

EXPOSE ${PORT}

CMD ["sh", "-c", "exec uv run streamlit run src/dx_sol_suggest/main.py --server.address=0.0.0.0 --server.port=${PORT} --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false --server.fileWatcherType=none --browser.gatherUsageStats=false"]
