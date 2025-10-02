# 🎬 Homeflix

A Netflix-style media streaming server with TMDB integration, running on Flask.

## 🚀 Quick Start

### Access Homeflix

**From this computer:**
```
http://localhost:5000
```

**From mobile/other devices on your network:**
```
http://192.168.11.104:5000
```

> 📖 **New to network access?** Check out [QUICK_START.md](QUICK_START.md)

---

## 📋 Requirements

- Python 3.11+
- Flask
- SQLite
- Internet connection (for TMDB API)

---

## 🔧 Installation & Setup

### 1. Install dependencies
```bash
make install
```

or manually:
```bash
pip3 install -r requirements.txt
```

### 2. Start the server
```bash
make run
```

The server will start at `http://0.0.0.0:5000`

### 3. Access from any device
- Same computer: `http://localhost:5000`
- Mobile/PC: `http://YOUR_IP:5000`

---

## 📱 Network Access

### Find Your IP Address

**On Windows (with WSL):**
```bash
# In Command Prompt
ipconfig
```
Look for your WiFi adapter's IPv4 address (e.g., 192.168.11.104)

**Check network status:**
```bash
make check-network
```

**Get IP quickly:**
```bash
make ip
```

> 📖 **Troubleshooting?** See [NETWORK_ACCESS.md](NETWORK_ACCESS.md) for detailed help

---

## 🎯 Available Commands

| Command | Description |
|---------|-------------|
| `make run` | Start the server |
| `make stop` | Stop the server |
| `make restart` | Restart the server |
| `make install` | Install dependencies |
| `make update` | Sync/update database |
| `make check-network` | Run network diagnostic |
| `make ip` | Show your IP address |

---

## 🗂️ Project Structure

```
Homeflix/
├── media_server.py       # Main Flask application
├── database.py           # Database models
├── db_service.py         # Database service layer
├── sync_data.py          # TMDB data sync
├── homeflix.db           # SQLite database
├── templates/            # HTML templates
├── static/               # JavaScript files
├── css/                  # CSS stylesheets
└── requirements.txt      # Python dependencies
```

---

## 🎨 Features

- ✅ Netflix-style UI
- ✅ Browse movies and TV shows
- ✅ Search functionality
- ✅ Video player with VidSrc integration
- ✅ TMDB API integration
- ✅ SQLite database for fast performance
- ✅ Responsive design (mobile-friendly)
- ✅ Network access from any device

---

## 🔄 Updating Content

To sync new movies and TV shows from TMDB:

```bash
make update
```

or manually:
```bash
python3 sync_data.py --movie-pages 10 --tv-pages 10
```

---

## 🐳 Docker Support

### Build and run with Docker Compose:
```bash
docker-compose up -d
```

### Stop:
```bash
docker-compose down
```

---

## 📖 Documentation

- [QUICK_START.md](QUICK_START.md) - Quick reference guide
- [NETWORK_ACCESS.md](NETWORK_ACCESS.md) - Detailed network troubleshooting
- [README_DATABASE.md](README_DATABASE.md) - Database information

---

## 🔒 Security Notes

⚠️ **For Local Network Use Only**

This application is designed for personal use on a trusted local network. It does not include authentication or HTTPS.

**Do NOT expose to the internet without:**
- Adding authentication
- Implementing HTTPS
- Setting up a reverse proxy
- Using a VPN

---

## 🆘 Troubleshooting

### Can't access from mobile?
1. Make sure both devices are on the same WiFi
2. Use your computer's IP, not `localhost`
3. Check firewall settings
4. Run `make check-network` for diagnostics

### Server won't start?
```bash
# Check if already running
ps aux | grep media_server.py

# Kill existing process
make stop

# Start fresh
make run
```

### Database issues?
```bash
# Re-sync database
python3 sync_data.py --force
```

---

## 📄 License

Personal use project. TMDB content and images are property of their respective owners.

---

## 🙏 Credits

- **TMDB API** - Movie and TV show data
- **VidSrc** - Video streaming
- **Flask** - Web framework

---

**Happy Streaming! 🍿**
