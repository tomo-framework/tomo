# Configuration Guide

Comprehensive guide to configuring Tomo and TypeScript integration.

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | LLM API key | Yes |
| `TOMO_REST_URL` | REST API endpoint | For REST |
| `TOMO_MCP_URL` | MCP WebSocket URL | For MCP |
| `DEBUG_MODE` | Enable debug logging | No |

## Tomo Server Config

- `--port`: Server port
- `--module`: Tools module
- `--log-level`: Logging level

## TypeScript Config

In `tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "es2020",
    "module": "esnext",
    "strict": true
  }
}
```

## Production Config

- Use HTTPS
- Add rate limiting
- Configure CORS

See [Troubleshooting](./troubleshooting.md) for config issues. 