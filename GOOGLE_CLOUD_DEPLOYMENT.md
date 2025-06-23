# 🚀 Deploy to Google Cloud Console

This guide will walk you through deploying your Comic Creation Suite on Google Cloud Platform using App Engine.

## Prerequisites

1. **Google Cloud Account** - Sign up at [cloud.google.com](https://cloud.google.com)
2. **Google Cloud SDK** - Install from [cloud.google.com/sdk](https://cloud.google.com/sdk)
3. **Billing Enabled** - Enable billing on your Google Cloud project

## Step 1: Set Up Google Cloud Project

### 1.1 Create a New Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "Select a project" → "New Project"
3. Enter project name: `comic-creation-suite`
4. Click "Create"

### 1.2 Enable Required APIs
In the Google Cloud Console, enable these APIs:

```bash
# Enable App Engine API
gcloud services enable appengine.googleapis.com

# Enable Cloud Storage API
gcloud services enable storage.googleapis.com

# Enable Vertex AI API (for AI features)
gcloud services enable aiplatform.googleapis.com

# Enable Cloud Build API
gcloud services enable cloudbuild.googleapis.com
```

### 1.3 Set Up Service Account
1. Go to "IAM & Admin" → "Service Accounts"
2. Click "Create Service Account"
3. Name: `comic-app-service`
4. Grant these roles:
   - App Engine Deployer
   - Cloud Storage Admin
   - Vertex AI User
5. Create and download the JSON key file

## Step 2: Configure Your App

### 2.1 Update Configuration Files

**Edit `app.yaml`:**
```yaml
runtime: python311
service: comic-creation-suite

env_variables:
  GOOGLE_CLOUD_PROJECT: "your-project-id"  # Replace with your project ID
  GCS_BUCKET_NAME: "comic-creation-data"   # Replace with your bucket name

handlers:
  - url: /.*
    script: auto
    secure: always

automatic_scaling:
  target_cpu_utilization: 0.65
  min_instances: 1
  max_instances: 10
  target_throughput_utilization: 0.6

resources:
  cpu: 1
  memory_gb: 2
  disk_size_gb: 10
```

### 2.2 Create Cloud Storage Bucket
```bash
# Create a bucket for storing comic data
gsutil mb gs://comic-creation-data

# Make bucket publicly readable (optional)
gsutil iam ch allUsers:objectViewer gs://comic-creation-data
```

### 2.3 Set Up Environment Variables
```bash
# Set your project ID
gcloud config set project YOUR_PROJECT_ID

# Set environment variables
gcloud app deploy --set-env-vars GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,GCS_BUCKET_NAME=comic-creation-data
```

## Step 3: Deploy to App Engine

### 3.1 Initialize App Engine
```bash
# Initialize App Engine in your project
gcloud app create --region=us-central1
```

### 3.2 Deploy Your App
```bash
# Deploy to App Engine
gcloud app deploy

# Or deploy with specific configuration
gcloud app deploy app.yaml
```

### 3.3 Verify Deployment
```bash
# View your app
gcloud app browse

# Check app status
gcloud app describe
```

## Step 4: Configure Custom Domain (Optional)

### 4.1 Add Custom Domain
1. Go to App Engine → Settings → Custom Domains
2. Click "Add Custom Domain"
3. Enter your domain name
4. Follow DNS configuration instructions

### 4.2 SSL Certificate
App Engine automatically provisions SSL certificates for custom domains.

## Step 5: Monitor and Manage

### 5.1 View Logs
```bash
# View application logs
gcloud app logs tail

# View specific service logs
gcloud app logs tail -s comic-creation-suite
```

### 5.2 Monitor Performance
1. Go to App Engine → Dashboard
2. View metrics like:
   - Request count
   - Latency
   - Error rate
   - Instance count

### 5.3 Scale Your App
```bash
# Update scaling configuration
gcloud app deploy app.yaml

# Or manually scale
gcloud app versions migrate v1 --min-instances=2 --max-instances=20
```

## Step 6: Set Up CI/CD (Optional)

### 6.1 Using Cloud Build
Create `cloudbuild.yaml`:
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/comic-app', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/comic-app']
  - name: 'gcr.io/cloud-builders/gcloud'
    args: ['app', 'deploy']
```

### 6.2 Connect to GitHub
1. Go to Cloud Build → Triggers
2. Connect your GitHub repository
3. Set up automatic deployment on push

## Troubleshooting

### Common Issues

1. **Deployment Fails**
   ```bash
   # Check logs
   gcloud app logs tail
   
   # Verify configuration
   gcloud app describe
   ```

2. **Import Errors**
   - Ensure all dependencies are in `requirements_gcp.txt`
   - Check Python version compatibility

3. **Permission Errors**
   ```bash
   # Verify service account permissions
   gcloud projects get-iam-policy YOUR_PROJECT_ID
   ```

4. **Memory Issues**
   - Increase memory in `app.yaml`
   - Optimize image processing

### Getting Help

- Check [App Engine documentation](https://cloud.google.com/appengine/docs)
- Review deployment logs
- Use Google Cloud Console monitoring tools

## Cost Optimization

### Free Tier
- App Engine Standard Environment has a generous free tier
- 28 instance hours per day
- 5GB storage
- 1GB outbound data transfer

### Paid Tier Optimization
```yaml
# Optimize for cost in app.yaml
automatic_scaling:
  target_cpu_utilization: 0.8  # Higher utilization
  min_instances: 0              # Scale to zero
  max_instances: 5              # Limit max instances
```

## Security Best Practices

1. **Environment Variables**
   - Store secrets in Google Secret Manager
   - Use environment variables for configuration

2. **Service Account**
   - Use least privilege principle
   - Rotate keys regularly

3. **HTTPS**
   - App Engine automatically provides HTTPS
   - Force HTTPS in your app

## Next Steps

1. **Test your deployed app**
2. **Set up monitoring and alerts**
3. **Configure custom domain**
4. **Set up CI/CD pipeline**
5. **Share your app URL**

---

**Your Comic Creation Suite is now live on Google Cloud!** 🎨📚✨

**App URL**: `https://YOUR_PROJECT_ID.uc.r.appspot.com` 