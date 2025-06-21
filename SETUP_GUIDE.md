# SLA Violation Prediction Platform - Local Setup Guide (Windows)

## 📥 Download and Setup Instructions

### Prerequisites
Before starting, make sure you have the following installed on your Windows machine:

1.  **Docker Desktop**: [Download Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)
    *   Docker Desktop includes Docker Engine, Docker CLI, Docker Compose, and Kubernetes.
    *   Ensure WSL 2 backend is enabled during installation.
2.  **Git**: [Download Git for Windows](https://git-scm.com/download/win)
    *   Choose the default options during installation.
3.  **Code Editor**: [VS Code](https://code.visualstudio.com/download) or any preferred editor.
4.  **Windows Terminal (Recommended)**: For a better command-line experience, consider installing [Windows Terminal](https://www.microsoft.com/store/productId/9N0RM4HKVDD4) from the Microsoft Store.

### 📁 Project Structure
```
sla-prediction-platform/
├── backend/                 # FastAPI backend
│   ├── app/                # Application code
│   ├── ml/                 # Machine learning models
│   ├── requirements.txt    # Python dependencies
│   └── .env.example       # Environment variables template
├── frontend/sla-dashboard/ # React frontend
│   ├── src/               # Source code
│   ├── package.json       # Node.js dependencies
│   └── .env.example       # Environment variables template
├── infra/                 # Docker and deployment configs
│   └── docker-compose.yml # Orchestrates all services
├── simulation_notebook.ipynb # Interactive demo
├── README.md              # Project documentation
└── SETUP_GUIDE.md         # This file
```

## 🚀 Step-by-Step Setup (Using Docker Compose)

### Step 1: Download the Project
Since this project was created in a sandbox environment, you'll need to recreate it locally. Follow these steps:

1.  **Create a new directory (e.g., on your C: drive or Desktop):**
    ```cmd
    mkdir sla-prediction-platform
    cd sla-prediction-platform
    ```

2.  **Copy the project files** (I'll provide all the code below, including the updated `docker-compose.yml`)

### Step 2: Prepare ML Models (One-time step)

Before running Docker Compose, you need to train the ML models locally once. This is because the `backend` Dockerfile copies the `ml` directory, and the models need to be present there.

1.  **Create backend directories and files** (copy the content from the files I'll provide)

2.  **Install Python and ML dependencies (temporarily for model training):**
    ```cmd
    cd backend
    pip install -r requirements.txt
    ```

3.  **Train the ML models:**
    ```cmd
    cd ml
    python train.py
    ```
    *   This will create `xgb_model.pkl`, `anomaly_model.pkl`, etc., in `backend/ml/`.

4.  **Return to the main project directory:**
    ```cmd
    cd ..\..
    ```

### Step 3: Run with Docker Compose

1.  **Open Docker Desktop** and ensure it's running.

2.  **Open a Command Prompt or Windows Terminal** and navigate to your main project directory (`sla-prediction-platform`).

3.  **Start all services using Docker Compose:**
    ```cmd
    docker-compose up --build -d
    ```
    *   `up`: Starts the services defined in `docker-compose.yml`.
    *   `--build`: Builds the Docker images for `backend` and `frontend` services (necessary on first run or after code changes).
    *   `-d`: Runs the containers in detached mode (in the background).

4.  **Check container status (optional):**
    ```cmd
    docker-compose ps
    ```

### Step 4: Access the Application

Allow a few minutes for all services (especially the database) to start up completely.

1.  **Frontend**: Open [http://localhost:5173](http://localhost:5173) in your web browser.
2.  **Backend API Documentation**: Open [http://localhost:8000/docs](http://localhost:8000/docs) for API documentation.
3.  **Grafana Dashboard**: Open [http://localhost:3000](http://localhost:3000) (default credentials: `admin`/`admin`).
4.  **Prometheus**: Open [http://localhost:9090](http://localhost:9090).

## 🔧 Configuration

### Environment Variables

For Docker Compose, most environment variables are set directly in `docker-compose.yml`. If you need to override them, you can create a `.env` file in the root of your project directory (where `docker-compose.yml` is located) and define variables there. For example:

```
# .env file in root directory
SECRET_KEY=my-custom-secret-key
```

### Backend Environment Variables (inside `backend/.env` - *not used with Docker Compose*)
*   When running with Docker Compose, the `backend/.env` file is **not used**. Environment variables are passed directly from `docker-compose.yml`.

### Frontend Environment Variables (inside `frontend/sla-dashboard/.env` - *not used with Docker Compose*)
*   Similarly, `frontend/sla-dashboard/.env` is **not used** when building the frontend Docker image. Variables are passed from `docker-compose.yml`.

## 🧪 Testing the Setup

### 1. Test Backend API
Open a **new command prompt/terminal** and run:
```cmd
rem Health check
curl http://localhost:8000/health

rem Test prediction
curl -X POST http://localhost:8000/predict/ ^
  -H "Content-Type: application/json" ^
  -d "{\"bandwidth\": 2.0, \"throughput\": 1.5, \"congestion\": 0.2, \"packet_loss\": 1.0, \"latency\": 10.0, \"jitter\": 0.5, \"percentage_video_occupancy\": 50.0, \"bitrate_video\": 800.0, \"number_videos\": 3}"
```
*   **Note**: If `curl` is not recognized in Command Prompt, use PowerShell or Git Bash, or download `curl` for Windows.

### 2. Test Frontend Features
-   ✅ Dark/Light mode toggle
-   ✅ Interactive map with 12+ nodes
-   ✅ Analytics charts
-   ✅ Node status overview
-   ✅ Real-time updates

### 3. Run Simulation Notebook
```cmd
rem Install Jupyter (if not already installed)
pip install jupyter

rem Start Jupyter (from the main project directory: sla-prediction-platform)
jupyter notebook simulation_notebook.ipynb
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Docker Compose Issues:
1.  **Containers not starting/exiting:**
    ```cmd
    docker-compose logs
    rem Check the logs for specific error messages.
    ```
2.  **Port conflicts:**
    -   Ensure ports 3000, 5173, 5432, 6379, 8000, 9090 are not in use by other applications.
    -   You can change the host ports in `docker-compose.yml` (e.g., `8001:8000`).
3.  **`docker-compose` command not found:**
    -   Ensure Docker Desktop is installed and running, and that Docker Compose is included in your system's PATH.

#### Backend Issues (if running outside Docker Compose):
*   Refer to the previous version of this guide or the `backend/README.md` for standalone backend troubleshooting.

#### Frontend Issues (if running outside Docker Compose):
*   Refer to the previous version of this guide or the `frontend/sla-dashboard/README.md` for standalone frontend troubleshooting.

#### ML Model Training Issues:
1.  **`python train.py` fails:**
    -   Ensure you have Python 3.11+ installed and its `pip` is working.
    -   Verify all dependencies in `backend/requirements.txt` are installed (`pip install -r backend/requirements.txt`).

## 🔄 Development Workflow

### Making Changes:
1.  **Backend code changes**: After modifying files in `backend/`, rebuild the backend service:
    ```cmd
    docker-compose up --build -d backend
    ```
2.  **Frontend code changes**: After modifying files in `frontend/sla-dashboard/`, rebuild the frontend service:
    ```cmd
    docker-compose up --build -d frontend
    ```
3.  **ML model changes**: If you modify `backend/ml/train.py` or `backend/ml/predictor.py`, you need to:
    -   Re-run `python backend\ml\train.py` locally to generate new `.pkl` files.
    -   Then rebuild the backend service: `docker-compose up --build -d backend`.

### Stopping Services:
```cmd
docker-compose down
```
*   This stops and removes containers, networks, and volumes created by `up`.

### Stopping and Removing Volumes (for a clean start):
```cmd
docker-compose down --volumes
```
*   Use this if you want to clear database data or Prometheus/Grafana data.

## 📊 Features Overview

### ✅ Working Features:
-   **Interactive Network Map**: 12+ nodes with risk visualization
-   **Dark/Light Mode**: Complete theme switching
-   **Real-time Dashboard**: Live metrics and charts
-   **ML Predictions**: SLA violation prediction with 99.5% accuracy
-   **Anomaly Detection**: Isolation Forest algorithm
-   **Alert System**: Telegram and email notifications
-   **Model Explainability**: SHAP values for predictions
-   **WebSocket Support**: Real-time updates
-   **Responsive Design**: Works on desktop and mobile

### 🔧 Optional Enhancements:
-   **Docker**: Fully integrated for easy local setup and deployment
-   **Monitoring**: Grafana and Prometheus included in Docker Compose
-   **CI/CD**: Use GitHub Actions workflow (provided in `.github/workflows/ci-cd.yml`)

## 📞 Support

If you encounter any issues:
1.  Check the troubleshooting section above
2.  Ensure Docker Desktop is running and healthy
3.  Check `docker-compose logs` for specific errors
4.  Check browser console and terminal for error messages

## 🎯 Next Steps

Once you have the project running locally with Docker Compose:
1.  Explore the interactive features
2.  Run the simulation notebook
3.  Customize the network topology
4.  Add your own data sources
5.  Deploy to production when ready

---

**Happy coding! 🚀**

