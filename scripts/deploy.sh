#!/bin/bash
# Verba.devops One-Click Deployment Script
# Supports Docker, Vercel (frontend), and Render (backend)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="verba-devops"
BACKEND_SERVICE="verba-backend"
FRONTEND_SERVICE="verba-frontend"
DOCKER_REGISTRY="ghcr.io" # GitHub Container Registry

# Utility functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed. Please install Node.js 18+ first."
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed. Please install Python 3.11+ first."
    fi
    
    success "All prerequisites are installed"
}

# Build Docker images
build_images() {
    log "Building Docker images..."
    
    # Build backend image
    log "Building backend image..."
    docker build -f docker/Dockerfile.backend -t $DOCKER_REGISTRY/$PROJECT_NAME/$BACKEND_SERVICE:latest .
    
    # Build frontend image
    log "Building frontend image..."
    docker build -f docker/Dockerfile.frontend -t $DOCKER_REGISTRY/$PROJECT_NAME/$FRONTEND_SERVICE:latest .
    
    success "Docker images built successfully"
}

# Deploy with Docker Compose
deploy_docker() {
    log "Deploying with Docker Compose..."
    
    # Create production environment file
    if [ ! -f .env.prod ]; then
        log "Creating production environment file..."
        cat > .env.prod << EOF
# Production Environment Configuration
NODE_ENV=production
MODE=offline
LOG_LEVEL=info
PYTHONPATH=/app/src

# Security
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
TRUSTED_HOSTS=localhost,127.0.0.1,yourdomain.com

# Performance
WHISPER_MODEL=base
ENABLE_DIARIZATION=true
ENABLE_SUMMARIZATION=true
MAX_FILE_SIZE=100MB
WORKERS=1

# Database
DATABASE_URL=sqlite:///app/data/verba.db
EOF
        warning "Please edit .env.prod with your production settings"
    fi
    
    # Stop existing containers
    docker-compose down 2>/dev/null || true
    
    # Start services
    docker-compose -f docker/docker-compose.yml --env-file .env.prod up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 10
    
    # Check backend health
    if curl -f http://localhost:8000/health &> /dev/null; then
        success "Backend is healthy"
    else
        error "Backend health check failed"
    fi
    
    # Check frontend
    if curl -f http://localhost:3000 &> /dev/null; then
        success "Frontend is healthy"
    else
        error "Frontend health check failed"
    fi
    
    success "Docker deployment completed successfully"
    log "Access your app at: http://localhost:3000"
}

# Deploy to Vercel (Frontend)
deploy_vercel() {
    log "Deploying frontend to Vercel..."
    
    # Check if Vercel CLI is installed
    if ! command -v vercel &> /dev/null; then
        log "Installing Vercel CLI..."
        npm i -g vercel
    fi
    
    # Login to Vercel (if not already logged in)
    if ! vercel whoami &> /dev/null; then
        log "Please login to Vercel..."
        vercel login
    fi
    
    # Build frontend
    log "Building frontend for production..."
    npm ci
    npm run build
    
    # Deploy to Vercel
    log "Deploying to Vercel..."
    vercel --prod --yes
    
    success "Frontend deployed to Vercel"
}

# Deploy to Render (Backend)
deploy_render() {
    log "Deploying backend to Render..."
    
    # Check if Render CLI is installed
    if ! command -v render &> /dev/null; then
        warning "Render CLI not found. Please deploy manually through Render dashboard."
        log "1. Go to https://render.com"
        log "2. Create a new Web Service"
        log "3. Connect your GitHub repository"
        log "4. Use the following settings:"
        log "   - Build Command: pip install -r backend/requirements.txt"
        log "   - Start Command: python -m uvicorn backend.src.main:app --host 0.0.0.0 --port \$PORT"
        log "   - Environment: Python 3.11"
        return
    fi
    
    # Create render.yaml if it doesn't exist
    if [ ! -f render.yaml ]; then
        log "Creating render.yaml configuration..."
        cat > render.yaml << EOF
services:
  - type: web
    name: verba-backend
    env: python
    buildCommand: pip install -r backend/requirements.txt
    startCommand: python -m uvicorn backend.src.main:app --host 0.0.0.0 --port \$PORT
    plan: starter
    envVars:
      - key: MODE
        value: offline
      - key: LOG_LEVEL
        value: info
      - key: PYTHONPATH
        value: /opt/render/project/src/backend/src
EOF
    fi
    
    # Deploy to Render
    render deploy
    
    success "Backend deployed to Render"
}

