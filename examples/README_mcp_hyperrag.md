# HyperRAG MCP server usage

This example MCP server (`examples/mcp_hyperrag.py`) can run over stdio (local) or
via HTTP (`streamable-http` transport) so que puedas apuntar un cliente MCP a una
URL remota.

## Prerrequisitos
- Un directorio de caché de HyperRAG ya poblado (ej. `caches/esql-esql_docs`).
- `pip install -r requirements.txt` (incluye el paquete `mcp`).
- `my_config.py` con las credenciales de LLM y embeddings.

## Lanzar el servidor

### Opción 1: stdio (local)

```bash
python examples/mcp_hyperrag.py \
  --working-dir caches/esql-esql_docs
```

El proceso queda escuchando por stdio (modo predeterminado de `FastMCP`).

### Opción 2: HTTP remoto (para usarlo vía URL)

Si quieres conectarte desde otra máquina o usar `mcp-remote` apuntando a un
URL, arranca el servidor con transporte `streamable-http` y exponiendo host/port:

```bash
python examples/mcp_hyperrag.py \
  --working-dir caches/esql-esql_docs \
  --transport streamable-http --host 0.0.0.0 --port 8000 --http-path /mcp
```

El endpoint MCP quedará accesible en `http://<tu_host>:8000/mcp` (ajusta el
puerto y la ruta si lo necesitas). Este modo sigue sin tocar Elasticsearch; solo
reutiliza el caché existente.

## Ejemplos de configuración de herramientas

### JSON estilo Claude Desktop (usando HTTP remoto)
```json
{
  "hyperrag": {
    "command": "npx",
    "args": [
      "--yes",
      "mcp-remote",
      "http://<tu_host>:8000/mcp"
    ],
    "timeout": 120000
  }
}
```
Reemplaza `<tu_host>` por la IP o dominio donde expusiste el servidor.

### Depuración local con `npx mcp-remote` (stdio)
Si prefieres stdio local, puedes envolver el comando Python así:
```bash
npx mcp-remote -- python examples/mcp_hyperrag.py --working-dir caches/esql-esql_docs
```
Esto conecta `mcp-remote` al servidor MCP vía stdio en tu máquina.
