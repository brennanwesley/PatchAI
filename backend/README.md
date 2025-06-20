# PatchAI Backend

## 🚀 Deployment Status: Docker Setup
**Last Updated: 2025-06-20**  
**Current Setup:** Docker-based deployment for consistent environments

## 📋 Project Overview
A FastAPI backend that provides chat functionality with OpenAI integration, containerized with Docker for reliable deployment.

## 🛠 Current Configuration

### Python Version
- **Required:** Python 3.11.10 (specified in `runtime.txt`)
- **Issue:** Render may still be defaulting to Python 3.13

### Key Dependencies
```
fastapi==0.95.2
uvicorn[standard]==0.24.0
openai==1.6.1
pydantic==1.10.13
python-dotenv==1.0.0
```

## 🔍 Current Issues

### 1. Python Version Mismatch
- **Problem:** Render might be ignoring `runtime.txt` and using Python 3.13
- **Error:** `TypeError: ForwardRef._evaluate() missing 1 required positional argument: 'globalns'`
- **Impact:** Backend fails to start on Render

### 2. Deployment Configuration
- `render.yaml` has been removed to prevent conflicts
- Using `runtime.txt` for Python version control
- Build command: `pip install --upgrade pip && pip install -r requirements.txt`
- Start command: `uvicorn main:app --host=0.0.0.0 --port=$PORT`

## ✅ What's Working
- Local development environment
- Core `/prompt` endpoint with OpenAI integration
- Basic error handling and logging
- CORS middleware for frontend connectivity

## 🔄 Next Steps (MANDATORY)

### 1. Fix Python Version Enforcement
- [ ] Verify Render is using Python 3.11.10 in build logs
- [ ] Consider using a `Dockerfile` for strict version control

### 2. Test Deployment
- [ ] Clear Render build cache
- [ ] Manually trigger deploy after cache clear
- [ ] Check build logs for Python version and dependency resolution

### 3. Verify Endpoints
- [ ] Test `/` - Health check
- [ ] Test `/docs` - OpenAPI documentation
- [ ] Test `/prompt` - OpenAI integration

## 🚀 Deployment Instructions

### 1. Prerequisites
- Docker installed on your development machine
- Docker Hub account (for pushing images, optional)
- Render account with Docker support

### 2. Environment Variables (Set in Render Dashboard)
```
OPENAI_API_KEY=your_openai_key
PORT=8000
```

### 3. Local Development with Docker

1. **Build the Docker image**
   ```bash
   docker build -t patchai-backend .
   ```

2. **Run the container locally**
   ```bash
   docker run -p 8000:8000 -e OPENAI_API_KEY=your_key_here patchai-backend
   ```

### 4. Deployment to Render

1. **Push your code to GitHub**
   ```bash
   git add .
   git commit -m "Add Docker support"
   git push origin main
   ```

2. **In Render Dashboard**:
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Configure the service:
     - Name: patchai-backend
     - Region: Choose closest to you
     - Branch: main
     - Runtime: Docker
     - Build Command: (leave empty, Dockerfile will be used)
     - Start Command: (leave empty, CMD in Dockerfile will be used)
     - Environment Variables:
       - `OPENAI_API_KEY`: your_openai_key
       - `PORT`: 8000
   - Click "Create Web Service"

## 📝 Important Notes
- **DO NOT** upgrade Python beyond 3.11.10 until Pydantic 2.x compatibility is confirmed
- **DO NOT** add `render.yaml` back unless absolutely necessary
- **ALWAYS** check build logs for Python version and dependency warnings

## 🔧 Troubleshooting

### Common Issues

1. **Docker Build Failures**
   - Ensure Docker is running on your machine
   - Check for network connectivity during build
   - Run `docker system prune` if you encounter cache issues

2. **Port Conflicts**
   - If port 8000 is in use, change the port in the `docker run` command
   - Example: `docker run -p 8001:8000 ...` to use port 8001

3. **Environment Variables**
   - Ensure all required environment variables are set
   - Check for typos in variable names

## 📞 Support
For assistance, please open an issue in the GitHub repository or contact the development team.
## 🛠 Development Setup

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/brennanwesley/PatchAI.git
   cd PatchAI/backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys
   ```

5. **Run the development server**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Access the API**
   - Interactive docs: http://localhost:8000/docs
   - API base URL: http://localhost:8000

## 🔄 Troubleshooting

### Common Issues

1. **Python Version Mismatch**
   - Ensure you're using Python 3.11.10
   - Check with: `python --version`
   - If needed, install Python 3.11.10 using pyenv or from python.org

2. **Dependency Conflicts**
   - Delete `venv` and reinstall dependencies if you encounter conflicts
   - Ensure no global packages are conflicting with the virtual environment

3. **Render Deployment Issues**
   - Always check build logs in Render dashboard
   - Look for Python version being used
   - Check for dependency resolution errors

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- OpenAI API integration
- Deployed on [Render](https://render.com/)
