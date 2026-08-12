#!/bin/bash
# ==============================================================================
# FraudShield AI — Oracle Cloud Infrastructure (OCI) Automated Deployment Script
# ==============================================================================
# This script sets up a fresh Ubuntu / Oracle Linux VM on Oracle Cloud Always Free Tier,
# installs Docker & Docker Compose, sets up production environment variables,
# and starts the entire FraudShield AI stack (Frontend + Backend + ML Engine + DBs).
# ==============================================================================

set -e

echo "🚀 Starting FraudShield AI Automated OCI Deployment..."

# Step 1: System Update & Dependencies
echo "📦 Updating system packages..."
sudo apt-get update -y && sudo apt-get upgrade -y
sudo apt-get install -y curl git apt-transport-https ca-certificates software-properties-common

# Step 2: Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker installed successfully."
fi

# Step 3: Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
    echo "🐙 Installing Docker Compose..."
    sudo apt-get install -y docker-compose-plugin docker-compose
fi

# Step 4: Configure Firewall Ports (80, 443, 3000, 8000)
echo "🛡️ Configuring Firewall rules..."
if command -v ufw &> /dev/null; then
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw allow 3000/tcp
    sudo ufw allow 8000/tcp
    sudo ufw --force enable || true
fi

# Step 5: Setup Production Environment
if [ ! -f .env ]; then
    echo "⚙️ Creating production .env file..."
    cat <<EOT > .env
ENVIRONMENT=production
DEBUG=false
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000", "http://localhost", "*"]

POSTGRES_USER=fraudshield
POSTGRES_PASSWORD=$(openssl rand -hex 16)
POSTGRES_DB=fraudshield
DATABASE_URL=postgresql+asyncpg://fraudshield:\${POSTGRES_PASSWORD}@postgres:5432/fraudshield

REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=$(openssl rand -hex 32)
JWT_ALGORITHM=HS256

KAFKA_BOOTSTRAP_SERVERS=kafka:9092
EOT
    echo "✅ Created .env file with randomized secure passwords!"
fi

# Step 6: Build and Launch Containerized Stack
echo "🏗️ Building and starting FraudShield AI containers..."
sudo docker-compose up -d --build

echo "
==============================================================================
🎉 FraudShield AI is LIVE on Oracle Cloud!
==============================================================================
- Frontend Dashboard:  http://$(curl -s ifconfig.me):3000
- Backend REST API:    http://$(curl -s ifconfig.me):8000/api/v1
- Interactive API Docs: http://$(curl -s ifconfig.me):8000/docs
==============================================================================
"
