# CosmosBuilder Deployment Guide
**Author:** MiniMax Agent  
**Date:** 2025-11-26  
**Version:** 1.0  

## Table of Contents
1. [System Requirements and Prerequisites](#system-requirements-and-prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Database Setup and Configuration](#database-setup-and-configuration)
5. [Environment Variables Configuration](#environment-variables-configuration)
6. [Security Hardening Checklist](#security-hardening-checklist)
7. [Monitoring and Logging Setup](#monitoring-and-logging-setup)
8. [Troubleshooting Common Issues](#troubleshooting-common-issues)
9. [Scaling and Performance Optimization](#scaling-and-performance-optimization)

---

## System Requirements and Prerequisites

### Minimum System Requirements
- **CPU:** 4 cores (8 cores recommended)
- **RAM:** 8GB (16GB recommended)
- **Storage:** 50GB free space (SSD recommended)
- **Network:** 1Gbps internet connection
- **OS:** Ubuntu 20.04+, CentOS 8+, or macOS 10.15+

### Required Software Dependencies
- **Docker:** Version 20.10+
- **Docker Compose:** Version 2.0+
- **Python:** Version 3.9+
- **Node.js:** Version 16+ (for frontend)
- **Git:** Latest version
- **Terraform:** Version 1.0+ (for cloud deployments)

### Cloud Provider Accounts
- **AWS:** IAM user with Administrator privileges
- **GCP:** Service account with Compute Engine and Cloud SQL permissions
- **Azure:** Contributor role with Key Vault access

### External Service Dependencies
- **Database:** PostgreSQL 13+ or MySQL 8+
- **Message Queue:** Redis 6+ or RabbitMQ 3.8+
- **Monitoring:** Prometheus + Grafana stack
- **SSL Certificates:** Let's Encrypt or custom certificates

---

## Local Development Setup

### 1. Repository Setup
```bash
# Clone the repository
git clone https://github.com/your-org/cosmosbuilder.git
cd cosmosbuilder

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

### 3. Database Setup (Local)
```bash
# Using Docker Compose (recommended)
docker-compose up -d postgres redis

# Or manual PostgreSQL setup
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres createuser --createdb cosmosbuilder
sudo -u postgres createdb cosmosbuilder_dev
```

### 4. Initialize Database
```bash
# Run database migrations
python scripts/migrate.py

# Seed initial data
python scripts/seed.py
```

### 5. Start Development Servers
```bash
# Start backend API server
python run_dev.py &

# Start frontend development server
cd frontend && npm run dev

# Access application
# Backend API: http://localhost:8000
# Frontend: http://localhost:3000
# API Documentation: http://localhost:8000/docs
```

---

## Production Deployment

### AWS Deployment

#### Prerequisites
- AWS CLI configured
- Terraform installed
- Domain name with Route53

#### Step 1: Infrastructure Setup
```bash
# Navigate to AWS terraform configuration
cd deployment/aws

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="environment=production"

# Apply configuration
terraform apply -var="environment=production"
```

#### Step 2: Application Deployment
```bash
# Build and push Docker images
docker build -t cosmosbuilder:latest .
docker tag cosmosbuilder:latest YOUR_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/cosmosbuilder:latest
docker push YOUR_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/cosmosbuilder:latest

# Deploy using AWS ECS
aws ecs update-service --cluster cosmosbuilder-cluster --service cosmosbuilder-service --force-new-deployment
```

#### Step 3: SSL Configuration
```bash
# Request SSL certificate
aws acm request-certificate --domain-name api.cosmosbuilder.com --validation-method DNS

# Configure load balancer HTTPS
# Update listener rules for SSL termination
```

### GCP Deployment

#### Prerequisites
- Google Cloud SDK installed
- Terraform configured
- Cloud DNS zone configured

#### Step 1: Infrastructure Setup
```bash
# Navigate to GCP terraform configuration
cd deployment/gcp

# Initialize Terraform
terraform init

# Set project ID
export GOOGLE_PROJECT_ID="your-project-id"

# Plan and apply
terraform plan -var="project_id=${GOOGLE_PROJECT_ID}"
terraform apply -var="project_id=${GOOGLE_PROJECT_ID}"
```

#### Step 2: Build and Deploy
```bash
# Build Docker image
gcloud builds submit --tag gcr.io/${GOOGLE_PROJECT_ID}/cosmosbuilder

# Deploy to Cloud Run
gcloud run deploy cosmosbuilder \
  --image gcr.io/${GOOGLE_PROJECT_ID}/cosmosbuilder \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### Azure Deployment

#### Prerequisites
- Azure CLI installed
- Terraform configured
- Azure DNS zone configured

#### Step 1: Infrastructure Setup
```bash
# Navigate to Azure terraform configuration
cd deployment/azure

# Login to Azure
az login

# Initialize Terraform
terraform init

# Create resource group
az group create --name cosmosbuilder-rg --location eastus

# Deploy infrastructure
terraform plan
terraform apply
```

#### Step 2: Container Deployment
```bash
# Build and push to Azure Container Registry
az acr build --registry yourregistry --image cosmosbuilder:latest .

# Deploy to Azure Container Instances
az container create \
  --resource-group cosmosbuilder-rg \
  --name cosmosbuilder-app \
  --image yourregistry.azurecr.io/cosmosbuilder:latest \
  --ports 8000 \
  --environment-variables \
    FLASK_ENV=production \
    DATABASE_URL=postgresql://...
```

---

## Database Setup and Configuration

### PostgreSQL Setup

#### Production Configuration
```sql
-- Create database and user
CREATE DATABASE cosmosbuilder;
CREATE USER cosmosbuilder_user WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE cosmosbuilder TO cosmosbuilder_user;

-- Create extensions
\c cosmosbuilder;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

#### Performance Tuning
```sql
-- postgresql.conf optimizations
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
```

### Redis Configuration
```bash
# redis.conf optimizations for production
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
appendonly yes
appendfsync everysec
```

### Backup Strategy
```bash
# Automated daily backups
#!/bin/bash
# backup_database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgresql"

# Create backup
pg_dump -h localhost -U cosmosbuilder_user cosmosbuilder > ${BACKUP_DIR}/cosmosbuilder_${DATE}.sql

# Compress and encrypt
gzip ${BACKUP_DIR}/cosmosbuilder_${DATE}.sql
gpg --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 \
    --s2k-digest-algo SHA512 --s2k-count 65536 \
    --symmetric --output ${BACKUP_DIR}/cosmosbuilder_${DATE}.sql.gz.gpg \
    ${BACKUP_DIR}/cosmosbuilder_${DATE}.sql.gz

# Upload to S3
aws s3 cp ${BACKUP_DIR}/cosmosbuilder_${DATE}.sql.gz.gpg \
    s3://cosmosbuilder-backups/database/
```

---

## Environment Variables Configuration

### Required Environment Variables

#### Application Configuration
```bash
# Core application settings
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/cosmosbuilder
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_BASE_URL=https://api.cosmosbuilder.com
API_RATE_LIMIT=1000
API_TIMEOUT=30

# Security Settings
JWT_SECRET_KEY=your-jwt-secret-key
JWT_EXPIRATION_HOURS=24
BCRYPT_LOG_ROUNDS=12
```

#### Cloud Provider Configuration

**AWS:**
```bash
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DEFAULT_REGION=us-west-2
AWS_S3_BUCKET=cosmosbuilder-assets
AWS_LAMBDA_ROLE=cosmosbuilder-lambda-role
```

**GCP:**
```bash
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
GCP_PROJECT_ID=your-project-id
GCP_STORAGE_BUCKET=cosmosbuilder-assets
GCP_PUB_SUB_TOPIC=cosmosbuilder-events
```

**Azure:**
```bash
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_TENANT_ID=your-tenant-id
AZURE_STORAGE_ACCOUNT=cosmosbuilderassets
AZURE_KEY_VAULT=cosmosbuilder-vault
```

#### Monitoring Configuration
```bash
# Prometheus
PROMETHEUS_URL=http://prometheus:9090
PROMETHEUS_SCRAPE_INTERVAL=15s

# Grafana
GRAFANA_URL=http://grafana:3000
GRAFANA_ADMIN_PASSWORD=your-grafana-password

# ELK Stack
ELASTICSEARCH_URL=http://elasticsearch:9200
LOGSTASH_PORT=5044
KIBANA_PORT=5601
```

#### Third-party Integrations
```bash
# Email Service
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your-sendgrid-api-key
SMTP_USE_TLS=true

# Payment Processing
STRIPE_PUBLIC_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Monitoring Services
DATADOG_API_KEY=your-datadog-key
NEW_RELIC_LICENSE_KEY=your-newrelic-key
SENTRY_DSN=https://your-sentry-dsn
```

### Environment Variable Management

#### Using AWS Parameter Store
```bash
# Store sensitive variables
aws ssm put-parameter --name "/cosmosbuilder/database/url" --value "postgresql://..." --type String --overwrite
aws ssm put-parameter --name "/cosmosbuilder/jwt/secret" --value "your-secret" --type SecureString --overwrite

# Retrieve in application
import boto3
ssm = boto3.client('ssm')
response = ssm.get_parameter(Name='/cosmosbuilder/database/url', WithDecryption=True)
DATABASE_URL = response['Parameter']['Value']
```

#### Using Azure Key Vault
```bash
# Store secrets
az keyvault secret set --vault-name cosmosbuilder-vault --name database-url --value "postgresql://..."
az keyvault secret set --vault-name cosmosbuilder-vault --name jwt-secret --value "your-secret"

# Retrieve in application
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://cosmosbuilder-vault.vault.azure.net/", credential=credential)
database_url = client.get_secret("database-url").value
```

---

## Security Hardening Checklist

### Infrastructure Security

#### ✅ Network Security
- [ ] Configure VPC with private subnets
- [ ] Implement security groups with least privilege
- [ ] Enable VPC Flow Logs
- [ ] Use AWS PrivateLink / GCP Private Service Connect / Azure Private Endpoint
- [ ] Configure Web Application Firewall (WAF)
- [ ] Enable DDoS protection

#### ✅ Authentication & Authorization
- [ ] Implement multi-factor authentication (MFA)
- [ ] Use role-based access control (RBAC)
- [ ] Enable IP whitelisting for admin endpoints
- [ ] Implement API key rotation policies
- [ ] Use OAuth 2.0 / OpenID Connect for user authentication

#### ✅ Data Protection
- [ ] Encrypt data at rest (AES-256)
- [ ] Encrypt data in transit (TLS 1.3)
- [ ] Implement database encryption
- [ ] Use encrypted storage volumes
- [ ] Enable automatic backup encryption
- [ ] Implement data classification policies

#### ✅ Application Security
```bash
# Security headers configuration
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

#### ✅ Vulnerability Management
- [ ] Regular security scans (OWASP ZAP, Nessus)
- [ ] Dependency vulnerability scanning
- [ ] Container image scanning
- [ ] Regular penetration testing
- [ ] Security patch management
- [ ] Bug bounty program

#### ✅ Monitoring & Incident Response
- [ ] Implement Security Information and Event Management (SIEM)
- [ ] Configure alerting for security events
- [ ] Enable audit logging
- [ ] Implement incident response plan
- [ ] Regular security training for team
- [ ] Backup and disaster recovery testing

### Application Security Best Practices

#### Code Security
```python
# Input validation example
from marshmallow import Schema, fields, validate

class ChainConfigSchema(Schema):
    chain_name = fields.Str(required=True, validate=validate.Length(min=3, max=50))
    consensus_type = fields.Str(required=True, validate=validate.OneOf(['poa', 'pos']))
    max_validators = fields.Int(required=True, validate=validate.Range(min=1, max=100))
```

#### SQL Injection Prevention
```python
# Use parameterized queries
cursor.execute("SELECT * FROM chains WHERE id = %s", (chain_id,))

# ORM usage
chain = Chain.query.filter_by(id=chain_id).first()
```

#### CSRF Protection
```python
# Flask-WTF CSRF protection
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# Include CSRF token in forms
<form>
    {{ csrf_token() }}
    ...
</form>
```

---

## Monitoring and Logging Setup

### Prometheus Monitoring

#### Prometheus Configuration
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'cosmosbuilder-api'
    static_configs:
      - targets: ['api-server:8000']
    metrics_path: '/metrics'
    
  - job_name: 'cosmosbuilder-worker'
    static_configs:
      - targets: ['worker:8000']
    
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

#### Custom Metrics
```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')
ACTIVE_CHAINS = Gauge('cosmosbuilder_active_chains', 'Number of active blockchain chains')

# Usage in Flask routes
@app.route('/api/chains')
def get_chains():
    REQUEST_COUNT.labels(method='GET', endpoint='/api/chains').inc()
    
    with REQUEST_LATENCY.time():
        chains = get_chains_from_db()
        ACTIVE_CHAINS.set(len(chains))
        return jsonify(chains)
```

### Grafana Dashboards

#### Key Dashboards to Create
1. **Application Performance Dashboard**
   - Request rate, latency, error rates
   - Database connection pool metrics
   - Cache hit rates

2. **Infrastructure Dashboard**
   - CPU, memory, disk usage
   - Network traffic
   - Container health

3. **Business Metrics Dashboard**
   - Active users, chains deployed
   - Revenue metrics
   - Customer satisfaction scores

### ELK Stack Logging

#### Logstash Configuration
```ruby
# logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "cosmosbuilder" {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{DATA:logger} - %{GREEDYDATA:message}" }
    }
    
    date {
      match => [ "timestamp", "ISO8601" ]
    }
    
    if [level] == "ERROR" {
      mutate {
        add_tag => [ "alert" ]
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "cosmosbuilder-%{+YYYY.MM.dd}"
  }
}
```

#### Structured Logging
```python
import structlog
import logging

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# Usage
logger = structlog.get_logger()
logger.info("Chain deployment started", chain_id="chain_123", user_id="user_456")
```

### Alerting Configuration

#### Prometheus Alert Rules
```yaml
# alerts.yml
groups:
  - name: cosmosbuilder_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"
      
      - alert: DatabaseConnectionsHigh
        expr: pg_stat_database_numbackends / pg_settings_max_connections > 0.8
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection pool nearly exhausted"
```

---

## Troubleshooting Common Issues

### Database Connection Issues

#### Problem: "connection refused"
```bash
# Check database status
docker-compose ps postgres
sudo systemctl status postgresql

# Test connection
psql -h localhost -U cosmosbuilder_user -d cosmosbuilder

# Check connection limits
SELECT count(*) FROM pg_stat_activity;
```

#### Problem: "too many connections"
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Terminate long-running queries
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'active' AND query_start < now() - interval '5 minutes';
```

### Application Performance Issues

#### High CPU Usage
```bash
# Check running processes
top -p $(pgrep -f cosmosbuilder)

# Monitor API endpoint performance
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/chains

# Profile Python application
python -m cProfile -o profile.prof run_app.py
```

#### Memory Leaks
```bash
# Monitor memory usage
ps aux | grep cosmosbuilder

# Memory profiling
pip install memory-profiler
python -m memory_profiler run_app.py

# Check for memory leaks in long-running processes
valgrind --tool=memcheck python run_app.py
```

### Cloud Deployment Issues

#### AWS ECS Deployment Failures
```bash
# Check service events
aws ecs describe-services --cluster cosmosbuilder-cluster --services cosmosbuilder-service

# View task definition
aws ecs describe-task-definition --task-definition cosmosbuilder:latest

# Check cloudwatch logs
aws logs describe-log-groups --log-group-name-prefix /ecs/cosmosbuilder
```

#### GCP Cloud Run Issues
```bash
# View deployment logs
gcloud run services describe cosmosbuilder --region us-central1 --format="export"

# Check revision details
gcloud run revisions list --service cosmosbuilder

# View real-time logs
gcloud run logs read cosmosbuilder --limit 50
```

### Network and Security Issues

#### SSL Certificate Problems
```bash
# Check certificate validity
openssl s_client -connect api.cosmosbuilder.com:443 -servername api.cosmosbuilder.com

# Renew Let's Encrypt certificate
certbot renew --dry-run

# Check certificate expiration
echo | openssl s_client -connect api.cosmosbuilder.com:443 2>/dev/null | openssl x509 -noout -dates
```

#### Rate Limiting Issues
```python
# Check rate limiting configuration
@app.route('/api/chains', methods=['GET'])
@limiter.limit("100 per hour")
def get_chains():
    # Implementation
    pass

# Test rate limiting
for i in {1..105}; do
  curl -H "X-Forwarded-For: 192.168.1.$i" http://api.cosmosbuilder.com/api/chains
  sleep 0.1
done
```

---

## Scaling and Performance Optimization

### Horizontal Scaling

#### Auto-scaling Configuration

**AWS Auto Scaling:**
```yaml
# auto-scaling.yml
apiVersion: autoscaling/v1
kind: HorizontalPodAutoscaler
metadata:
  name: cosmosbuilder-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cosmosbuilder-api
  minReplicas: 2
  maxReplicas: 20
  targetCPUUtilizationPercentage: 70
```

**Custom Metrics Scaling:**
```python
from kubernetes import client, config
from kubernetes.client.rest import ApiException

class CustomScaler:
    def __init__(self):
        config.load_incluster_config()
        self.apps_v1 = client.AppsV1Api()
    
    def scale_based_on_queue_length(self):
        queue_length = self.get_queue_length()
        
        if queue_length > 1000:
            self.scale_up()
        elif queue_length < 100:
            self.scale_down()
    
    def scale_up(self):
        # Implementation for scaling up
        pass
```

### Database Optimization

#### Connection Pooling
```python
# SQLAlchemy connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

#### Query Optimization
```sql
-- Add indexes for frequently queried columns
CREATE INDEX idx_chains_user_id ON chains(user_id);
CREATE INDEX idx_chains_status ON chains(status);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);

-- Query performance analysis
EXPLAIN ANALYZE SELECT * FROM chains WHERE user_id = 'user123' AND status = 'active';
```

### Caching Strategy

#### Redis Caching
```python
import redis
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration=300):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = redis_client.get(cache_key)
            if result:
                return json.loads(result)
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            redis_client.setex(cache_key, expiration, json.dumps(result))
            return result
        return wrapper
    return decorator

@cache_result(expiration=600)
def get_chain_statistics(chain_id):
    # Expensive database operation
    return expensive_calculation()
```

#### CDN Configuration
```yaml
# CloudFlare configuration
cache_settings:
  browser_cache_ttl: 14400
  edge_cache_ttl: 14400
  cache_level: "aggressive"
  
security_settings:
  security_level: "medium"
  browser_integrity_check: true
  hotlink_protection: true
```

### Performance Monitoring

#### Application Performance Monitoring
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider

# Configure tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger-agent",
    agent_port=6831,
)

# Custom spans
with tracer.start_as_current_span("deploy_chain") as span:
    span.set_attribute("chain.id", chain_id)
    span.set_attribute("user.id", user_id)
    
    result = deploy_blockchain(chain_id, config)
    
    span.set_attribute("deployment.success", result.success)
    span.set_attribute("deployment.duration", result.duration)
```

### Load Balancing

#### Nginx Configuration
```nginx
# nginx.conf
upstream cosmosbuilder_api {
    least_conn;
    server api-server-1:8000 weight=1 max_fails=3 fail_timeout=30s;
    server api-server-2:8000 weight=1 max_fails=3 fail_timeout=30s;
    server api-server-3:8000 weight=1 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name api.cosmosbuilder.com;
    
    location / {
        proxy_pass http://cosmosbuilder_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 5s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Load balancing
        proxy_next_upstream error timeout invalid_header http_500 http_502 http_503;
        proxy_next_upstream_tries 3;
        proxy_next_upstream_timeout 10s;
    }
}
```

---

## Conclusion

This deployment guide provides comprehensive instructions for deploying CosmosBuilder in various environments. Follow the security checklist and monitoring setup to ensure production-grade deployment. 

For additional support, refer to the troubleshooting section or contact the development team.

**Next Steps:**
1. Complete environment setup using this guide
2. Configure monitoring and alerting
3. Implement security hardening measures
4. Set up backup and disaster recovery procedures
5. Conduct load testing before production deployment

---

**Support Contact:**
- Email: support@cosmosbuilder.com
- Documentation: https://docs.cosmosbuilder.com
- GitHub Issues: https://github.com/your-org/cosmosbuilder/issues