# 🚀 Flawless AgentVerse Deployment on Google Cloud Run

This guide provides a step-by-step, production-ready framework for deploying your Multi-Agent **AgentVerse** platform entirely on **Google Cloud Run** using the **Google Agent Development Kit (ADK)** and **Vertex AI**, completely optimized to avoid quota issues and latency bottlenecks.

---

## 🏗️ Phase 1: Overcoming API Limitations & Quota Constraints

When deploying a multi-agent AI system, the biggest risk is hitting API rate limits (HTTP 429 errors), because Agents iterate and call tools dynamically. We prevent this by architecting natively on Google Cloud:

1. **Leverage Vertex AI Native Integration**:
   - Do NOT use a standard `GOOGLE_API_KEY`. It has extremely strict rate limits.
   - Use `GOOGLE_GENAI_USE_VERTEXAI="TRUE"`. This routes your ADK agents through your Google Cloud project's Vertex AI quota, which scales robustly (and you can freely request higher throughput from the GCP Console).
   
2. **Enable Google Service APIs**:
   You need to enable APIs on the Google Cloud Console. Run:
   ```bash
   gcloud services enable \
     aiplatform.googleapis.com \
     secretmanager.googleapis.com \
     run.googleapis.com \
     cloudbuild.googleapis.com
   ```

3. **Requesting Quota Increases**:
   - Go to **Google Cloud Console > IAM & Admin > Quotas**.
   - Search for **Vertex AI Gemini API** (Requests per minute / Tokens per minute).
   - Click "Edit Quotas" and request higher limits if you expect heavy traffic. (Google automatically grants moderate increases on billing-enabled accounts instantly).

---

## 🔒 Phase 2: Secure Secret Management

Do not hardcode `.json` secret files or API keys in your Docker image.

1. **Create Secrets in Google Secret Manager**:
   ```bash
   gcloud secrets create agentverse-cse-id --replication-policy="automatic"
   echo -n "YOUR_CUSTOM_SEARCH_ENGINE_ID" | gcloud secrets versions add agentverse-cse-id --data-file=-
   ```
   *(Repeat for any other 3rd party API keys, like YouTube or Maps)*

2. **Assign Service Account Permissions**:
   Cloud Run uses the Default Compute Service Account (or a custom one). Give it access to Vertex AI and Secret Manager:
   ```bash
   PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")
   SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
   
   # Grant access to call Gemini models
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:${SERVICE_ACCOUNT}" \
     --role="roles/aiplatform.user"

   # Grant access to read secrets
   gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
     --member="serviceAccount:${SERVICE_ACCOUNT}" \
     --role="roles/secretmanager.secretAccessor"
   ```

---

## 🐳 Phase 3: Creating an Optimized Dockerfile

Create a `Dockerfile` at the root of your project:

```dockerfile
# Use a lightweight python image
FROM python:3.11-slim

# Prevent python from buffering stdout (better logging)
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose the Cloud Run port
EXPOSE 8080

# Command to run the FastAPI app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

Create a `.dockerignore` file:
```dockerignore
venv/
__pycache__/
*.json
.env
.git/
```

---

## ☁️ Phase 4: Deploying to Google Cloud Run

We deploy directly using Google Cloud Build, injecting the Secret Manager variables directly into the Cloud Run environment.

Run the following command replacing `YOUR_PROJECT_ID` accordingly:

```bash
gcloud run deploy agentverse-api \
  --source . \
  --region us-central1 \
  --project YOUR_PROJECT_ID \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 1 \
  --max-instances 10 \
  --set-env-vars="GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1" \
  --set-secrets="GOOGLE_CSE_ID=agentverse-cse-id:latest"
```

### 💡 Why these specific flags?
- `--memory 2Gi` & `--cpu 2`: Multi-agent orchestration requires concurrency and processes heavy text payloads.
- `--min-instances 1`: This **prevents cold starts**. When a user sends a query, the ADK doesn't have to wait 5 seconds to load the Python environment. It stays "warm" keeping latency low.
- `--set-secrets`: Securely pulls your CSE ID (and other keys) from Secret Manager as environment variables during runtime.

---

## 🎯 Finishing Touches for a Top-Tier Submission

1. **Logging & Tracing**: 
   Since we use Cloud Run, any exception thrown in your ADK backend will automatically appear in **Google Cloud Logging**. You can trace exactly which agent failed.
   
2. **Serverless Scaling**: 
   With `--max-instances 10`, if the judges hammer your app with requests, Cloud Run provisions up to 10 parallel containers. You don't have to worry about the backend crashing under load.

3. **No Auth Keys Required for Gemini**:
   Because the Compute Engine Service Account is given `roles/aiplatform.user` and we set `GOOGLE_GENAI_USE_VERTEXAI="TRUE"`, the Agent Development Kit authenticates **magically via Google Cloud IAM**. No leaked `API_KEY` issues, no sudden "quota exceeded" warnings from standard AI Studio keys.
