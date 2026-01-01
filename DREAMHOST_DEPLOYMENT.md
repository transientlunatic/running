# Deployment Guide for DreamHost Shared Hosting

This guide explains how to deploy the Race Results API on DreamHost shared hosting using FastCGI.

## Deployment Options

There are two ways to deploy the API:
1. **Automated Deployment via GitHub Actions** (recommended) - Automatically deploys on push to main/master branch
2. **Manual Deployment** - Manual SSH deployment following step-by-step instructions

## Prerequisites

- DreamHost shared hosting account with shell access
- Python 3.7 or higher installed
- SSH access to your hosting account

---

## Option 1: Automated Deployment via GitHub Actions (Recommended)

The repository includes a GitHub Actions workflow that automatically deploys to DreamHost when changes are pushed to the main/master branch.

### Setup GitHub Secrets

Configure the following secrets in your GitHub repository (Settings → Secrets and variables → Actions):

| Secret Name | Description | Example |
|-------------|-------------|---------|
| `DREAMHOST_HOST` | Your DreamHost server hostname | `yourserver.dreamhost.com` |
| `DREAMHOST_USERNAME` | Your SSH username | `yourusername` |
| `DREAMHOST_SSH_KEY` | Your private SSH key for authentication | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `DREAMHOST_PORT` | SSH port (usually 22) | `22` |
| `DREAMHOST_DEPLOY_PATH` | Absolute path to deployment directory | `/home/yourusername/yourdomain.com` |
| `DREAMHOST_HEALTH_URL` | (Optional) Health check endpoint URL | `https://yourdomain.com/api/health` |

### Generate SSH Key Pair

If you don't already have an SSH key pair for deployment:

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions-deploy" -f dreamhost_deploy_key
```

This creates two files:
- `dreamhost_deploy_key` - Private key (add to GitHub Secrets as `DREAMHOST_SSH_KEY`)
- `dreamhost_deploy_key.pub` - Public key (add to DreamHost authorized_keys)

### Add Public Key to DreamHost

```bash
# SSH to your DreamHost server
ssh yourusername@yourserver.dreamhost.com

# Add the public key to authorized_keys
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "your-public-key-content" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

### Initial Manual Setup Required

Before the automated deployment can work, you need to perform the initial setup once manually:

1. **Create the deployment directory structure:**
   ```bash
   ssh yourusername@yourserver.dreamhost.com
   cd ~/yourdomain.com
   python3 -m venv venv
   ```

2. **Create configuration files** (see Manual Deployment section below for details):
   - `api_config.py` - API configuration with keys and secrets
   - `.htaccess` - Apache rewrite rules
   - `api.fcgi` - FastCGI entry point

3. **Create the database:**
   ```bash
   source venv/bin/activate
   python3 << EOF
   from running_results.database import RaceResultsDatabase
   db = RaceResultsDatabase('race_results.db')
   db.close()
   print("Database created successfully!")
   EOF
   ```

### How Automated Deployment Works

Once configured, the GitHub Actions workflow:

1. **Triggers** on push to main/master or manual workflow dispatch
2. **Connects** to DreamHost via SSH using stored credentials
3. **Clones/Updates** the repository on the server
4. **Installs** the package and dependencies in the virtual environment
5. **Restarts** the FastCGI service by touching `api.fcgi`
6. **Validates** deployment with a health check (if URL configured)

### Manual Trigger

You can manually trigger a deployment from GitHub:
1. Go to Actions → Deploy to Dreamhost
2. Click "Run workflow"
3. Select the branch and click "Run workflow"

### Monitoring Deployments

- View deployment status in the Actions tab of your GitHub repository
- Check logs for any deployment failures
- Health check results appear in the workflow logs

---

## Option 2: Manual Deployment

If you prefer to deploy manually or need to troubleshoot, follow these steps:

## Step-by-Step Deployment

### 1. Connect to Your DreamHost Server

```bash
ssh username@yourserver.dreamhost.com
```

### 2. Set Up Python Environment

Navigate to your web directory:

```bash
cd ~/yourdomain.com
```

Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install the Package and Dependencies

Install the running_results package:

```bash
pip install git+https://github.com/transientlunatic/running.git
```

Or if you have the package locally, upload it and install:

```bash
pip install -e /path/to/running_results
```

Install FastCGI support:

```bash
pip install flup
```

### 4. Create Database

Create your race results database:

```bash
cd ~/yourdomain.com
python3 << EOF
from running_results.database import RaceResultsDatabase

# Create database
db = RaceResultsDatabase('race_results.db')
db.close()
print("Database created successfully!")
EOF
```

### 5. Configure API Settings

Create a configuration file `api_config.py`:

```python
# api_config.py
import os

# Database path (use absolute path)
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'race_results.db')

# API Keys - CHANGE THESE to your own secure keys
API_KEYS = {
    'your-secure-api-key-here',
    'another-api-key-if-needed',
}

# Flask secret key - CHANGE THIS to a random string
SECRET_KEY = 'your-very-secure-secret-key-change-this'

# Disable debug in production
DEBUG = False

# Enable CORS if needed for web frontend
CORS_ENABLED = True
```

**Important**: Generate secure random keys! You can use:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 6. Create FastCGI Script

Create `api.fcgi` file:

```python
#!/usr/bin/env python3
"""FastCGI script for Race Results API."""
import sys
import os

# Activate virtual environment
activate_this = '/home/username/yourdomain.com/venv/bin/activate_this.py'
with open(activate_this) as f:
    exec(f.read(), {'__file__': activate_this})

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from flup.server.fcgi import WSGIServer
from running_results.api import create_app, APIConfig

# Load configuration
config = APIConfig.from_file('api_config.py')

# Create app
app = create_app(config=config)

if __name__ == '__main__':
    WSGIServer(app).run()
```

