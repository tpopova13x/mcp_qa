FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir mcp[cli]==1.27.0 chromadb==1.5.7 psycopg2-binary==2.9.11
COPY app/mcp_server/server.py .
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; req = urllib.request.Request('http://localhost:8080/mcp', method='POST', headers={'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}, data=b'{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-03-26\",\"capabilities\":{},\"clientInfo\":{\"name\":\"healthcheck\",\"version\":\"0.1.0\"}}}'); urllib.request.urlopen(req)" || exit 1
CMD ["python", "server.py"]
