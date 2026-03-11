#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Generate SSH Deployment Key for GitHub Actions
# Run this on your LOCAL machine (or Cloud9 / VS Code terminal)
#
# This creates:
#   deploy_key      → private key → add to GitHub Secrets as EC2_SSH_KEY
#   deploy_key.pub  → public key  → add to EC2 ~/.ssh/authorized_keys
# ─────────────────────────────────────────────────────────────────────────────

echo "Generating SSH deployment key pair..."
ssh-keygen -t rsa -b 4096 -C "github-deploy-key" -f deploy_key -N ""

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 1 — Add PUBLIC key to your EC2 instance:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SSH into your EC2 instance and run:"
echo "  nano ~/.ssh/authorized_keys"
echo "Then paste this public key on a NEW LINE at the bottom:"
echo ""
cat deploy_key.pub
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 2 — Add PRIVATE key to GitHub Secrets:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Go to: GitHub Repo → Settings → Secrets → Actions → New secret"
echo "Name:  EC2_SSH_KEY"
echo "Value: (copy everything below including BEGIN and END lines)"
echo ""
cat deploy_key
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "STEP 3 — Add EC2 IP to GitHub Secrets:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Name:  EC2_HOST"
echo "Value: Your EC2 instance Public IPv4 address"
echo "(Find it in AWS Console → EC2 → Instances → your instance)"
