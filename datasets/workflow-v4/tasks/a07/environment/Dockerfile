FROM python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3
WORKDIR /workspace
RUN apt-get update && apt-get install -y --no-install-recommends bash curl git ca-certificates procps iproute2 libatomic1 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir jsonschema==4.26.0
COPY data.sqlite evidence.json sources.md schema.json output_contract.json starting_gross_profit_bases.sql starting_current_h20_bridge.sql starting_cash_generation.sql /workspace/
