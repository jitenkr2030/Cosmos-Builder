#!/usr/bin/env python3
"""
CosmosBuilder Complete Platform Setup
Production deployment script for the entire CosmosBuilder platform
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

def print_header(title: str):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"🌌 {title}")
    print("="*60)

def print_section(title: str):
    """Print section header"""
    print(f"\n📋 {title}")
    print("-" * 50)

def run_command(command: str, description: str):
    """Run shell command with error handling"""
    print(f"⚙️  {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ {description} - Completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def create_startup_scripts():
    """Create platform startup scripts"""
    print_section("Creating Startup Scripts")
    
    # Main startup script
    startup_script = '''#!/bin/bash
# CosmosBuilder Platform Startup Script

echo "🌌 Starting CosmosBuilder Platform..."

# Set environment variables
export COSMOSBUILDER_HOME=$(pwd)
export PYTHONPATH=$COSMOSBUILDER_HOME:$PYTHONPATH
export FLASK_ENV=production
export COSMOSBUILDER_API_PORT=5000

# Start API server
echo "🚀 Starting API Server..."
cd api-server && python app.py &
API_PID=$!

# Start monitoring services
echo "📊 Starting Monitoring Engine..."
cd ../monitoring && python analytics_engine.py &
MONITORING_PID=$!

# Start security services
echo "🛡️  Starting Security Manager..."
cd ../security && python key_manager.py &
SECURITY_PID=$!

echo "✅ CosmosBuilder Platform is now running!"
echo "📍 API Server: http://localhost:5000"
echo "📊 Monitoring: http://localhost:5001"
echo "🔐 Security: http://localhost:5002"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "echo '🛑 Stopping services...'; kill $API_PID $MONITORING_PID $SECURITY_PID; exit" INT
wait
'''
    
    with open('/workspace/CosmosBuilder/start.sh', 'w') as f:
        f.write(startup_script)
    
    # Make script executable
    os.chmod('/workspace/CosmosBuilder/start.sh', 0o755)
    
    # Windows batch script
    batch_script = '''@echo off
echo 🌌 Starting CosmosBuilder Platform...

set COSMOSBUILDER_HOME=%cd%
set PYTHONPATH=%COSMOSBUILDER_HOME%;%PYTHONPATH%
set FLASK_ENV=production
set COSMOSBUILDER_API_PORT=5000

echo 🚀 Starting API Server...
cd api-server && start python app.py

echo 📊 Starting Monitoring Engine...
cd ..\\monitoring && start python analytics_engine.py

echo 🛡️  Starting Security Manager...
cd ..\\security && start python key_manager.py

echo ✅ CosmosBuilder Platform is now running!
echo 📍 API Server: http://localhost:5000
echo 📊 Monitoring: http://localhost:5001
echo 🔐 Security: http://localhost:5002

pause
'''
    
    with open('/workspace/CosmosBuilder/start.bat', 'w') as f:
        f.write(batch_script)
    
    print("✅ Startup scripts created")

def create_docker_compose():
    """Create Docker Compose configuration"""
    print_section("Creating Docker Compose Configuration")
    
    docker_compose = '''version: '3.8'

services:
  cosmosbuilder-api:
    build: ./api-server
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - PYTHONPATH=/app
    volumes:
      - ./api-server:/app
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  cosmosbuilder-monitor:
    build: ./monitoring
    ports:
      - "5001:5001"
    environment:
      - PYTHONPATH=/app
    volumes:
      - ./monitoring:/app
      - ./data:/app/data
    restart: unless-stopped

  cosmosbuilder-security:
    build: ./security
    ports:
      - "5002:5002"
    environment:
      - PYTHONPATH=/app
    volumes:
      - ./security:/app
      - ./data:/app/data
      - ./security-keys:/app/keys
    restart: unless-stopped

  cosmosbuilder-governance:
    build: ./governance
    ports:
      - "5003:5003"
    environment:
      - PYTHONPATH=/app
    volumes:
      - ./governance:/app
      - ./data:/app/data
    restart: unless-stopped

  cosmosbuilder-compliance:
    build: ./enterprise
    ports:
      - "5004:5004"
    environment:
      - PYTHONPATH=/app
    volumes:
      - ./enterprise:/app
      - ./data:/app/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - cosmosbuilder-api
      - cosmosbuilder-monitor
      - cosmosbuilder-security
    restart: unless-stopped

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped

  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: cosmosbuilder
      POSTGRES_USER: cosmosbuilder
      POSTGRES_PASSWORD: securepassword123
    ports:
      - "5432:5432"
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  redis-data:
  postgres-data:

networks:
  default:
    driver: bridge
'''
    
    with open('/workspace/CosmosBuilder/docker-compose.yml', 'w') as f:
        f.write(docker_compose)
    
    print("✅ Docker Compose configuration created")

def create_requirements_files():
    """Create requirements.txt files for each component"""
    print_section("Creating Requirements Files")
    
    # Main requirements
    main_requirements = '''# CosmosBuilder Core Requirements
Flask==2.3.3
Flask-CORS==4.0.0
Flask-RESTful==0.3.10
Flask-SocketIO==5.3.6
Flask-SQLAlchemy==3.0.5
SQLAlchemy==2.0.23
psycopg2-binary==2.9.9
Redis==5.0.1
celery==5.3.4
requests==2.31.0
websockets==11.0.3
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
fastapi==0.104.1
uvicorn==0.24.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
cryptography==41.0.8
bcrypt==4.1.2
PyJWT==2.8.0
validators==0.22.0
'''
    
    # Security requirements
    security_requirements = '''# CosmosBuilder Security Requirements
cryptography==41.0.8
bcrypt==4.1.2
PyJWT==2.8.0
cryptography-hazmat==0.6.0
cryptography-hazmat-2.0.0
pyotp==2.9.0
qrcode==7.4.2
'''
    
    # API requirements
    api_requirements = '''# CosmosBuilder API Requirements
flask==2.3.3
flask-cors==4.0.0
flask-socketio==5.3.6
flask-restful==0.3.10
flask-sqlalchemy==3.0.5
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
celery==5.3.4
websockets==11.0.3
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
fastapi==0.104.1
uvicorn==0.24.0
'''
    
    # Monitoring requirements
    monitoring_requirements = '''# CosmosBuilder Monitoring Requirements
prometheus-client==0.19.0
grafana-api==1.0.3
elasticsearch==8.11.0
influxdb-client==1.38.0
matplotlib==3.8.2
seaborn==0.13.0
plotly==5.17.0
dash==2.14.1
'''
    
    # Write requirements files
    os.makedirs('/workspace/CosmosBuilder/requirements', exist_ok=True)
    
    with open('/workspace/CosmosBuilder/requirements/main.txt', 'w') as f:
        f.write(main_requirements)
    
    with open('/workspace/CosmosBuilder/requirements/security.txt', 'w') as f:
        f.write(security_requirements)
    
    with open('/workspace/CosmosBuilder/requirements/api.txt', 'w') as f:
        f.write(api_requirements)
    
    with open('/workspace/CosmosBuilder/requirements/monitoring.txt', 'w') as f:
        f.write(monitoring_requirements)
    
    print("✅ Requirements files created")

def create_nginx_config():
    """Create Nginx configuration"""
    print_section("Creating Nginx Configuration")
    
    nginx_conf = '''events {
    worker_connections 1024;
}

http {
    upstream cosmosbuilder_api {
        server cosmosbuilder-api:5000;
    }
    
    upstream cosmosbuilder_monitor {
        server cosmosbuilder-monitor:5001;
    }
    
    upstream cosmosbuilder_security {
        server cosmosbuilder-security:5002;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
    limit_req_zone $binary_remote_addr zone=general:10m rate=200r/m;
    
    # Main application
    server {
        listen 80;
        server_name localhost cosmosbuilder.local;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        
        # API routes
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            proxy_pass http://cosmosbuilder_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS headers
            add_header 'Access-Control-Allow-Origin' '*' always;
            add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
            add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type' always;
        }
        
        # WebSocket support
        location /socket.io/ {
            proxy_pass http://cosmosbuilder_api;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Monitoring dashboard
        location /monitor/ {
            limit_req zone=general burst=50 nodelay;
            proxy_pass http://cosmosbuilder_monitor;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Security dashboard
        location /security/ {
            limit_req zone=general burst=30 nodelay;
            proxy_pass http://cosmosbuilder_security;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
        
        # Static files
        location /static/ {
            root /var/www/cosmsbuilder;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
        
        # Health check
        location /health {
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }
    }
    
    # Monitoring server
    server {
        listen 8080;
        server_name monitoring.cosmosbuilder.local;
        
        location / {
            proxy_pass http://cosmosbuilder_monitor;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
'''
    
    with open('/workspace/CosmosBuilder/nginx.conf', 'w') as f:
        f.write(nginx_conf)
    
    print("✅ Nginx configuration created")

def create_kubernetes_manifests():
    """Create Kubernetes deployment manifests"""
    print_section("Creating Kubernetes Manifests")
    
    # Create k8s directory
    os.makedirs('/workspace/CosmosBuilder/k8s', exist_ok=True)
    
    # API deployment
    api_deployment = '''apiVersion: apps/v1
kind: Deployment
metadata:
  name: cosmosbuilder-api
  namespace: cosmosbuilder
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cosmosbuilder-api
  template:
    metadata:
      labels:
        app: cosmosbuilder-api
    spec:
      containers:
      - name: api
        image: cosmosbuilder/api:latest
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: cosmosbuilder-secrets
              key: database-url
        - name: REDIS_URL
          value: "redis://redis:6379"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: cosmosbuilder-api-service
  namespace: cosmosbuilder
spec:
  selector:
    app: cosmosbuilder-api
  ports:
    - protocol: TCP
      port: 80
      targetPort: 5000
  type: ClusterIP
'''
    
    with open('/workspace/CosmosBuilder/k8s/api-deployment.yaml', 'w') as f:
        f.write(api_deployment)
    
    # ConfigMap
    config_map = '''apiVersion: v1
kind: ConfigMap
metadata:
  name: cosmosbuilder-config
  namespace: cosmosbuilder
data:
  api.conf: |
    LOG_LEVEL=INFO
    API_PORT=5000
    CORS_ORIGINS=*
    MAX_CONTENT_LENGTH=16777216
  
  monitoring.conf: |
    MONITORING_PORT=5001
    METRICS_RETENTION_DAYS=30
    ALERT_THRESHOLDS_ENABLED=true
  
  security.conf: |
    SECURITY_PORT=5002
    HSM_ENABLED=false
    AUDIT_LOG_RETENTION_DAYS=365
    KEY_ROTATION_DAYS=90
'''
    
    with open('/workspace/CosmosBuilder/k8s/configmap.yaml', 'w') as f:
        f.write(config_map)
    
    # Ingress
    ingress = '''apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cosmosbuilder-ingress
  namespace: cosmosbuilder
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/rate-limit: "100"
    nginx.ingress.kubernetes.io/cors-allow-origin: "*"
spec:
  tls:
  - hosts:
    - api.cosmosbuilder.com
    - monitor.cosmosbuilder.com
    - security.cosmosbuilder.com
    secretName: cosmosbuilder-tls
  rules:
  - host: api.cosmosbuilder.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: cosmosbuilder-api-service
            port:
              number: 80
  - host: monitor.cosmosbuilder.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: cosmosbuilder-monitor-service
            port:
              number: 80
  - host: security.cosmosbuilder.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: cosmosbuilder-security-service
            port:
              number: 80
'''
    
    with open('/workspace/CosmosBuilder/k8s/ingress.yaml', 'w') as f:
        f.write(ingress)
    
    print("✅ Kubernetes manifests created")

def create_environment_files():
    """Create environment configuration files"""
    print_section("Creating Environment Configuration")
    
    # Production environment
    prod_env = '''# CosmosBuilder Production Environment
FLASK_ENV=production
DATABASE_URL=postgresql://cosmosbuilder:securepassword123@postgres:5432/cosmosbuilder
REDIS_URL=redis://redis:6379
SECRET_KEY=your-super-secret-key-here-change-in-production
JWT_SECRET_KEY=jwt-secret-key-change-in-production
API_PORT=5000
MONITORING_PORT=5001
SECURITY_PORT=5002

# Security Settings
HSM_ENABLED=false
AUDIT_LOG_RETENTION_DAYS=365
KEY_ROTATION_DAYS=90
ENCRYPTION_ALGORITHM=AES-256

# Monitoring Settings
METRICS_RETENTION_DAYS=30
ALERT_THRESHOLDS_ENABLED=true
PERFORMANCE_MONITORING=true

# Compliance Settings
KYC_PROVIDER=internal
COMPLIANCE_LEVEL=standard
AUDIT_TRAIL_ENABLED=true

# API Limits
API_RATE_LIMIT=1000
API_RATE_WINDOW=3600
MAX_REQUEST_SIZE=16777216
'''
    
    with open('/workspace/CosmosBuilder/.env.production', 'w') as f:
        f.write(prod_env)
    
    # Development environment
    dev_env = '''# CosmosBuilder Development Environment
FLASK_ENV=development
DEBUG=true
DATABASE_URL=sqlite:///data/cosmosbuilder_dev.db
SECRET_KEY=dev-secret-key-not-for-production
API_PORT=5000
MONITORING_PORT=5001
SECURITY_PORT=5002

# Security Settings (Relaxed for development)
HSM_ENABLED=false
AUDIT_LOG_RETENTION_DAYS=7
KEY_ROTATION_DAYS=30
ENCRYPTION_ALGORITHM=AES-128

# Monitoring Settings
METRICS_RETENTION_DAYS=7
ALERT_THRESHOLDS_ENABLED=false
PERFORMANCE_MONITORING=true

# Development Tools
API_DOCS_ENABLED=true
DEBUG_TOOLBAR_ENABLED=true
'''
    
    with open('/workspace/CosmosBuilder/.env.development', 'w') as f:
        f.write(dev_env)
    
    print("✅ Environment files created")

def create_monitoring_dashboard():
    """Create monitoring dashboard configuration"""
    print_section("Creating Monitoring Dashboard")
    
    # Grafana dashboard JSON
    grafana_dashboard = {
        "dashboard": {
            "id": None,
            "title": "CosmosBuilder Platform",
            "tags": ["cosmosbuilder", "blockchain", "monitoring"],
            "timezone": "UTC",
            "refresh": "5s",
            "time": {
                "from": "now-1h",
                "to": "now"
            },
            "panels": [
                {
                    "id": 1,
                    "title": "API Response Time",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "avg(http_request_duration_seconds) * 1000",
                            "legendFormat": "Response Time (ms)"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                },
                {
                    "id": 2,
                    "title": "Requests per Second",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "rate(http_requests_total[1m])",
                            "legendFormat": "{{method}} {{endpoint}}"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                },
                {
                    "id": 3,
                    "title": "Active Chains",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "cosmosbuilder_active_chains",
                            "legendFormat": "Active Chains"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                },
                {
                    "id": 4,
                    "title": "Security Events",
                    "type": "graph",
                    "targets": [
                        {
                            "expr": "rate(security_events_total[1m])",
                            "legendFormat": "{{event_type}}"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                }
            ]
        }
    }
    
    os.makedirs('/workspace/CosmosBuilder/monitoring/grafana', exist_ok=True)
    with open('/workspace/CosmosBuilder/monitoring/grafana/dashboard.json', 'w') as f:
        json.dump(grafana_dashboard, f, indent=2)
    
    print("✅ Monitoring dashboard created")

def create_ssl_certificates():
    """Create self-signed SSL certificates for development"""
    print_section("Creating SSL Certificates")
    
    # Create SSL directory
    os.makedirs('/workspace/CosmosBuilder/ssl', exist_ok=True)
    
    # Generate self-signed certificate
    cert_script = '''#!/bin/bash
# Generate self-signed SSL certificates for development

echo "🔒 Generating SSL certificates..."

# Generate private key
openssl genrsa -out ca.key 2048

# Generate certificate
openssl req -new -x509 -key ca.key -out ca.crt -days 365 -subj "/C=US/ST=Dev/L=Dev/O=CosmosBuilder/OU=Development/CN=localhost"

echo "✅ SSL certificates generated in ./ssl/"
echo "📝 Note: These are self-signed certificates for development only!"
echo "🔐 Use proper certificates from a CA for production environments"
'''
    
    with open('/workspace/CosmosBuilder/generate-ssl.sh', 'w') as f:
        f.write(cert_script)
    
    os.chmod('/workspace/CosmosBuilder/generate-ssl.sh', 0o755)
    
    print("✅ SSL certificate generation script created")

def create_test_suite():
    """Create test suite for the platform"""
    print_section("Creating Test Suite")
    
    # Create tests directory
    os.makedirs('/workspace/CosmosBuilder/tests', exist_ok=True)
    
    # API tests
    api_tests = '''import unittest
import requests
import json
import time
from app import app

class CosmosBuilderAPITest(unittest.TestCase):
    """API test suite"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = app.test_client()
        self.app.testing = True
        
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        
    def test_chain_creation(self):
        """Test chain creation endpoint"""
        chain_data = {
            'chain_name': 'TestChain',
            'chain_id': 'test-1',
            'symbol': 'TEST',
            'denomination': 'utest'
        }
        
        response = self.app.post('/api/v1/chains',
                               json=chain_data,
                               content_type='application/json')
        self.assertEqual(response.status_code, 201)
        
    def test_invalid_chain_config(self):
        """Test invalid chain configuration"""
        invalid_data = {'chain_name': ''}  # Missing required fields
        
        response = self.app.post('/api/v1/chains',
                               json=invalid_data,
                               content_type='application/json')
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
'''
    
    with open('/workspace/CosmosBuilder/tests/test_api.py', 'w') as f:
        f.write(api_tests)
    
    # Security tests
    security_tests = '''import unittest
