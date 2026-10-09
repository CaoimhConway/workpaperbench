FROM python:3.12-slim-bookworm@sha256:54c85f3c47607a77f32adec749d3c81d1348bf25833671f512b26a9b6d778cb3
WORKDIR /workspace
RUN apt-get update && apt-get install -y --no-install-recommends bash curl git ca-certificates procps iproute2 libatomic1 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir jsonschema==4.26.0
COPY data.sqlite evidence.json sources.md schema.json output_contract.json starting_regional_attribution.sql starting_worldwide_reconciliation.sql starting_company_margin_bridge.sql /workspace/
