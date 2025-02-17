# 🚀 Todo App - Your Productive Companion

![Render Deployment](https://img.shields.io/badge/Render-Deployed-%23FF6F61?style=for-the-badge&logo=render&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10%2B-%233776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.0%2B-%23000?style=for-the-badge&logo=flask&logoColor=white)

A visually stunning and feature-rich Todo List application designed to boost your productivity with style! ✨


## 🌟 Features That Spark Joy

- **🌈 Dynamic Gradient Background** - Mesmerizing animated gradients that make task management delightful
- **⚡ Priority Matrix** - Categorize tasks with 🔥 High/⚡ Medium/🌱 Low priority system
- **📱 Mobile-First Design** - Perfectly responsive across all devices
- **🎮 Interactive UI** - Smooth animations & hover effects
- **📊 Progress Tracking** - Visual completion indicators
- **🗑️ Smart Archiving** - Auto-sort completed tasks with bulk delete
- **🔐 Secure Storage** - Server-side database with different access tiers:
  - **👤 Registered Users** - Permanent task storage
  - **👥 Guest Sessions** - Temporary storage preserved for 30 days
- **🆔 Anonymous Session ID** - Auto-generated session IDs preserve tasks without login
- **🔐 Google OAuth Integration** - Secure one-click authentication

## 🛠️ Tech Stack

**Frontend:**  
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-%237952B3?style=flat-square&logo=bootstrap&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-Animation-%231572B6?style=flat-square&logo=css3&logoColor=white)
![OAuth2](https://img.shields.io/badge/OAuth2-Google-%234285F4?style=flat-square&logo=google&logoColor=white)

**Backend:**  
![Flask](https://img.shields.io/badge/Flask-RESTful-%23000?style=flat-square&logo=flask&logoColor=white)
![Flask-Dance](https://img.shields.io/badge/Flask_Dance-OAuth-%23000?style=flat-square&logo=flask&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Database-%23003B57?style=flat-square&logo=sqlite&logoColor=white)

## 🚀 Quick Start

1. **Clone the repo**
   ```bash
   git clone https://github.com/yourusername/todo-app.git
   cd todo-app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   flask run
   ```

4. **Access in browser**  
   - Use immediately as guest with auto-generated session ID  
   - Or login with Google for permanent storage

## ☁️ Render Deployment

[![Live Demo](https://img.shields.io/badge/Live_Demo-Access_Now-%2300B4FF?style=for-the-badge&logo=render&logoColor=white)](https://todo-app-using-flask.onrender.com)

1. **Create New Web Service** on Render
2. Connect your GitHub repository
3. Set environment variables:
   ```text
   SECRET_KEY = your-secret-key-here
   GOOGLE_CLIENT_ID = your-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET = your-secret-key
   ```
4. Keep default build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app`

*Note: The demo link might take 20-30 seconds to wake up on Render's free tier*