Make it executable:

```bash
chmod +x api.fcgi
```

### 7. Create .htaccess File

Create `.htaccess` in your web directory:

```apache
# Enable FastCGI
Options +ExecCGI
AddHandler fcgid-script .fcgi

# Redirect all requests to api.fcgi
RewriteEngine On
RewriteBase /

# Don't rewrite requests for the FastCGI script itself
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d

# Redirect everything to api.fcgi
RewriteRule ^(.*)$ api.fcgi/$1 [QSA,L]

# Alternative: Set environment variables here instead of in api_config.py
# SetEnv RACE_DB_PATH /home/username/yourdomain.com/race_results.db
# SetEnv RACE_API_KEYS your-api-key-1,your-api-key-2
# SetEnv RACE_API_SECRET_KEY your-secret-key
```

### 8. Set Correct Permissions

```bash
chmod 755 ~/yourdomain.com
chmod 644 .htaccess
chmod 755 api.fcgi
chmod 644 api_config.py
chmod 664 race_results.db
```

### 9. Test the Deployment

Visit your domain in a browser:

```
https://yourdomain.com/
```

You should see the API information page.

Test the health endpoint:

```
https://yourdomain.com/api/health
```

Test listing races:

```
https://yourdomain.com/api/races
```

### 10. Add Initial Data

Use the API to add your race results:

```bash
curl -X POST https://yourdomain.com/api/results \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secure-api-key-here" \
  -d '{
    "race_name": "My First Race",
    "race_year": 2024,
    "race_category": "10k",
    "results": [
      {
        "name": "John Smith",
        "position_overall": 1,
        "finish_time_seconds": 1800,
        "club": "Running Club"
      }
    ]
  }'
```

## Directory Structure

Your DreamHost directory should look like:

```
~/yourdomain.com/
├── venv/                      # Virtual environment
├── api.fcgi                   # FastCGI script
├── api_config.py              # Configuration file
├── .htaccess                  # Apache configuration
├── race_results.db            # SQLite database
└── logs/                      # Optional: log directory
```

## Troubleshooting

### 500 Internal Server Error

Check Apache error logs:

```bash
tail -f ~/logs/yourdomain.com/http/error.log
```

Common issues:
- Incorrect file permissions
- Python path issues in api.fcgi
- Missing dependencies
- Database permission errors

### Database Locked Errors

If you get "database is locked" errors:

```bash
# Check database permissions
chmod 664 race_results.db

# Ensure directory is writable
chmod 755 ~/yourdomain.com
```

### Import Errors

Make sure the virtual environment is properly activated in api.fcgi:

```python
# Check that this path is correct
activate_this = '/home/username/yourdomain.com/venv/bin/activate_this.py'
```

### FastCGI Not Working

Some DreamHost servers may not support FastCGI. Alternative: Use Passenger with WSGI.

Create `passenger_wsgi.py`:

```python
import sys
import os

# Activate virtual environment
INTERP = os.path.join(os.environ['HOME'], 'yourdomain.com', 'venv', 'bin', 'python3')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.insert(0, os.path.dirname(__file__))

from running_results.api import create_app, APIConfig

# Load configuration
config = APIConfig.from_file('api_config.py')

# Create application
application = create_app(config=config)
```

## Security Best Practices

1. **Use HTTPS**: Ensure your DreamHost site uses SSL/TLS
2. **Secure API Keys**: Use long, random API keys (32+ characters)
3. **Protect Configuration**: Don't commit api_config.py to version control
4. **Regular Backups**: Backup your database regularly
5. **Monitor Access**: Check logs for unusual activity

```bash
# Backup database
cp race_results.db race_results.db.backup.$(date +%Y%m%d)
```

6. **Restrict Database Access**: Ensure database file is not web-accessible

```apache
# Add to .htaccess
<Files "race_results.db">
    Order allow,deny
    Deny from all
</Files>
```

## Maintenance

### Updating the Package

```bash
cd ~/yourdomain.com
source venv/bin/activate
pip install --upgrade git+https://github.com/transientlunatic/running.git

# Restart by touching the FastCGI script
touch api.fcgi
```

### Database Backups

Set up a cron job for automatic backups:

```bash
crontab -e
```

Add:

```
0 2 * * * cp ~/yourdomain.com/race_results.db ~/backups/race_results.db.$(date +\%Y\%m\%d)
0 2 * * 0 find ~/backups/ -name "race_results.db.*" -mtime +30 -delete
```

### Monitoring

Create a simple monitoring script:

```bash
#!/bin/bash
# monitor.sh
curl -s https://yourdomain.com/api/health | grep -q "healthy"
if [ $? -ne 0 ]; then
    echo "API is down!" | mail -s "API Alert" your@email.com
fi
```

Add to cron:

```
*/15 * * * * /home/username/yourdomain.com/monitor.sh
```

## Support

For issues specific to:
- **DreamHost**: Contact DreamHost support
- **Running Results API**: Open an issue on GitHub
- **General deployment**: Check the API documentation

## Additional Resources

- [DreamHost FastCGI Documentation](https://help.dreamhost.com/hc/en-us/articles/215769578-Passenger-overview)
- [Flask Deployment Documentation](https://flask.palletsprojects.com/en/latest/deploying/)
- [API Documentation](../api/API_DOCUMENTATION.md)