# Desktop app build
build_desktop() {
    log "Building desktop applications..."
    
    # Install Tauri CLI if not present
    if ! command -v cargo-tauri &> /dev/null; then
        log "Installing Tauri CLI..."
        npm install -g @tauri-apps/cli
    fi
    
    # Bundle Python dependencies
    log "Bundling Python dependencies..."
    mkdir -p python_libs
    pip install -r backend/requirements.txt --target python_libs --upgrade
    
    # Build for current platform
    log "Building desktop app for current platform..."
    npm run tauri build
    
    success "Desktop app built successfully"
    log "Built applications are in src-tauri/target/release/"
}

# Cleanup function
cleanup() {
    log "Cleaning up..."
    docker system prune -f &> /dev/null || true
}

# Health check
health_check() {
    log "Performing health check..."
    
    # Check backend
    if curl -f http://localhost:8000/health &> /dev/null; then
        backend_status="✅ Healthy"
    else
        backend_status="❌ Unhealthy"
    fi
    
    # Check frontend
    if curl -f http://localhost:3000 &> /dev/null; then
        frontend_status="✅ Healthy"
    else
        frontend_status="❌ Unhealthy"
    fi
    
    echo -e "\n${BLUE}=== Health Check Results ===${NC}"
    echo -e "Backend:  $backend_status"
    echo -e "Frontend: $frontend_status"
    echo -e "\n${BLUE}=== Service URLs ===${NC}"
    echo -e "Frontend: http://localhost:3000"
    echo -e "Backend:  http://localhost:8000"
    echo -e "API Docs: http://localhost:8000/docs"
    echo -e "Health:   http://localhost:8000/health"
}

# Show usage
show_usage() {
    echo -e "${BLUE}Verba.devops Deployment Script${NC}"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  docker     Deploy using Docker Compose (recommended)"
    echo "  vercel     Deploy frontend to Vercel"
    echo "  render     Deploy backend to Render"
    echo "  desktop    Build desktop applications"
    echo "  cloud      Deploy to Vercel + Render"
    echo "  build      Build Docker images only"
    echo "  health     Check service health"
    echo "  stop       Stop all services"
    echo "  clean      Clean up Docker resources"
    echo "  help       Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 docker          # Deploy locally with Docker"
    echo "  $0 cloud           # Deploy to cloud (Vercel + Render)"
    echo "  $0 desktop         # Build desktop app"
    echo "  $0 health          # Check if services are running"
}

# Stop services
stop_services() {
    log "Stopping all services..."
    docker-compose down 2>/dev/null || true
    success "Services stopped"
}

# Main deployment logic
main() {
    case "${1:-docker}" in
        "docker")
            check_prerequisites
            build_images
            deploy_docker
            health_check
            ;;
        "vercel")
            check_prerequisites
            deploy_vercel
            ;;
        "render")
            check_prerequisites
            deploy_render
            ;;
        "cloud")
            check_prerequisites
            deploy_vercel
            deploy_render
            ;;
        "desktop")
            check_prerequisites
            build_desktop
            ;;
        "build")
            check_prerequisites
            build_images
            ;;
        "health")
            health_check
            ;;
        "stop")
            stop_services
            ;;
        "clean")
            cleanup
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        *)
            error "Unknown option: $1. Use '$0 help' for usage information."
            ;;
    esac
}

# Trap cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"