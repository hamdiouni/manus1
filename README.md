# SLA Violation Prediction and Anomaly Detection Platform

A comprehensive, production-ready platform for predicting SLA violations and detecting anomalies in network telemetry data using machine learning.

## 🚀 Features

### Core Capabilities
- **Real-time SLA Violation Prediction** using XGBoost and Random Forest models
- **Anomaly Detection** with Isolation Forest algorithm
- **Interactive Network Topology Map** with risk visualization
- **Real-time WebSocket Updates** for live monitoring
- **Automatic Model Retraining** pipeline with new data
- **Multi-channel Alert System** (Telegram, Email)
- **Model Explainability** with SHAP values
- **Comprehensive REST API** with FastAPI
- **Production-ready Deployment** with Docker and cloud support

### Advanced Features
- **Dark/Light Mode** theme switching
- **Responsive Design** for desktop and mobile
- **Real-time Analytics Dashboard** with interactive charts
- **Network Health Monitoring** with 12+ node visualization
- **Risk Score Color-coding** for network connections
- **Automated CI/CD Pipeline** with GitHub Actions
- **Monitoring Stack** with Grafana and Prometheus
- **Cloud Deployment** support for GCP, AWS, and Azure

## 📊 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Database      │
│   (React)       │◄──►│   (FastAPI)     │◄──►│ (PostgreSQL)    │
│                 │    │                 │    │                 │
│ • Interactive   │    │ • ML Models     │    │ • Telemetry     │
│   Map           │    │ • Predictions   │    │ • Predictions   │
│ • Real-time     │    │ • WebSocket     │    │ • Model Metrics │
│   Dashboard     │    │ • Alerts        │    │ • Alert Logs    │
│ • Dark/Light    │    │ • Auto-retrain  │    │                 │
│   Mode          │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         │              │   ML Pipeline   │              │
         └──────────────┤                 ├──────────────┘
                        │ • XGBoost       │
                        │ • Random Forest │
                        │ • Isolation     │
                        │   Forest        │
                        │ • SHAP          │
                        │   Explainers    │
                        └─────────────────┘
```

## 🛠 Technology Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **SQLAlchemy** - Database ORM with PostgreSQL
- **XGBoost** - Gradient boosting for SLA prediction
- **Scikit-learn** - Machine learning utilities
- **SHAP** - Model explainability
- **WebSockets** - Real-time communication
- **Redis** - Caching and session management

### Frontend
- **React 18** - Modern UI framework
- **Leaflet.js** - Interactive maps
- **Tailwind CSS** - Utility-first styling
- **shadcn/ui** - High-quality components
- **Recharts** - Data visualization
- **WebSocket Client** - Real-time updates

### Infrastructure
- **Docker** - Containerization
- **PostgreSQL** - Primary database
- **Redis** - Caching layer
- **Nginx** - Reverse proxy and static serving
- **Grafana** - Monitoring dashboards
- **Prometheus** - Metrics collection

### Cloud & DevOps
- **GitHub Actions** - CI/CD pipeline
- **Google Cloud Platform** - Cloud Run, Cloud SQL
- **Amazon Web Services** - ECR, ECS/Fargate
- **Microsoft Azure** - Container Registry, Container Instances

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sla-prediction-platform
   ```

2. **Start with Docker Compose**
   ```bash
   cp infra/.env.example infra/.env
   # Edit infra/.env with your configuration
   ./infra/deploy.sh local
   ```

3. **Access the platform**
   - Frontend: http://localhost
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Grafana: http://localhost:3000 (admin/admin)

### Cloud Deployment

#### Google Cloud Platform
```bash
export GCP_PROJECT_ID=your-project-id
./infra/deploy.sh gcp
```

#### Amazon Web Services
```bash
export AWS_ACCOUNT_ID=123456789012
export AWS_REGION=us-east-1
./infra/deploy.sh aws
```

#### Microsoft Azure
```bash
export AZURE_LOCATION=eastus
./infra/deploy.sh azure
```

## 📖 Documentation

### API Endpoints

#### Prediction Endpoints
- `POST /predict/` - Get SLA violation prediction
- `POST /predict-and-store/` - Predict and store in database
- `POST /anomaly/` - Detect anomalies in telemetry data
- `GET /explain/{id}` - Get SHAP explanation for prediction

#### Data Management
- `GET /telemetry/` - List telemetry records
- `POST /telemetry/` - Create new telemetry record
- `GET /telemetry/{id}` - Get specific telemetry record
- `PUT /telemetry/{id}` - Update telemetry record
- `DELETE /telemetry/{id}` - Delete telemetry record

#### Model Management
- `GET /model/metrics` - Get current model performance metrics
- `POST /retrain/trigger` - Manually trigger model retraining

#### Alerts & Monitoring
- `POST /alerts/configure` - Configure alert settings
- `GET /health` - API health check
- `GET /analytics/high-risk` - Get high-risk predictions
- `GET /analytics/anomalies` - Get recent anomalies

#### Real-time Communication
- `WebSocket /ws/telemetry` - Real-time telemetry updates

### Machine Learning Models

