# Deployment Guide for Manga Storyboard Generator

This guide provides step-by-step instructions for deploying your Streamlit app to various platforms so you can share it with others.

## 🚀 Quick Deploy Options

### Option 1: Streamlit Cloud (Recommended - Free & Easy)

**Step 1: Prepare Your Repository**
1. Make sure your code is in a GitHub repository
2. Ensure you have these files in your root directory:
   - `streamlit_app.py` (main entry point)
   - `requirements.txt`
   - `.streamlit/config.toml`

**Step 2: Deploy to Streamlit Cloud**
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository
5. Set the main file path to: `streamlit_app.py`
6. Click "Deploy"

**Step 3: Configure Environment Variables**
In your Streamlit Cloud app settings, add these environment variables:
```
GOOGLE_APPLICATION_CREDENTIALS_JSON=your_service_account_json_here
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_STORAGE_BUCKET=your_bucket_name
```

**Step 4: Share Your App**
Once deployed, you'll get a URL like: `https://your-app-name.streamlit.app`
Share this link with others!

### Option 2: Heroku (Free Tier Discontinued)

**Step 1: Install Heroku CLI**
```bash
# Download from https://devcenter.heroku.com/articles/heroku-cli
```

**Step 2: Deploy**
```bash
heroku login
heroku create your-app-name
heroku config:set GOOGLE_APPLICATION_CREDENTIALS_JSON="your_service_account_json"
heroku config:set GOOGLE_CLOUD_PROJECT="your_project_id"
heroku config:set GOOGLE_CLOUD_STORAGE_BUCKET="your_bucket_name"
git push heroku main
```

### Option 3: Railway (Alternative to Heroku)

**Step 1: Sign up at [railway.app](https://railway.app)**

**Step 2: Connect your GitHub repository**

**Step 3: Add environment variables in Railway dashboard**

**Step 4: Deploy automatically**

### Option 4: Google Cloud Run

**Step 1: Create Dockerfile**
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Step 2: Deploy to Cloud Run**
```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/manga-generator
gcloud run deploy manga-generator --image gcr.io/YOUR_PROJECT_ID/manga-generator --platform managed
```

## 🔧 Environment Variables Setup

For any deployment platform, you'll need to set these environment variables:

1. **GOOGLE_APPLICATION_CREDENTIALS_JSON**: Your Google Cloud service account JSON (as a string)
2. **GOOGLE_CLOUD_PROJECT**: Your Google Cloud project ID
3. **GOOGLE_CLOUD_STORAGE_BUCKET**: Your GCS bucket name

## 📁 Required Files for Deployment

Make sure these files are in your repository root:
- ✅ `streamlit_app.py` - Main entry point
- ✅ `requirements.txt` - Python dependencies
- ✅ `.streamlit/config.toml` - Streamlit configuration
- ✅ `src/` - Your source code directory
- ✅ `data/` - Data directories (will be created automatically)

## 🛠️ Troubleshooting

### Common Issues:

1. **Import Errors**: Make sure `streamlit_app.py` is in the root directory
2. **Missing Dependencies**: Check that `requirements.txt` includes all packages
3. **Environment Variables**: Ensure all Google Cloud credentials are set correctly
4. **File Paths**: Use relative paths in your code

### Testing Locally Before Deployment:

```bash
streamlit run streamlit_app.py
```

## 🔒 Security Considerations

1. **Never commit your `service_account.json` file**
2. Use environment variables for sensitive data
3. Set up proper IAM permissions in Google Cloud
4. Consider rate limiting for public access

## 📊 Monitoring Your Deployed App

- **Streamlit Cloud**: Built-in analytics dashboard
- **Heroku**: Use `heroku logs --tail`
- **Railway**: Built-in logging dashboard
- **Cloud Run**: Google Cloud Console monitoring

## 🎯 Next Steps After Deployment

1. Test all functionality in the deployed environment
2. Set up custom domain (optional)
3. Configure monitoring and alerts
4. Share your app URL with users!

---

**Need Help?** Check the platform-specific documentation or create an issue in your repository. 