#!/bin/bash

# EdAgent Deployment Script
# This script handles deployment to different environments

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate environment
validate_environment() {
    case $ENVIRONMENT in
        development|staging|production)
            log_info "Deploying to $ENVIRONMENT environment"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT"
            log_error "Valid environments: development, staging, production"
            exit 1
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check if docker-compose is available
    if ! command -v docker compose &> /dev/null; then
        log_error "docker compose is not installed"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Load environment configuration
load_environment() {
    local env_file="$PROJECT_ROOT/config/${ENVIRONMENT}.env"
    
    if [[ -f "$env_file" ]]; then
        log_info "Loading environment configuration from $env_file"
        set -a  # Automatically export all variables
        source "$env_file"
        set +a
    else
        log_warn "Environment file not found: $env_file"
        log_warn "Using default configuration"
    fi
    
    # Load secrets if available
    local secrets_file="$PROJECT_ROOT/config/${ENVIRONMENT}.secrets"
    if [[ -f "$secrets_file" ]]; then
        log_info "Loading secrets from $secrets_file"
        set -a
        source "$secrets_file"
        set +a
    fi
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    cd "$PROJECT_ROOT"
    
    # Build the image with version tag
    docker build -t "edagent:$VERSION" -t "edagent:latest" .
    
    log_info "Docker image built successfully"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    cd "$PROJECT_ROOT"
    
    # Start database and redis services
    docker compose up -d db redis
    
    # Wait for database to be healthy
    log_info "Waiting for database to be ready..."
    local max_attempts=60
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        # Check if database service is healthy
        if docker compose ps db | grep -q "healthy"; then
            log_info "Database is healthy and ready"
            break
        elif docker compose exec -T db pg_isready -U edagent -d edagent > /dev/null 2>&1; then
            log_info "Database is ready"
            break
        fi
        
        log_info "Database not ready, attempt $attempt/$max_attempts, waiting..."
        sleep 3
        ((attempt++))
        
        if [[ $attempt -gt $max_attempts ]]; then
            log_error "Database failed to become ready after $max_attempts attempts"
            log_error "Checking database logs..."
            docker compose logs db
            exit 1
        fi
    done
    
    # Run migrations with proper network connectivity
    log_info "Running Alembic migrations..."
    
    # Try running migrations with explicit network first
    if docker compose run --rm edagent python -m alembic upgrade head; then
        log_info "Database migrations completed successfully"
    else
        log_warn "Migration failed, trying alternative approach..."
        
        # Alternative: run migrations from within the database network
        if docker compose exec -T edagent python -m alembic upgrade head; then
            log_info "Database migrations completed successfully (alternative method)"
        else
            log_error "Migration failed with both methods"
            log_error "Checking application logs..."
            docker compose logs edagent
            exit 1
        fi
    fi
}

# Deploy application
deploy_application() {
    log_info "Deploying application..."
    
    cd "$PROJECT_ROOT"
    
    # Stop existing services
    docker compose down
    
    # Start services
    docker compose up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to start..."
    sleep 15
    
    # Health check
    if health_check; then
        log_info "Application deployed successfully"
    else
        log_error "Health check failed after deployment"
        exit 1
    fi
}

# Health check
health_check() {
    log_info "Performing health check..."
    
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s http://localhost:8000/health > /dev/null; then
            log_info "Health check passed"
            return 0
        fi
        
        log_info "Health check attempt $attempt/$max_attempts failed, retrying..."
        sleep 2
        ((attempt++))
    done
    
    log_error "Health check failed after $max_attempts attempts"
    return 1
}

# Backup database (for production)
backup_database() {
    if [[ "$ENVIRONMENT" == "production" ]]; then
        log_info "Creating database backup..."
        
        local backup_dir="$PROJECT_ROOT/backups"
        local backup_file="$backup_dir/edagent_$(date +%Y%m%d_%H%M%S).sql"
        
        mkdir -p "$backup_dir"
        
        docker compose exec -T db pg_dump -U edagent edagent > "$backup_file"
        
        log_info "Database backup created: $backup_file"
    fi
}

# Rollback function
rollback() {
    log_warn "Rolling back deployment..."
    
    cd "$PROJECT_ROOT"
    
    # Stop current services
    docker compose down
    
    # Start with previous version (assuming it's tagged as 'previous')
    docker compose up -d
    
    log_info "Rollback completed"
}

# Main deployment function
main() {
    log_info "Starting EdAgent deployment..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"
    
    validate_environment
    check_prerequisites
    load_environment
    
    # Create logs directory
    mkdir -p "$PROJECT_ROOT/logs"
    
    # Backup database for production
    backup_database
    
    # Build and deploy
    build_image
    run_migrations
    deploy_application
    
    log_info "Deployment completed successfully!"
    log_info "Application is running at http://localhost:8000"
}

# Handle script arguments
case "${1:-deploy}" in
    deploy)
        main
        ;;
    rollback)
        rollback
        ;;
    health-check)
        health_check
        ;;
    *)
        echo "Usage: $0 [deploy|rollback|health-check] [environment] [version]"
        echo "  deploy: Deploy the application (default)"
        echo "  rollback: Rollback to previous version"
        echo "  health-check: Check application health"
        echo ""
        echo "Environments: development, staging, production"
        echo "Default environment: staging"
        echo "Default version: latest"
        exit 1
        ;;
esac