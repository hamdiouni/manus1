# SLA Violation Prediction Platform - Deployment Guide

This guide covers deployment options for the SLA Violation Prediction and Anomaly Detection platform.

## Quick Start (Local Development)

1. **Prerequisites**
   ```bash
   # Install Docker and Docker Compose
   # Install Git
   ```

2. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd sla-prediction-platform
   cp infra/.env.example infra/.env
   # Edit infra/.env with your configuration
   ```

3. **Deploy Locally**
   ```bash
   ./infra/deploy.sh local
   ```

4. **Access Services**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Grafana: http://localhost:3000 (admin/admin)
   - Prometheus: http://localhost:9090

## Cloud Deployment

### Google Cloud Platform (GCP)

1. **Prerequisites**
   ```bash
   # Install gcloud CLI
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Set Environment Variables**
   ```bash
   export GCP_PROJECT_ID=your-project-id
   ```

3. **Deploy**
   ```bash
   ./infra/deploy.sh gcp
   ```

### Amazon Web Services (AWS)

1. **Prerequisites**
   ```bash
   # Install AWS CLI
   aws configure
   ```

2. **Set Environment Variables**
   ```bash
   export AWS_ACCOUNT_ID=123456789012
   export AWS_REGION=us-east-1
   ```

3. **Deploy**
   ```bash
   ./infra/deploy.sh aws
   ```

### Microsoft Azure

1. **Prerequisites**
   ```bash
   # Install Azure CLI
   az login
   ```

2. **Set Environment Variables**
   ```bash
   export AZURE_LOCATION=eastus
   ```

3. **Deploy**
   ```bash
   ./infra/deploy.sh azure
   ```

## Configuration

### Environment Variables

#### Backend Configuration
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `SECRET_KEY`: JWT secret key
- `TELEGRAM_BOT_TOKEN`: Telegram bot token for alerts
- `TELEGRAM_CHAT_ID`: Telegram chat ID for alerts
- `EMAIL_USER`: SMTP email username
- `EMAIL_PASSWORD`: SMTP email password
- `ALERT_EMAIL`: Email address for alerts

#### Frontend Configuration
- `VITE_API_BASE_URL`: Backend API URL
- `VITE_WS_URL`: WebSocket URL
- `VITE_MAP_DEFAULT_CENTER_LAT`: Default map latitude
- `VITE_MAP_DEFAULT_CENTER_LNG`: Default map longitude

### Alert Configuration

#### Telegram Setup
1. Create a bot with @BotFather
2. Get the bot token
3. Get your chat ID by messaging the bot and visiting:
   `https://api.telegram.org/bot<TOKEN>/getUpdates`

#### Email Setup
1. Use Gmail with App Password or SMTP server
2. Configure EMAIL_USER and EMAIL_PASSWORD

## Monitoring

### Grafana Dashboards
- **SLA Violations Dashboard**: Real-time SLA violation metrics
- **Network Performance**: Latency, throughput, packet loss
- **System Health**: Application and infrastructure metrics
- **ML Model Performance**: Model accuracy and prediction metrics

### Prometheus Metrics
- Application metrics from FastAPI
- Database performance metrics
- System resource utilization
- Custom business metrics

## Scaling

### Horizontal Scaling
- Backend: Increase replica count in Cloud Run/ECS/AKS
- Database: Use read replicas for read-heavy workloads
- Redis: Use Redis Cluster for high availability

### Vertical Scaling
- Increase CPU/memory for compute-intensive ML operations
- Use GPU instances for advanced ML models

## Security

### Production Security Checklist
- [ ] Change default passwords
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up VPC/private networks
- [ ] Enable database encryption
- [ ] Configure backup and disaster recovery
- [ ] Set up monitoring and alerting
- [ ] Regular security updates

### Network Security
- Use private subnets for databases
- Configure security groups/firewall rules
- Enable VPC flow logs
- Use managed SSL certificates

## Backup and Recovery

### Database Backup
- Automated daily backups
- Point-in-time recovery
- Cross-region backup replication

### Model Backup
- Versioned model storage
- Automated model archival
- Model rollback capabilities

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check database connectivity
   docker exec -it sla_postgres psql -U sla_user -d sla_prediction
   ```

2. **WebSocket Connection Issues**
   - Check CORS configuration
   - Verify WebSocket URL in frontend
   - Check firewall/proxy settings

3. **Model Training Issues**
   - Check available disk space
   - Verify data quality
   - Monitor memory usage

### Logs
```bash
# View application logs
docker-compose logs -f backend
docker-compose logs -f frontend

# View specific service logs
docker logs sla_backend
```

## Performance Optimization

### Database Optimization
- Create appropriate indexes
- Use connection pooling
- Optimize query performance
- Regular VACUUM and ANALYZE

### Application Optimization
- Enable caching with Redis
- Use async/await patterns
- Optimize ML model inference
- Implement request rate limiting

## CI/CD Pipeline

The platform includes a GitHub Actions workflow for:
- Automated testing
- Docker image building
- Cloud deployment
- Security scanning

### Setup CI/CD
1. Fork the repository
2. Set up GitHub secrets:
   - `GCP_PROJECT_ID`
   - `GCP_SA_KEY`
   - Other cloud credentials as needed
3. Push to main branch to trigger deployment

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Check monitoring dashboards
4. Create an issue in the repository

## License

This project is licensed under the MIT License.

