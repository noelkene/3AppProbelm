# Google Cloud Platform Authentication Setup

## Create a .env file

Create a file named `.env` in your project root directory with the following content:

```
# Google Cloud Settings
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GCS_BUCKET_NAME=your-bucket-name

# Path to your service account key file
GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-service-account-key.json
```

Replace:
- `your-project-id` with your actual Google Cloud project ID
- `your-bucket-name` with your Google Cloud Storage bucket name
- `/path/to/your-service-account-key.json` with the absolute path to your service account key file

## Getting a Service Account Key

1. Go to the Google Cloud Console: https://console.cloud.google.com/
2. Navigate to "IAM & Admin" > "Service Accounts"
3. Create a new service account or use an existing one
4. Grant the following roles:
   - Storage Admin
   - Vertex AI User
5. Click on the service account and go to the "Keys" tab
6. Add a new key (JSON format)
7. Download the key file to your computer
8. Update the `GOOGLE_APPLICATION_CREDENTIALS` in your `.env` file with the path to this key file

## Alternative: Use Application Default Credentials

If you have the Google Cloud SDK installed:

1. Install the Google Cloud SDK from: https://cloud.google.com/sdk/docs/install-sdk
2. Authenticate using: `gcloud auth application-default login`
3. Set your project: `gcloud config set project your-project-id`

## Required APIs

Make sure the following APIs are enabled in your Google Cloud project:
- Google Cloud Storage API
- Vertex AI API
- Generative AI API

You can enable these APIs in the Google Cloud Console under "APIs & Services" > "Library". 