# 🚀 Shivam Petroleum Dashboard - Deployment Guide

## 📋 Deployment Options

### 1. 🌐 Streamlit Cloud (Easiest & Free)

**Best for:** Quick deployment, free hosting, easy updates

#### Steps:

1. **Push to GitHub:**

   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/shivam-petroleum-dashboards.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud:**

   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository
   - Set main file: `main_app.py`
   - Click "Deploy"

3. **Access:** Your app will be live at `https://your-app-name.streamlit.app`

---

### 2. 🐳 Docker Deployment (Recommended for Production)

**Best for:** Professional deployment, full control, scalability

#### Files Created:

- `Dockerfile` ✅
- `docker-compose.yml` ✅

#### Steps:

```bash
# Build and run
docker-compose up -d

# Access at http://localhost:8501
```

#### Deploy to Cloud:

- **AWS ECS/Fargate**
- **Google Cloud Run**
- **Azure Container Instances**
- **DigitalOcean App Platform**

---

### 3. ☁️ Heroku (Easy Cloud Deployment)

**Best for:** Quick cloud deployment, managed hosting

#### Steps:

1. **Install Heroku CLI**
2. **Create Heroku app:**

   ```bash
   heroku create shivam-petroleum-dashboards
   ```

3. **Deploy:**
   ```bash
   git add .
   git commit -m "Deploy to Heroku"
   git push heroku main
   ```

---

### 4. 🏠 Local Network Deployment

**Best for:** Internal company use, local network access

#### Steps:

```bash
# Run on all network interfaces
streamlit run main_app.py --server.address=0.0.0.0 --server.port=8501

# Access from other devices: http://YOUR_IP:8501
```

---

### 5. 🖥️ VPS/Server Deployment

**Best for:** Full control, custom domain, production use

#### Steps:

1. **Set up server** (Ubuntu/CentOS)
2. **Install dependencies:**

   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx
   pip3 install -r requirements.txt
   ```

3. **Run with systemd service:**

   ```bash
   sudo systemctl start shivam-dashboard
   sudo systemctl enable shivam-dashboard
   ```

4. **Configure Nginx reverse proxy**

---

## 🎯 Recommended Deployment Strategy

### For Quick Start: Streamlit Cloud

- ✅ Free
- ✅ Easy setup
- ✅ Automatic updates
- ✅ HTTPS included

### For Production: Docker + Cloud

- ✅ Professional
- ✅ Scalable
- ✅ Full control
- ✅ Custom domain

### For Internal Use: Local Network

- ✅ No internet required
- ✅ Fast access
- ✅ Full control

---

## 📁 Project Structure

```
shivamPetroleum/
├── main_app.py                 # Main multi-page app
├── pages/                      # Individual dashboard pages
│   ├── 1_📊_Account_Ledger.py
│   ├── 2_💰_Interest_Calculator.py
│   └── 3_📈_Customer_Analysis.py
├── ledger_app.py              # Standalone ledger app
├── interest_calculator_app.py # Standalone interest app
├── streamlit_app.py           # Standalone analysis app
├── ledger_data.json           # Data files
├── customer_data.json
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── start_all.bat              # Windows startup
├── start_all.sh               # Linux/Mac startup
└── DEPLOYMENT_GUIDE.md
```

---

## 🔧 Configuration Options

### Environment Variables

```bash
# Set in your deployment environment
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_THEME_BASE=light
```

### Custom Domain (for VPS/Server)

```nginx
# Nginx configuration
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 🚀 Quick Start Commands

### Local Development

```bash
# Start main app
streamlit run main_app.py

# Start individual apps
streamlit run ledger_app.py --server.port=8502
streamlit run interest_calculator_app.py --server.port=8503
streamlit run streamlit_app.py --server.port=8504

# Use startup scripts
./start_all.sh        # Linux/Mac
start_all.bat         # Windows
```

### Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Cloud Deployment

```bash
# Streamlit Cloud (after GitHub push)
# Just use the web interface at share.streamlit.io

# Heroku
heroku create your-app-name
git push heroku main
```

---

## 📊 Dashboard URLs

After deployment, access your dashboards at:

- **Main App (Multi-page):** `http://your-domain:8501`
- **Account Ledger:** `http://your-domain:8502`
- **Interest Calculator:** `http://your-domain:8503`
- **Customer Analysis:** `http://your-domain:8504`

---

## 🔒 Security Considerations

1. **Authentication:** Add login system for production
2. **HTTPS:** Use SSL certificates for secure access
3. **Firewall:** Restrict access to authorized IPs
4. **Data Backup:** Regular backup of JSON data files
5. **Updates:** Keep dependencies updated

---

## 📞 Support

For deployment issues or questions:

1. Check the logs: `docker-compose logs -f`
2. Verify data files are present
3. Check port availability
4. Review firewall settings

**Happy Deploying! 🎉**
