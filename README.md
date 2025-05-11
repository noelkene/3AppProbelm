# AI Manga Storyboard Generator

An AI-powered application that generates manga-style storyboards from text input. The application uses Google's Vertex AI for image generation and text processing.

## Features

- Convert text stories into manga-style panels
- Generate multiple variants for each panel
- Character and background reference management
- Manual selection of preferred variants
- Google Cloud Storage integration for image storage

## Prerequisites

- Python 3.9+
- Google Cloud Platform account
- Vertex AI API enabled
- Cloud Storage bucket
- Cloud Run API enabled

## Local Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd <repo-name>
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Google Cloud authentication:
```bash
gcloud auth application-default login
```

5. Run the application locally:
```bash
streamlit run src/app.py
```

## Deployment to Google Cloud Run

1. Build and push the Docker image:
```bash
gcloud builds submit --tag gcr.io/<your-project-id>/manga-storyboard
```

2. Deploy to Cloud Run:
```bash
gcloud run deploy manga-storyboard \
  --image gcr.io/<your-project-id>/manga-storyboard \
  --platform managed \
  --region <your-region> \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=<your-project-id>"
```

## Environment Variables

- `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID
- `GOOGLE_CLOUD_LOCATION`: Region for Vertex AI (default: us-central1)

## Project Structure

```
.
├── src/
│   ├── app.py              # Main Streamlit application
│   ├── config/
│   │   └── settings.py     # Configuration settings
│   ├── models/
│   │   └── project.py      # Data models
│   └── services/
│       ├── ai_service.py   # Vertex AI integration
│       └── storage_service.py  # Cloud Storage integration
├── Dockerfile
├── requirements.txt
└── README.md
```

## License

MIT License 