from security.key_manager import KeyManager

class KeyManagerTest(unittest.TestCase):
    """Key management test suite"""
    
    def setUp(self):
        """Set up test environment"""
        self.key_manager = KeyManager('test_keys')
        
    def test_generate_key_pair(self):
        """Test key pair generation"""
        key = self.key_manager.generate_key_pair('testnet-1', 'validator')
        self.assertIsNotNone(key.key_id)
        self.assertEqual(key.chain_id, 'testnet-1')
        self.assertEqual(key.key_type, 'validator')
        
    def test_key_encryption(self):
        """Test key encryption/decryption"""
        key = self.key_manager.generate_key_pair('testnet-1', 'validator')
        
        # Test signing
        test_data = b"test message"
        signature = self.key_manager.sign_transaction(key.key_id, test_data)
        self.assertIsNotNone(signature)

if __name__ == '__main__':
    unittest.main()
'''
    
    with open('/workspace/CosmosBuilder/tests/test_security.py', 'w') as f:
        f.write(security_tests)
    
    print("✅ Test suite created")

def main():
    """Main setup function"""
    print_header("CosmosBuilder Complete Platform Setup")
    
    print("🌟 This script will set up the complete CosmosBuilder platform for production deployment.")
    
    # Change to workspace directory
    os.chdir('/workspace/CosmosBuilder')
    
    # Create necessary directories
    directories = [
        'data', 'logs', 'keys', 'backups', 'generated_chains', 'deployments',
        'certificates', 'scripts'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    # Run setup steps
    create_startup_scripts()
    create_docker_compose()
    create_requirements_files()
    create_nginx_config()
    create_kubernetes_manifests()
    create_environment_files()
    create_monitoring_dashboard()
    create_ssl_certificates()
    create_test_suite()
    
    print_section("Final Setup")
    
    # Run final commands
    run_command("chmod +x *.sh", "Making scripts executable")
    run_command("python -m pip install -r requirements/main.txt", "Installing Python dependencies")
    
    print_header("Setup Complete!")
    
    print("""
🎉 CosmosBuilder Platform is now ready for deployment!

📁 Next Steps:

1. 🌐 Configure your domain and DNS settings
2. 🔒 Generate production SSL certificates
3. 🗄️  Set up production database
4. 🔐 Configure security settings and keys
5. 🚀 Deploy using Docker Compose or Kubernetes

📋 Available Commands:

   ./start.sh           - Start the platform locally
   docker-compose up    - Start with Docker Compose
   kubectl apply -f k8s/ - Deploy to Kubernetes
   
📍 Important URLs:

   http://localhost:5000 - API Server
   http://localhost:5001 - Monitoring Dashboard
   http://localhost:5002 - Security Dashboard
   
📚 Documentation:

   See IMPLEMENTATION_SUMMARY.md for complete feature overview
   Check docs/README.md for detailed usage instructions
   
🔒 Security Notes:

   - Change all default passwords and secrets
   - Enable HSM integration for production
   - Configure proper SSL certificates
   - Set up backup and monitoring

🚀 Ready to build the future of blockchain technology!
    """)

if __name__ == "__main__":
    main()