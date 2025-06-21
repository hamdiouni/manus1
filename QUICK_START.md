# Quick Start Commands (Windows with Docker Compose - Simplified)

## 🚀 Fast Setup (Copy & Paste)

### Prerequisites (Download & Install):
1.  **Docker Desktop**: [Download Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
    *   *Ensure WSL 2 backend is enabled during installation.*
2.  **Git**: [Download Git for Windows](https://git-scm.com/download/win)
3.  **Windows Terminal (Recommended)**: [Download from Microsoft Store](https://www.microsoft.com/store/productId/9N0RM4HKVDD4)

### 1. Download and Extract Project
```cmd
rem Download the project archive (you'll need to get this file from the agent)
rem Extract it using 7-Zip or any unzipping tool (e.g., 7z x sla-prediction-platform.tar.gz)
rem Then navigate into the extracted folder
cd sla-prediction-platform
```

### 2. Prepare ML Models (One-time step)

Before running Docker Compose, you need to train the ML models locally once:

```cmd
rem Install Python temporarily for model training
rem Download Python from: https://www.python.org/downloads/windows/
rem Make sure to check "Add Python to PATH" during installation

cd backend
pip install -r requirements.txt
cd ml
python train.py
cd ..\..
```

### 3. Run with Docker Compose

1.  **Open Docker Desktop** and ensure it's running.
2.  **Open a Command Prompt or Windows Terminal** in the `sla-prediction-platform` directory.
3.  **Start all services:**
    ```cmd
    docker-compose up --build -d
    ```
    *   Allow a few minutes for all services (especially the database) to start up completely.

### 4. Access Application

-   **Frontend**: Open [http://localhost:5173](http://localhost:5173) in your web browser
-   **Backend API Documentation**: Open [http://localhost:8000/docs](http://localhost:8000/docs)
-   **Backend Health Check**: Visit [http://localhost:8000/health](http://localhost:8000/health)

## ✅ Verification Steps

1.  **Backend Health**: Visit [http://localhost:8000/health](http://localhost:8000/health)
2.  **API Docs**: Visit [http://localhost:8000/docs](http://localhost:8000/docs)
3.  **Frontend**: Visit [http://localhost:5173](http://localhost:5173)
4.  **Test Features**:
    -   Toggle dark/light mode
    -   Click on map nodes
    -   Switch between tabs
    -   Check real-time updates

## 🐛 Quick Fixes

### If containers are not starting or exiting:
```cmd
docker-compose logs
rem Check the logs for specific error messages.
```

### If you need a clean start (clears database data):
```cmd
docker-compose down --volumes
docker-compose up --build -d
```

### If ML models are not loaded:
```cmd
cd backend\ml
python train.py
cd ..\..
docker-compose up --build -d backend
```

## 📱 Features to Test

-   ✅ Interactive map with 12+ network nodes
-   ✅ Dark/light mode switching
-   ✅ Real-time analytics dashboard
-   ✅ Node status monitoring
-   ✅ SLA violation predictions
-   ✅ Anomaly detection
-   ✅ Responsive design
-   ✅ WebSocket real-time updates

## 🛑 Stop Services

To stop all services:
```cmd
docker-compose down
```

To stop and remove all data (clean slate):
```cmd
docker-compose down --volumes
```

---

**This simplified setup includes only Frontend + Backend + Database - no monitoring overhead!**

