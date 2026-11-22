# Sentry Setup Guide

Sentry is an error tracking and performance monitoring platform that helps you:
- Track errors and exceptions in real-time
- Monitor application performance
- Receive alerts when critical errors occur
- Analyze error trends and patterns

## Quick Setup

### 1. Create a Sentry Account

1. Go to [sentry.io](https://sentry.io)
2. Sign up for a free account
3. Create a new organization
4. Create a new project for Django
5. Select "Django" as the platform

### 2. Get Your DSN

1. After creating the project, copy the DSN (Data Source Name)
2. It looks like: `https://xxxxx@sentry.io/xxxxx`

### 3. Add Environment Variable

Add to your `.env` file:

```env
SENTRY_DSN=https://your-sentry-dsn-here@sentry.io/project-id
ENVIRONMENT=production
```

### 4. Install Dependencies

```bash
pip install sentry-sdk
```

This is already in `requirements.txt`.

### 5. Test Sentry Integration

Once deployed, test Sentry with:

```bash
curl https://your-app.onrender.com/monitoring/sentry-test/ -X POST
```

You should see a test event in your Sentry dashboard within seconds.

## Configuration Details

### Sentry Settings in Django

The app automatically configures Sentry when:
- `SENTRY_DSN` environment variable is set
- Application is in production mode (`DEBUG=False`)

Configuration:
- **Sample Rate**: 10% of transactions are captured (trace_sample_rate=0.1)
- **Integrations**: Django, Redis, Logging
- **Ignored Errors**: 404s and validation errors (less critical)

### Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SENTRY_DSN` | Sentry project DSN | `https://xxxxx@sentry.io/xxxxx` |
| `ENVIRONMENT` | Application environment | `production`, `staging`, `development` |

## Monitoring Endpoints

### Status Check

```bash
GET /monitoring/status/
```

Shows monitoring configuration status.

**Response:**
```json
{
  "monitoring": {
    "sentry": {
      "enabled": true,
      "environment": "production",
      "dsn": "https://xxxxx***"
    },
    "logging": {
      "enabled": true,
      "level": "INFO"
    }
  }
}
```

### Test Sentry

```bash
POST /monitoring/sentry-test/
```

Sends a test exception to Sentry. Useful for verification after deployment.

## Using Sentry in Code

### Capturing Exceptions

```python
from config.monitoring import capture_exception

try:
    # Your code here
    result = perform_operation()
except Exception as e:
    capture_exception(
        e,
        level='error',
        tags={'operation': 'perform_operation', 'user': user.id},
        extra={'details': 'Additional context'}
    )
```

### Capturing Messages

```python
from config.monitoring import capture_message

capture_message(
    'Operation completed successfully',
    level='info',
    tags={'operation': 'complete'},
    extra={'duration': '1.5s'}
)
```

### Using Context Manager

```python
from config.monitoring import MonitoringContextManager

with MonitoringContextManager(
    'expensive_operation',
    tags={'user': user.id},
    extra={'operation_type': 'matching'}
):
    # Your code here
    result = expensive_operation()
    # If exception occurs, it's automatically captured
```

## Sentry Dashboard Features

### Issues

- Real-time exception tracking
- Grouped by error type
- Stack traces with source code
- Affected users and browsers
- Release information

### Performance

- Slow transaction tracking
- Database query performance
- API endpoint latency
- Error rate trends

### Alerts

- Critical error notifications
- Performance regression alerts
- Spike detection (unusual increases)
- Custom alert rules

## Best Practices

1. **Set Environment Variables**
   - Use different DSNs for staging and production
   - Set `ENVIRONMENT` variable appropriately

2. **Use Tags**
   - Add user ID, operation type, etc. to events
   - Helps with filtering and grouping

3. **Add Context**
   - Include relevant extra data
   - Helps with debugging

4. **Review Regularly**
   - Check Sentry dashboard weekly
   - Prioritize and fix high-impact errors
   - Track error trends

5. **Set Up Alerts**
   - Configure email/Slack notifications
   - Respond quickly to critical errors

## Troubleshooting

### Sentry Events Not Appearing

1. Check SENTRY_DSN is set correctly
2. Ensure `DEBUG=False` in production
3. Verify the DSN in Sentry dashboard project settings
4. Test with `/monitoring/sentry-test/` endpoint

### Too Many Events

- Adjust `traces_sample_rate` to lower value (0.05 for 5%)
- Add more errors to `ignore_errors` list
- Use Sentry's inbound data filter

### Performance Impact

- Sentry has minimal performance impact (async)
- If needed, reduce sample rate
- Use `IGNORE_EXCEPTIONS` in cache configuration to prevent cache errors from being sent

## Related Documentation

- [Sentry Django Documentation](https://docs.sentry.io/platforms/python/integrations/django/)
- [Sentry Performance Monitoring](https://docs.sentry.io/platforms/python/performance/)
- [Error Handling Guide](./ERROR_HANDLING.md)
- [Monitoring Guide](./MONITORING.md)
