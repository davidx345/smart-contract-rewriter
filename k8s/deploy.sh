#!/bin/bash

# Smart Contract Rewriter Kubernetes Deployment Script
# Phase 6: Container Orchestration with Kubernetes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="smart-contract-rewriter"
KUBECTL_TIMEOUT="300s"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if kubectl is installed
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if connected to a cluster
    if ! kubectl cluster-info &> /dev/null; then
        print_error "Not connected to a Kubernetes cluster. Please configure kubectl first."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to build Docker images
build_images() {
    print_status "Building Docker images..."
    
    # Build backend image
    print_status "Building backend image..."
    docker build -t smart-contract-rewriter/backend:latest ./backend/
    
    # Build frontend image
    print_status "Building frontend image..."
    docker build -t smart-contract-rewriter/frontend:latest ./frontend/
    
    print_success "Docker images built successfully"
}

# Function to apply Kubernetes manifests
deploy_kubernetes() {
    print_status "Deploying to Kubernetes..."
    
    # Apply manifests in order
    local manifests=(
        "00-namespace.yaml"
        "01-configmaps.yaml"
        "02-secrets.yaml"
        "03-storage.yaml"
        "09-rbac.yaml"
        "10-database-init.yaml"
        "04-postgres.yaml"
        "05-redis.yaml"
        "06-backend.yaml"
        "07-frontend.yaml"
        "08-ingress-networking.yaml"
        "11-monitoring.yaml"
    )
    
    for manifest in "${manifests[@]}"; do
        if [[ -f "k8s/$manifest" ]]; then
            print_status "Applying $manifest..."
            kubectl apply -f "k8s/$manifest"
        else
            print_warning "Manifest $manifest not found, skipping..."
        fi
    done
    
    print_success "Kubernetes manifests applied"
}

# Function to wait for deployments to be ready
wait_for_deployments() {
    print_status "Waiting for deployments to be ready..."
    
    local deployments=("postgres" "redis" "backend" "frontend")
    
    for deployment in "${deployments[@]}"; do
        print_status "Waiting for deployment/$deployment to be ready..."
        kubectl wait --for=condition=available deployment/$deployment \
            --namespace=$NAMESPACE \
            --timeout=$KUBECTL_TIMEOUT
    done
    
    print_success "All deployments are ready"
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Wait for postgres to be ready
    print_status "Waiting for PostgreSQL to be ready..."
    kubectl wait --for=condition=ready pod \
        --selector=app.kubernetes.io/component=database \
        --namespace=$NAMESPACE \
        --timeout=$KUBECTL_TIMEOUT
    
    # Run migrations using a job
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration-$(date +%s)
  namespace: $NAMESPACE
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
      - name: migration
        image: smart-contract-rewriter/backend:latest
        command: ["python", "-m", "alembic", "upgrade", "head"]
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: DATABASE_URL
      backoffLimit: 3
EOF
    
    print_success "Database migration job created"
}

# Function to check service health
check_health() {
    print_status "Checking service health..."
    
    # Check if all pods are running
    print_status "Checking pod status..."
    kubectl get pods --namespace=$NAMESPACE
    
    # Check services
    print_status "Checking services..."
    kubectl get services --namespace=$NAMESPACE
    
    # Check if backend is responding
    print_status "Checking backend health..."
    kubectl port-forward service/backend-service 8080:8000 --namespace=$NAMESPACE &
    PORT_FORWARD_PID=$!
    sleep 5
    
    if curl -f http://localhost:8080/health; then
        print_success "Backend health check passed"
    else
        print_warning "Backend health check failed"
    fi
    
    kill $PORT_FORWARD_PID 2>/dev/null || true
    
    print_success "Health checks completed"
}

# Function to display deployment information
display_info() {
    print_status "Deployment Information:"
    echo ""
    echo "Namespace: $NAMESPACE"
    echo ""
    echo "Services:"
    kubectl get services --namespace=$NAMESPACE
    echo ""
    echo "Pods:"
    kubectl get pods --namespace=$NAMESPACE
    echo ""
    echo "Ingress:"
    kubectl get ingress --namespace=$NAMESPACE
    echo ""
    
    print_status "To access the application:"
    echo "1. Frontend: kubectl port-forward service/frontend-service 3000:80 --namespace=$NAMESPACE"
    echo "2. Backend API: kubectl port-forward service/backend-service 8000:8000 --namespace=$NAMESPACE"
    echo "3. Prometheus: kubectl port-forward service/prometheus 9090:9090 --namespace=$NAMESPACE"
    echo ""
    
    print_status "To view logs:"
    echo "Backend: kubectl logs -f deployment/backend --namespace=$NAMESPACE"
    echo "Frontend: kubectl logs -f deployment/frontend --namespace=$NAMESPACE"
    echo "Database: kubectl logs -f deployment/postgres --namespace=$NAMESPACE"
    echo ""
    
    print_status "To scale services:"
    echo "kubectl scale deployment backend --replicas=5 --namespace=$NAMESPACE"
    echo "kubectl scale deployment frontend --replicas=3 --namespace=$NAMESPACE"
}

# Function to cleanup (for development)
cleanup() {
    print_warning "Cleaning up existing deployment..."
    kubectl delete namespace $NAMESPACE --ignore-not-found=true
    print_success "Cleanup completed"
}

# Main deployment function
main() {
    echo "🚀 Smart Contract Rewriter - Kubernetes Deployment (Phase 6)"
    echo "============================================================"
    
    # Parse command line arguments
    case "${1:-deploy}" in
        "cleanup")
            cleanup
            ;;
        "build")
            check_prerequisites
            build_images
            ;;
        "deploy")
            check_prerequisites
            build_images
            deploy_kubernetes
            wait_for_deployments
            run_migrations
            check_health
            display_info
            ;;
        "status")
            display_info
            ;;
        "health")
            check_health
            ;;
        *)
            echo "Usage: $0 {deploy|build|cleanup|status|health}"
            echo ""
            echo "Commands:"
            echo "  deploy  - Full deployment (build + deploy + migrate)"
            echo "  build   - Build Docker images only"
            echo "  cleanup - Remove existing deployment"
            echo "  status  - Show deployment status"
            echo "  health  - Run health checks"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"