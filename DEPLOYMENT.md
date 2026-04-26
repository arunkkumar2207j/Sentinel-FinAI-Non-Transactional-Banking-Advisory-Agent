# Deployment Guide for Sentinel-FinAI

This guide covers deploying the Sentinel-FinAI Non-Transactional Banking Advisory Agent using Docker.

## Prerequisites

- Docker Engine 20.10+ or Docker Desktop
- Docker Compose 2.0+
- OpenAI API Key

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Sentinel-FinAI-Non-Transactional-Banking-Advisory-Agent
```

### 2. Configure Environment Variables

Copy the example environment file and add your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env` and set your `OPENAI_API_KEY`:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### 3. Build and Run with Docker Compose

```bash
docker-compose up -d --build
```

This will:

- Build the Docker image
- Start the Sentinel-FinAI container
- Expose the application on port 8501
- Mount persistent volumes for data and logs

### 4. Access the Application

Open your browser and navigate to:

- **Local:** http://localhost:8501
- **Remote:** http://your-server-ip:8501

### 5. Monitor Logs

```bash
# View application logs
docker-compose logs -f sentinel-finai

# View logs from the host
 tail -f backend/logs/sentinel_ops.log
```

## Docker Commands

### Build the Image

```bash
docker build -t sentinel-finai .
```

### Run the Container

```bash
docker run -d \
  --name sentinel-finai \
  -p 8501:8501 \
  --env-file .env \
  -v ./backend/data:/app/backend/data \
  -v ./backend/logs:/app/backend/logs \
  sentinel-finai
```

### Stop the Container

```bash
docker-compose down
```

### Remove Containers and Volumes

```bash
docker-compose down -v
```

### Rebuild the Image

```bash
docker-compose up -d --build --force-recreate
```

## Production Deployment

### Using Nginx as Reverse Proxy

For production deployments, it's recommended to use Nginx as a reverse proxy:

1. Uncomment the nginx service in `docker-compose.yml`
2. Create an `nginx.conf` file with your configuration
3. Rebuild and restart:

```bash
docker-compose up -d --build
```

### Using HTTPS with Let's Encrypt

You can add Certbot to secure your deployment:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://sentinel-finai:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Health Checks

The container includes a health check that monitors the application:

```bash
# Check container health status
docker inspect --format='{{.State.Health.Status}}' sentinel-finai

# Manual health check
curl -f http://localhost:8501/health
```

## Persistent Data

The following directories are mounted as volumes:

- `./backend/data` - ChromaDB vector database and persistent data
- `./backend/logs` - Application logs

**Important:** Ensure these directories are backed up regularly.

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs sentinel-finai

# Check if port 8501 is already in use
lsof -i :8501
```

### OpenAI API Key Issues

```bash
# Verify environment variable is set
docker-compose exec sentinel-finai env | grep OPENAI_API_KEY

# Check application logs for authentication errors
docker-compose logs sentinel-finai | grep -i "api\|auth\|key"
```

### Memory Issues

If you encounter memory issues with ChromaDB:

```bash
# Increase Docker memory limit
# Docker Desktop: Settings -> Resources -> Memory (set to 4GB+)
```

### Rebuild After Code Changes

```bash
docker-compose up -d --build --force-recreate
```

## Monitoring

### Resource Usage

```bash
# Monitor container resource usage
docker stats sentinel-finai
```

### Application Logs

```bash
# Follow logs in real-time
docker-compose logs -f sentinel-finai

# View specific log files
tail -f backend/logs/sentinel_ops.log
```

## Security Best Practices

1. **Never commit `.env` file** - Add it to `.gitignore`
2. **Use secrets management** - For production, use Docker secrets or a vault
3. **Keep images updated** - Regularly rebuild with latest base images
4. **Use non-root user** - The Dockerfile uses `appuser` for security
5. **Limit resource usage** - Set memory and CPU limits in production
6. **Enable HTTPS** - Always use TLS in production environments

## Scaling

For horizontal scaling, consider:

1. Using a load balancer (Nginx, HAProxy)
2. Running multiple containers with different ports
3. Using Docker Swarm or Kubernetes for orchestration
4. Implementing session management for stateful operations

## Backup and Recovery

### Backup Data

```bash
# Backup ChromaDB
tar -czf chroma-backup-$(date +%Y%m%d).tar.gz backend/data/chroma_db/

# Backup logs
tar -czf logs-backup-$(date +%Y%m%d).tar.gz backend/logs/
```

### Restore Data

```bash
# Restore ChromaDB
tar -xzf chroma-backup-YYYYMMDD.tar.gz -C backend/data/
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy Sentinel-FinAI

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Build and Push Docker Image
        run: |
          docker build -t sentinel-finai .
          docker tag sentinel-finai your-registry/sentinel-finai:latest
          docker push your-registry/sentinel-finai:latest

      - name: Deploy to Server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/sentinel-finai
            docker-compose pull
            docker-compose up -d
```

## Support

For issues or questions:

- Check the [documentation](./docs/README.md)
- Review application logs
- Verify environment configuration
