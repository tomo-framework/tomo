# Troubleshooting Guide

Common issues and solutions for Tomo-TypeScript integration.

## Connection Issues

### Problem: Connection Refused
**Solution**:
1. Check if Tomo server is running
2. Verify port in URL
3. Check firewall settings

### Problem: WebSocket Disconnects
**Solution**:
- Implement reconnect logic
- Check network stability
- Increase timeout settings

## Tool Execution Errors

### Problem: Tool Not Found
**Solution**:
- Verify module loading with --module
- Check tool registration
- Restart server

### Problem: Input Validation Failed
**Solution**:
- Check input schema
- Validate JSON format
- Use TypeScript types

## Performance Issues

### Problem: High Latency
**Solution**:
- Use subprocess for local dev
- Optimize network
- Cache schemas

## Deployment Issues

### Problem: Vercel Cold Starts
**Solution**:
- Use persistent services
- Warm up endpoints
- Optimize bundle size

## Debug Tips

- Enable verbose logging
- Use browser dev tools
- Test with Postman/WS clients

If issues persist, check GitHub issues or open a new one. 