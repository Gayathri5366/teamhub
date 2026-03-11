#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# TeamHub EC2 Server Setup Script
# Cloud DevOpsSec Project – NCI MSc Cloud Computing
#
# Run this ONCE on a fresh Amazon Linux 2023 EC2 instance to prepare it
# as the deployment server for TeamHub.
#
# Architecture: GitHub Actions → SSH → This EC2 → Gunicorn → Django
#
# Usage (after SSH into EC2):
#   chmod +x ec2_setup.sh
#   ./ec2_setup.sh
# ─────────────────────────────────────────────────────────────────────────────

set -e  # Exit immediately if any command fails

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  TeamHub EC2 Setup Script"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Step 1: Install Git ───────────────────────────────────────────────────────
echo "[1/7] Installing Git..."
sudo yum install git -y
git --version

# ── Step 2: Install Python 3 (comes with Amazon Linux 2023) ──────────────────
echo "[2/7] Checking Python..."
python3 --version

# ── Step 3: Clone the TeamHub repository ─────────────────────────────────────
echo "[3/7] Cloning TeamHub repository..."
# Replace <your-github-username> with your actual GitHub username
cd ~
git clone https://github.com/<your-github-username>/teamhub.git
cd ~/teamhub

# ── Step 4: Create and activate Python virtual environment ───────────────────
echo "[4/7] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# ── Step 5: Install application dependencies ─────────────────────────────────
echo "[5/7] Installing dependencies..."
pip install -r requirements.txt

# ── Step 6: Run initial setup ────────────────────────────────────────────────
echo "[6/7] Running Django setup..."
export DJANGO_SECRET_KEY="change-this-to-a-long-random-secret-key"
export DEBUG="False"
export ALLOWED_HOSTS="*"

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Create a default superuser (optional)
python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@teamhub.com', 'Admin1234!')
    print('Superuser created: admin / Admin1234!')
else:
    print('Superuser already exists.')
"

# ── Step 7: Install and start Gunicorn systemd service ───────────────────────
echo "[7/7] Setting up Gunicorn service..."
sudo cp ~/teamhub/deployment/gunicorn.service /etc/systemd/system/gunicorn.service
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn --no-pager

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Setup complete!"
echo "  TeamHub is running at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
