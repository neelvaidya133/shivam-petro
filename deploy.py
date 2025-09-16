#!/usr/bin/env python3
"""
Deployment script for Shivam Petroleum Dashboards
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_requirements():
    """Check if all required files exist"""
    required_files = [
        "ledger_data.json",
        "customer_data.json", 
        "ledger_app.py",
        "interest_calculator_app.py",
        "streamlit_app.py",
        "dashboard_launcher.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"  - {file}")
        return False
    
    print("✅ All required files found")
    return True

def install_dependencies():
    """Install Python dependencies"""
    return run_command("pip install -r requirements.txt", "Installing dependencies")

def run_tests():
    """Run basic syntax tests"""
    test_files = [
        "ledger_app.py",
        "interest_calculator_app.py", 
        "streamlit_app.py",
        "dashboard_launcher.py"
    ]
    
    for file in test_files:
        if not run_command(f"python -m py_compile {file}", f"Testing {file}"):
            return False
    
    return True

def create_startup_scripts():
    """Create startup scripts for each dashboard"""
    
    # Windows batch files
    scripts = {
        "start_launcher.bat": "streamlit run dashboard_launcher.py",
        "start_ledger.bat": "streamlit run ledger_app.py", 
        "start_interest.bat": "streamlit run interest_calculator_app.py",
        "start_analysis.bat": "streamlit run streamlit_app.py"
    }
    
    for filename, command in scripts.items():
        with open(filename, 'w') as f:
            f.write(f"@echo off\n")
            f.write(f"echo Starting {filename.replace('.bat', '').replace('start_', '').title()} Dashboard...\n")
            f.write(f"{command}\n")
            f.write(f"pause\n")
        print(f"✅ Created {filename}")
    
    # Linux/Mac shell scripts
    scripts_shell = {
        "start_launcher.sh": "streamlit run dashboard_launcher.py",
        "start_ledger.sh": "streamlit run ledger_app.py",
        "start_interest.sh": "streamlit run interest_calculator_app.py", 
        "start_analysis.sh": "streamlit run streamlit_app.py"
    }
    
    for filename, command in scripts_shell.items():
        with open(filename, 'w') as f:
            f.write(f"#!/bin/bash\n")
            f.write(f"echo 'Starting {filename.replace('.sh', '').replace('start_', '').title()} Dashboard...'\n")
            f.write(f"{command}\n")
        os.chmod(filename, 0o755)  # Make executable
        print(f"✅ Created {filename}")

def create_docker_setup():
    """Create Docker configuration for deployment"""
    
    dockerfile_content = """FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run the launcher
CMD ["streamlit", "run", "dashboard_launcher.py", "--server.port=8501", "--server.address=0.0.0.0"]
"""
    
    with open("Dockerfile", 'w') as f:
        f.write(dockerfile_content)
    print("✅ Created Dockerfile")
    
    # Docker compose
    compose_content = """version: '3.8'

services:
  shivam-dashboards:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
    restart: unless-stopped
"""
    
    with open("docker-compose.yml", 'w') as f:
        f.write(compose_content)
    print("✅ Created docker-compose.yml")

def create_readme():
    """Create comprehensive README for deployment"""
    
    readme_content = """# 🏢 Shivam Petroleum - Dashboard Suite

## 📊 Available Dashboards

### 1. 📈 Account Ledger Dashboard (`ledger_app.py`)
- View customer account balances
- Analyze transaction trends  
- Track outstanding amounts
- Download transaction data

### 2. 💰 Interest Calculator Dashboard (`interest_calculator_app.py`)
- Group transactions by date
- Calculate compound interest on balances
- Daily interest analysis with FIFO payments
- Export interest reports

### 3. 📊 Customer Analysis Dashboard (`streamlit_app.py`)
- Analyze product sales
- Calculate profits
- View customer transactions
- Generate reports

### 4. 🚀 Dashboard Launcher (`dashboard_launcher.py`)
- Central hub to access all dashboards
- Quick navigation between applications

## 🚀 Quick Start

### Option 1: Direct Launch
```bash
# Launch specific dashboard
streamlit run ledger_app.py
streamlit run interest_calculator_app.py  
streamlit run streamlit_app.py
streamlit run dashboard_launcher.py

# Or use startup scripts
./start_launcher.sh    # Linux/Mac
start_launcher.bat     # Windows
```

### Option 2: Docker Deployment
```bash
# Build and run with Docker
docker-compose up -d

# Access at http://localhost:8501
```

## 📁 Data Files

- `ledger_data.json` - Account ledger data (13 customers)
- `customer_data.json` - Customer transaction data
- `ledger_processor.py` - Data processing script

## 🛠️ Development

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Process New Data
```bash
python ledger_processor.py
```

## 🌐 Deployment Options

### 1. Local Development
- Run directly with Streamlit
- Use startup scripts for convenience

### 2. Docker Deployment
- Use `docker-compose up -d`
- Accessible on any port 8501

### 3. Cloud Deployment
- Deploy to Streamlit Cloud
- Deploy to Heroku, AWS, or Google Cloud
- Use Docker for containerized deployment

## 📋 Features

### Interest Calculator (NEW!)
- ✅ **Daily Compound Interest** calculation
- ✅ **FIFO Payment** logic (oldest debt first)
- ✅ **Complete Daily Coverage** (no gaps)
- ✅ **Opening Balance** included
- ✅ **Export Capabilities** for reports

### Account Ledger
- ✅ Customer balance tracking
- ✅ Transaction history
- ✅ Visual trend analysis
- ✅ Data export

### Customer Analysis  
- ✅ Product sales analysis
- ✅ Profit calculations
- ✅ Customer insights
- ✅ Report generation

## 🔧 Configuration

### Interest Rate
- Default: 12% per annum
- Configurable in the dashboard
- Daily compound calculation

### Data Processing
- Indian number format support
- Date standardization (DD/MM/YYYY → YYYY-MM-DD)
- Balance tracking with Dr/Cr indicators

## 📞 Support

For technical support or questions about the dashboards, please refer to the code documentation or contact the development team.

---
**Shivam Petroleum Dashboard Suite** - Built with Streamlit & Python
"""
    
    with open("README_DEPLOYMENT.md", 'w') as f:
        f.write(readme_content)
    print("✅ Created README_DEPLOYMENT.md")

def main():
    """Main deployment function"""
    print("🚀 SHIVAM PETROLEUM DASHBOARD DEPLOYMENT")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("❌ Deployment aborted due to missing files")
        return False
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        return False
    
    # Run tests
    if not run_tests():
        print("❌ Tests failed")
        return False
    
    # Create startup scripts
    create_startup_scripts()
    
    # Create Docker setup
    create_docker_setup()
    
    # Create documentation
    create_readme()
    
    print("\n🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
    print("\n📋 Next Steps:")
    print("1. Run: streamlit run dashboard_launcher.py")
    print("2. Or use: ./start_launcher.sh (Linux/Mac) or start_launcher.bat (Windows)")
    print("3. For Docker: docker-compose up -d")
    print("\n🌐 Access your dashboards at: http://localhost:8501")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