#### SLA Violation Prediction
- **Primary Model**: XGBoost (tuned) - 99.5% accuracy, 99.82% AUC
- **Baseline Model**: Random Forest - 98.01% accuracy, 99.75% AUC
- **Features**: Bandwidth, throughput, congestion, packet loss, latency, jitter, video metrics

#### Anomaly Detection
- **Model**: Isolation Forest
- **Detection Rate**: ~12% anomaly detection on network data
- **Features**: All telemetry parameters with statistical analysis

#### Model Explainability
- **SHAP Values**: Feature importance for individual predictions
- **Feature Importance**: Global model interpretation
- **Visualization**: Interactive charts and explanations

### Frontend Features

#### Interactive Network Map
- **12 Network Nodes**: Servers, routers, and edge nodes across the US
- **Risk Visualization**: Color-coded connections (Green/Yellow/Red)
- **Real-time Updates**: Live status and metrics
- **Node Details**: Clickable popups with node information

#### Dashboard Components
- **SLA Violations**: Real-time count and trend analysis
- **Anomaly Detection**: Live anomaly alerts and history
- **Network Health**: Overall system health percentage
- **Performance Metrics**: Latency, throughput, packet loss charts

#### User Experience
- **Dark/Light Mode**: Seamless theme switching
- **Responsive Design**: Works on desktop and mobile
- **Real-time Alerts**: In-app notifications for high-risk events
- **Interactive Charts**: Hover effects and detailed tooltips

## 🔧 Configuration

### Environment Variables

#### Backend Configuration
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/sla_prediction
REDIS_URL=redis://localhost:6379
SECRET_KEY=your-secret-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
```

#### Frontend Configuration
```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/telemetry
VITE_MAP_DEFAULT_CENTER_LAT=39.8283
VITE_MAP_DEFAULT_CENTER_LNG=-98.5795
```

### Alert Configuration

#### Telegram Setup
1. Create a bot with @BotFather on Telegram
2. Get the bot token and chat ID
3. Configure in environment variables

#### Email Setup
1. Use Gmail with App Password or SMTP server
2. Configure EMAIL_USER and EMAIL_PASSWORD
3. Set ALERT_EMAIL for notifications

## 📊 Monitoring

### Grafana Dashboards
- **SLA Violations Dashboard**: Real-time violation metrics and trends
- **Network Performance**: Latency, throughput, and packet loss monitoring
- **System Health**: Application and infrastructure metrics
- **ML Model Performance**: Model accuracy and prediction statistics

### Prometheus Metrics
- Application performance metrics from FastAPI
- Database connection and query performance
- System resource utilization (CPU, memory, disk)
- Custom business metrics (SLA violations, anomalies)

### Health Checks
- API endpoint health monitoring
- Database connectivity checks
- Model availability verification
- WebSocket connection status

## 🧪 Testing

### Real-time Simulation
Use the provided Jupyter notebook (`simulation_notebook.ipynb`) to:
- Generate synthetic network telemetry data
- Test real-time prediction capabilities
- Visualize model performance
- Simulate alert scenarios
- Analyze SHAP explanations

### API Testing
```bash
# Health check
curl http://localhost:8000/health

# Prediction test
curl -X POST http://localhost:8000/predict/ \
  -H "Content-Type: application/json" \
  -d '{"bandwidth": 2.0, "throughput": 1.5, "latency": 10.0, "packet_loss": 1.0}'
```

### Frontend Testing
1. Open http://localhost in your browser
2. Test dark/light mode toggle
3. Interact with the network map
4. Check real-time updates in analytics tab
5. Verify node status information

## 🔒 Security

### Production Security Checklist
- [ ] Change default passwords and secret keys
- [ ] Enable HTTPS/TLS with valid certificates
- [ ] Configure firewall rules and security groups
- [ ] Set up VPC/private networks for databases
- [ ] Enable database encryption at rest
- [ ] Configure backup and disaster recovery
- [ ] Set up monitoring and alerting
- [ ] Regular security updates and patches

### Network Security
- Use private subnets for database and Redis
- Configure security groups to restrict access
- Enable VPC flow logs for network monitoring
- Use managed SSL certificates from cloud providers

## 📈 Performance

### Optimization Tips
- **Database**: Create appropriate indexes, use connection pooling
- **Caching**: Leverage Redis for frequently accessed data
- **API**: Use async/await patterns, implement rate limiting
- **Frontend**: Enable gzip compression, optimize bundle size
- **ML Models**: Use model caching, optimize inference time

### Scaling Recommendations
- **Horizontal Scaling**: Increase replica count for backend services
- **Database Scaling**: Use read replicas for read-heavy workloads
- **Caching**: Implement Redis Cluster for high availability
- **CDN**: Use CloudFront or similar for static asset delivery

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Backend development
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend development
cd frontend/sla-dashboard
npm install
npm run dev
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
1. Check the [troubleshooting section](DEPLOYMENT.md#troubleshooting)
2. Review application logs
3. Check monitoring dashboards
4. Create an issue in the repository

## 🙏 Acknowledgments

- **XGBoost** team for the excellent gradient boosting framework
- **FastAPI** for the high-performance web framework
- **React** and **Leaflet.js** communities for frontend technologies
- **SHAP** team for model explainability tools
- **Docker** and cloud providers for deployment infrastructure

---

**Built with ❤️ for network operations teams worldwide**

