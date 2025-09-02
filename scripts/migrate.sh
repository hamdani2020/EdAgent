#!/bin/bash

# Database Migration Script for EdAgent
# This script handles database migrations for different environments

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT=${1:-development}
COMMAND=${2:-upgrade}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load environment configuration
load_environment() {
    local env_file="$PROJECT_ROOT/config/${ENVIRONMENT}.env"
    
    if [[ -f "$env_file" ]]; then
        log_info "Loading environment configuration from $env_file"
        set -a
        source "$env_file"
        set +a
    else
        log_warn "Environment file not found: $env_file"
    fi
    
    # Load .env file as fallback
    if [[ -f "$PROJECT_ROOT/.env" ]]; then
        set -a
        source "$PROJECT_ROOT/.env"
        set +a
    fi
}

# Check database connection
check_database() {
    log_info "Checking database connection..."
    
    cd "$PROJECT_ROOT"
    
    if python -c "
from edagent.database.connection import get_database_engine
try:
    engine = get_database_engine()
    with engine.connect() as conn:
        conn.execute('SELECT 1')
    print('Database connection successful')
except Exception as e:
    print(f'Database connection failed: {e}')
    exit(1)
"; then
        log_info "Database connection verified"
    else
        log_error "Database connection failed"
        exit 1
    fi
}

# Run migrations
run_migrations() {
    log_info "Running database migrations..."
    
    cd "$PROJECT_ROOT"
    
    case $COMMAND in
        upgrade)
            log_info "Upgrading database to latest version..."
            python -m alembic upgrade head
            ;;
        downgrade)
            local target=${3:-"-1"}
            log_info "Downgrading database to $target..."
            python -m alembic downgrade "$target"
            ;;
        current)
            log_info "Showing current database version..."
            python -m alembic current
            ;;
        history)
            log_info "Showing migration history..."
            python -m alembic history
            ;;
        revision)
            local message=${3:-"Auto-generated migration"}
            log_info "Creating new migration: $message"
            python -m alembic revision --autogenerate -m "$message"
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
    
    log_info "Migration command completed successfully"
}

# Show usage information
show_usage() {
    echo "Usage: $0 [environment] [command] [options]"
    echo ""
    echo "Environments:"
    echo "  development  - Local development database"
    echo "  staging      - Staging environment database"
    echo "  production   - Production database"
    echo ""
    echo "Commands:"
    echo "  upgrade      - Upgrade to latest migration (default)"
    echo "  downgrade    - Downgrade database [target]"
    echo "  current      - Show current migration version"
    echo "  history      - Show migration history"
    echo "  revision     - Create new migration [message]"
    echo ""
    echo "Examples:"
    echo "  $0 development upgrade"
    echo "  $0 staging current"
    echo "  $0 production revision 'Add user preferences table'"
    echo "  $0 development downgrade -1"
}

# Main function
main() {
    log_info "Starting database migration..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Command: $COMMAND"
    
    load_environment
    check_database
    run_migrations
    
    log_info "Database migration completed successfully!"
}

# Handle script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-}" in
        -h|--help|help)
            show_usage
            exit 0
            ;;
        *)
            main "$@"
            ;;
    esac
fi