# TeamHub – Team Collaboration Platform

**Module:** H9CDOS – Cloud DevOpsSec | **NCI MSc Cloud Computing** | Semester 2, 2025–26

A dynamic cloud-based Django web application with a full CI/CD pipeline.

---

## Architecture

```
VS Code (Dev)
     |
     | git push
     v
GitHub Repository (Private)
     |
     | triggers
     v
GitHub Actions Pipeline
  ├── Stage 1: Lint (Flake8)
  ├── Stage 2: Security Analysis (Bandit + Safety)
  ├── Stage 3: Unit Tests + Coverage
  └── Stage 4: Deploy via SSH
              |
              | SSH (EC2_SSH_KEY secret)
              v
         AWS EC2 Instance (Amazon Linux 2023)
              |
              | git pull + pip install + migrate
              v
         Gunicorn (port 8000)
              |
              v
         TeamHub Django Application
```

---

## Features

- Collaboration Spaces — create, edit, archive, delete
- Role-based membership — Admin, Editor, Viewer
- Shared Notes — full CRUD per space
- Input validation — server-side on all forms
- CI/CD — automated deploy on every push to `main`

---

## Local Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/teamhub.git
cd teamhub

# 2. Create virtual environment
python -m venv venv

# 3. Activate (Windows)
venv\Scripts\activate
# Activate (Mac/Linux)
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run migrations
python manage.py migrate

# 6. Create superuser (optional)
python manage.py createsuperuser

# 7. Run development server
python manage.py runserver
```

Visit → http://127.0.0.1:8000

---

## Running Tests & Static Analysis

```bash
# Unit tests
python manage.py test tests/ --verbosity=2

# Tests with coverage
coverage run --source='.' manage.py test tests/
coverage report

# Flake8 linting
flake8 . --max-line-length=120 --exclude=venv,staticfiles,migrations

# Bandit security analysis (SAST)
bandit -r . -x ./tests,./staticfiles,./venv --severity-level medium

# Safety dependency CVE check
safety check --full-report
```

---

## EC2 Deployment Setup (One Time)

### Step 1 — Launch EC2 Instance in AWS

- **AMI:** Amazon Linux 2023
- **Instance type:** t3.micro
- **Key pair:** vockey (download labsuser.pem from Learner Lab)
- **Security group inbound rules:**
  - SSH → TCP port 22 → 0.0.0.0/0
  - Custom TCP → port 8000 → 0.0.0.0/0
- **Auto-assign public IP:** Enabled

### Step 2 — SSH into EC2

```bash
# Mac/Linux – fix key permissions first
chmod 400 ~/Downloads/labsuser.pem

# Connect
ssh -i ~/Downloads/labsuser.pem ec2-user@<EC2-Public-IP>
```

**Windows (PowerShell):**
```powershell
ssh -i C:\Users\<you>\Downloads\labsuser.pem ec2-user@<EC2-Public-IP>
```

### Step 3 — Run the setup script on EC2

```bash
# On EC2 – install git, clone repo, set up venv, install Gunicorn
sudo yum install git -y
git clone https://github.com/<your-username>/teamhub.git
cd ~/teamhub
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
export ALLOWED_HOSTS="*"
python manage.py collectstatic --noinput
```

### Step 4 — Install Gunicorn as a systemd service

```bash
# On EC2
sudo cp ~/teamhub/deployment/gunicorn.service /etc/systemd/system/gunicorn.service
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

Visit → http://<EC2-Public-IP>:8000

If you see: `Invalid HTTP_HOST header` → run:
```bash
export ALLOWED_HOSTS="*"
sudo systemctl restart gunicorn
```

---

## GitHub Actions CI/CD Setup

### Step 1 — Generate SSH deployment key (on local machine or VS Code terminal)

```bash
ssh-keygen -t rsa -b 4096 -C "github-deploy-key" -f deploy_key -N ""
```

### Step 2 — Add public key to EC2

```bash
# On EC2 instance – paste the contents of deploy_key.pub on a new line
nano ~/.ssh/authorized_keys
```

### Step 3 — Add secrets to GitHub

Go to: **GitHub Repo → Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value |
|---|---|
| `EC2_SSH_KEY` | Contents of `deploy_key` (private key — include BEGIN/END lines) |
| `EC2_HOST` | EC2 Public IPv4 address |

### Step 4 — Push to trigger CI/CD

```bash
git add .
git commit -m "Initial commit"
git push -u origin main
```

Every push to `main` automatically:
1. Runs Flake8 lint
2. Runs Bandit security scan
3. Runs unit tests with coverage
4. SSHs into EC2 → git pull → pip install → migrate → restarts Gunicorn

Monitor at: **GitHub → Actions tab**

---

## Project Structure

```
teamhub/
├── .github/
│   └── workflows/
│       └── deploy.yml          # CI/CD pipeline (lint → test → deploy to EC2)
├── deployment/
│   ├── gunicorn.service        # systemd service file for EC2
│   ├── ec2_setup.sh            # One-time EC2 server setup script
│   └── generate_ssh_key.sh     # Helper to generate SSH deploy keys
├── teamhub/                    # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── collaboration/              # Main app (spaces, members, notes)
│   ├── models.py
│   ├── views.py
│   ├── forms.py
│   └── urls.py
├── accounts/                   # Auth (register, login, profile)
├── templates/                  # Bootstrap 5 HTML templates
├── tests/                      # Unit tests
├── requirements.txt
└── manage.py
```

---

## Gunicorn Service Commands (on EC2)

```bash
# Check status
sudo systemctl status gunicorn

# Restart after code change
sudo systemctl restart gunicorn

# Stop
sudo systemctl stop gunicorn

# View logs
sudo journalctl -u gunicorn -n 50
```
