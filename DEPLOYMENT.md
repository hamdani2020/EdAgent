# EdAgent Deployment Guide

This guide covers the deployment of EdAgent to different environments using Docker and Docker Compose.

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Git
- At least 4GB RAM and 10GB disk space

## Quick Start

### Development Environment

1. Clone the repository and navigate to the project directory
2. Copy environment configuration:
   ```bash
   cp config/development.env .env
   ```
3. Set required environment variables in `.env`:
   ```bash
   GEMINI_API_KEY=your_gemini_api_key
   YOUTUBE_API_KEY=your_youtube_api_key
   SECRET_KEY=your_secret_key
   ```
4. Deploy using the deployment script:
   ```bash
   ./scripts/deploy.sh development
   ```

### Staging Environment

1. Copy staging configuration:
   ```bash
   cp config/staging.env .env
   ```
2. Update environment variables in `.env`
3. Deploy:
   ```bash
   ./scripts/deploy.sh staging
   ```

### Production Environment

1. Copy production configuration:
   ```bash
   cp config/production.env .env
   ```
2. Create secrets file:
   ```bash
   cp config/production.env config/production.secrets
   # Edit config/production.secrets with actual secrets
   ```
3. Deploy:
   ```bash
   ./scripts/deploy.sh production
   ```

## Environment Configuration

### Environment Files

- `config/development.env` - Development settings
- `config/staging.env` - Staging settings  
- `config/production.env` - Production settings

### Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `YOUTUBE_API_KEY` | YouTube Data API key | Yes |
| `SECRET_KEY` | Application secret key | Yes |
| `DATABASE_URL` | Database connection string | No (defaults to SQLite) |
| `REDIS_URL` | Redis connection string | No |
| `ENVIRONMENT` | Environment name (development/staging/production) | No |

### Optional Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `API_HOST` | API server host | 0.0.0.0 |
| `API_PORT` | API server port | 8000 |
| `LOG_LEVEL` | Logging level | INFO |
| `RATE_LIMIT_RPM` | Rate limit requests per minute | 60 |

## Services

### Core Services

- **edagent**: Main application server
- **db**: PostgreSQL database
- **redis**: Redis cache
- **nginx**: Reverse proxy and load balancer

### Monitoring Services (Optional)

- **prometheus**: Metrics collection
- **grafana**: Metrics visualization
- **alertmanager**: Alert management

## Deployment Scripts

### Main Deployment Script

```bash
./scripts/deploy.sh [environment] [version]
```

Options:
- `environment`: development, staging, or production (default: staging)
- `version`: Docker image version (default: latest)

### Database Migration Script

```bash
./scripts/migrate.sh [environment] [command]
```

Commands:
- `upgrade`: Apply latest migrations (default)
- `downgrade`: Rollback migrations
- `current`: Show current version
- `history`: Show migration history
- `revision`: Create new migration

## Docker Compose Files

### Main Application

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d edagent

# View logs
docker-compose logs -f edagent

# Stop services
docker-compose down
```

### With Monitoring

```bash
# Start application with monitoring
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Access monitoring dashboards
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# AlertManager: http://localhost:9093
```

## Health Checks

### Basic Health Check

```bash
curl http://localhost:8000/health
```

### Detailed Health Check

```bash
curl http://localhost:8000/health/detailed
```

### Service-Specific Checks

```bash
# Database
docker-compose exec db pg_isready -U edagent

# Redis
docker-compose exec redis redis-cli ping

# Application logs
docker-compose logs edagent
```

## Monitoring and Logging

### Application Logs

Logs are stored in the `logs/` directory:
- `logs/edagent-{environment}.log` - Application logs
- `logs/nginx/` - Nginx access and error logs

### Metrics

Prometheus metrics are available at:
- Application metrics: `http://localhost:8000/metrics`
- System metrics: `http://localhost:9100/metrics`
- Database metrics: `http://localhost:9187/metrics`

### Grafana Dashboards

Default dashboards are available in `monitoring/grafana/dashboards/`:
- EdAgent Application Dashboard
- System Metrics Dashboard
- Database Performance Dashboard

## Backup and Recovery

### Database Backup

```bash
# Manual backup
docker-compose exec db pg_dump -U edagent edagent > backup.sql

# Automated backup (production deployments)
./scripts/deploy.sh production  # Creates automatic backup
```

### Database Restore

```bash
# Restore from backup
docker-compose exec -T db psql -U edagent edagent < backup.sql
```

## Troubleshooting

### Common Issues

1. **Database connection failed**
   ```bash
   # Check database status
   docker-compose ps db
   docker-compose logs db
   
   # Restart database
   docker-compose restart db
   ```

2. **Application won't start**
   ```bash
   # Check application logs
   docker-compose logs edagent
   
   # Check environment variables
   docker-compose exec edagent env | grep -E "(GEMINI|YOUTUBE|SECRET)"
   ```

3. **High memory usage**
   ```bash
   # Check resource usage
   docker stats
   
   # Restart services
   docker-compose restart
   ```

### Log Analysis

```bash
# View recent logs
docker-compose logs --tail=100 -f edagent

# Search for errors
docker-compose logs edagent | grep ERROR

# Monitor resource usage
docker-compose exec edagent top
```

## Security Considerations

### Production Security

1. **Environment Variables**: Store secrets in separate files, not in version control
2. **Network Security**: Configure firewall rules to restrict access
3. **SSL/TLS**: Enable HTTPS in production (uncomment SSL configuration in nginx.conf)
4. **Database Security**: Use strong passwords and restrict database access
5. **API Keys**: Rotate API keys regularly

### Security Checklist

- [ ] Secrets stored securely (not in git)
- [ ] Strong database passwords
- [ ] HTTPS enabled for production
- [ ] Rate limiting configured
- [ ] Input validation enabled
- [ ] Regular security updates

## Performance Optimization

### Production Tuning

1. **Database**: Adjust connection pool sizes based on load
2. **Redis**: Configure appropriate memory limits
3. **Nginx**: Tune worker processes and connections
4. **Application**: Monitor and adjust rate limits

### Scaling

For high-traffic deployments:
1. Use multiple application instances behind a load balancer
2. Implement database read replicas
3. Use Redis clustering for cache scaling
4. Consider CDN for static assets

## Support

For deployment issues:
1. Check the troubleshooting section above
2. Review application logs
3. Verify environment configuration
4. Check service health endpoints