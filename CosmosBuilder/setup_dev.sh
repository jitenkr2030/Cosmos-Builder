#!/bin/bash

# CosmosBuilder Local Development Setup Script
# This script sets up the complete development environment using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Check if Docker is installed
check_docker() {
    print_header "Checking Docker Installation"
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        echo "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        echo "Visit: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_status "Docker and Docker Compose are installed"
}

# Create necessary directories
create_directories() {
    print_header "Creating Directory Structure"
    
    directories=(
        "logs"
        "uploads"
        "deployments"
        "ssl"
        "monitoring/grafana/dashboards"
        "monitoring/grafana/datasources"
        "scripts"
    )
    
    for dir in "${directories[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            print_status "Created directory: $dir"
        else
            print_status "Directory already exists: $dir"
        fi
    done
}

# Create environment file
create_env_file() {
    print_header "Setting Up Environment Variables"
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# CosmosBuilder Development Environment
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET_KEY=dev-jwt-secret-change-in-production

# Database Configuration
DATABASE_URL=postgresql://cosmosbuilder:cosmosbuilder_dev_password@postgres:5432/cosmosbuilder
POSTGRES_DB=cosmosbuilder
POSTGRES_USER=cosmosbuilder
POSTGRES_PASSWORD=cosmosbuilder_dev_password

# Redis Configuration
REDIS_URL=redis://:redis_dev_password@redis:6379/0

# Message Queue Configuration
CELERY_BROKER_URL=redis://:redis_dev_password@redis:6379/1
CELERY_RESULT_BACKEND=redis://:redis_dev_password@redis:6379/2

# Monitoring Configuration
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_ADMIN_PASSWORD=grafana_dev_password
ELASTICSEARCH_URL=http://elasticsearch:9200

# Email Configuration (Mailhog for development)
SMTP_HOST=mailhog
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=false

# Object Storage (MinIO for development)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_USE_SSL=false

# API Configuration
API_BASE_URL=http://localhost:8000
API_RATE_LIMIT=1000
API_TIMEOUT=30

# Logging
LOG_LEVEL=DEBUG

# Development Settings
DEBUG=True
TESTING=False
EOF
        print_status "Created .env file with default development settings"
        print_warning "Please review and update the .env file for your environment"
    else
        print_status ".env file already exists"
    fi
}

# Start services
start_services() {
    print_header "Starting Services"
    
    print_status "Pulling Docker images..."
    docker-compose pull
    
    print_status "Building application containers..."
    docker-compose build
    
    print_status "Starting services in background..."
    docker-compose up -d
    
    print_status "Waiting for services to be ready..."
    sleep 30
}

# Health check
health_check() {
    print_header "Health Check"
    
    # Check database connection
    if docker-compose exec -T postgres pg_isready -U cosmosbuilder -d cosmosbuilder > /dev/null 2>&1; then
        print_status "✓ PostgreSQL is healthy"
    else
        print_error "✗ PostgreSQL is not ready"
    fi
    
    # Check Redis
    if docker-compose exec -T redis redis-cli -a redis_dev_password ping | grep -q PONG; then
        print_status "✓ Redis is healthy"
    else
        print_error "✗ Redis is not ready"
    fi
    
    # Check API server
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_status "✓ API server is healthy"
    else
        print_warning "⚠ API server might still be starting up"
    fi
    
    # Check frontend
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        print_status "✓ Frontend is healthy"
    else
        print_warning "⚠ Frontend might still be starting up"
    fi
}

# Display service URLs
show_urls() {
    print_header "Service URLs"
    
    echo -e "${GREEN}CosmosBuilder Services:${NC}"
    echo -e "  Frontend Application:        ${BLUE}http://localhost:3000${NC}"
    echo -e "  API Server:                  ${BLUE}http://localhost:8000${NC}"
    echo -e "  API Documentation:           ${BLUE}http://localhost:8000/docs${NC}"
    echo -e ""
    echo -e "${GREEN}Monitoring & Management:${NC}"
    echo -e "  Grafana Dashboard:           ${BLUE}http://localhost:3001${NC}"
    echo -e "  Prometheus:                  ${BLUE}http://localhost:9090${NC}"
    echo -e "  Kibana (Logs):               ${BLUE}http://localhost:5601${NC}"
    echo -e "  Jaeger (Tracing):            ${BLUE}http://localhost:16686${NC}"
    echo -e "  Flower (Task Monitor):       ${BLUE}http://localhost:5555${NC}"
    echo -e ""
    echo -e "${GREEN}Development Tools:${NC}"
    echo -e "  pgAdmin:                     ${BLUE}http://localhost:8080${NC}"
    echo -e "  MailHog (Email):             ${BLUE}http://localhost:8025${NC}"
    echo -e "  MinIO Console:               ${BLUE}http://localhost:9001${NC}"
    echo ""
    echo -e "${YELLOW}Default Credentials:${NC}"
    echo -e "  Grafana: admin / grafana_dev_password"
    echo -e "  pgAdmin: admin@cosmosbuilder.com / pgadmin_dev_password"
    echo -e "  MinIO: minioadmin / minioadmin123"
    echo ""
}

# Show logs
show_logs() {
    print_header "Service Logs"
    echo -e "${YELLOW}To view logs for all services, use:${NC}"
    echo -e "  ${GREEN}docker-compose logs -f${NC}"
    echo ""
    echo -e "${YELLOW}To view logs for specific service:${NC}"
    echo -e "  ${GREEN}docker-compose logs -f api-server${NC}"
    echo -e "  ${GREEN}docker-compose logs -f worker${NC}"
    echo -e "  ${GREEN}docker-compose logs -f frontend${NC}"
    echo ""
}

# Main setup function
main() {
    print_header "CosmosBuilder Development Setup"
    
    check_docker
    create_directories
    create_env_file
    start_services
    
    print_header "Setup Complete"
    health_check
    show_urls
    show_logs
    
    print_status "CosmosBuilder development environment is ready!"
    print_warning "Remember to:"
    echo "  1. Review and update the .env file"
    echo "  2. Change default passwords before production use"
    echo "  3. Monitor service health using the provided URLs"
    echo "  4. Check logs regularly during development"
    echo ""
    print_status "Happy coding! 🚀"
}

# Handle script interruption
trap 'print_error "Setup interrupted. You can run this script again to continue."; exit 1' INT

# Run main function
main "$@"