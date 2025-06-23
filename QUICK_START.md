# 🚀 Quick Start: Deploy Your Manga Generator

## Option 1: Streamlit Cloud (Easiest - 5 minutes)

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### Step 2: Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click "New app"
4. Select your repository
5. Set main file path: `streamlit_app.py`
6. Click "Deploy"

### Step 3: Add Environment Variables
In your Streamlit Cloud app settings, add:
```
GOOGLE_APPLICATION_CREDENTIALS_JSON=your_service_account_json_string
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_STORAGE_BUCKET=your_bucket_name
```

### Step 4: Share Your App!
Your app will be available at: `https://your-app-name.streamlit.app`

---

## Option 2: Local Testing

### Test Locally First
```bash
streamlit run streamlit_app.py
```

### Docker Local
```bash
docker build -t manga-generator .
docker run -p 8501:8501 manga-generator
```

---

## 🔧 Environment Variables Needed

You'll need these environment variables for Google Cloud:

1. **GOOGLE_APPLICATION_CREDENTIALS_JSON**: Your service account JSON (as a string)
2. **GOOGLE_CLOUD_PROJECT**: Your Google Cloud project ID  
3. **GOOGLE_CLOUD_STORAGE_BUCKET**: Your GCS bucket name

---

## 📁 Files Created for Deployment

- ✅ `streamlit_app.py` - Main entry point
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `Dockerfile` - For containerized deployment
- ✅ `docker-compose.yml` - For local Docker testing
- ✅ `Procfile` - For Heroku deployment
- ✅ `deploy.sh` - Deployment automation script
- ✅ `DEPLOYMENT_GUIDE.md` - Detailed deployment guide

---

## 🎯 Next Steps

1. **Choose your deployment method** (Streamlit Cloud recommended)
2. **Set up your environment variables**
3. **Deploy your app**
4. **Test all functionality**
5. **Share the link with others!**

---

## 🆘 Need Help?

- Check `DEPLOYMENT_GUIDE.md` for detailed instructions
- Run `./deploy.sh` for interactive deployment help
- Test locally first with `streamlit run streamlit_app.py`

**Your app is ready to deploy! 🎉** 