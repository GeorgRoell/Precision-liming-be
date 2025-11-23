# Deploy to Google Cloud Run - Step by Step Guide

This guide will walk you through deploying your NextFarming backend API to Google Cloud Run.

**Estimated time:** 20-30 minutes
**Cost:** Free tier covers your usage (first 2M requests/month free)

---

## Prerequisites

- ✅ Backend working locally (you've already done this!)
- ⏳ Google Cloud account
- ⏳ Google Cloud CLI installed

---

## Step 1: Install Google Cloud CLI (5 minutes)

### For Windows:

**Option A: Download Installer (Recommended)**
1. Visit: https://cloud.google.com/sdk/docs/install
2. Download the Windows installer (GoogleCloudSDKInstaller.exe)
3. Run the installer
4. Check "Start Google Cloud SDK Shell" at the end
5. Follow the initialization prompts

**Option B: Using PowerShell**
```powershell
# Run in PowerShell as Administrator
(New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
& $env:Temp\GoogleCloudSDKInstaller.exe
```

### Verify Installation:
```bash
gcloud --version
```

You should see something like:
```
Google Cloud SDK 458.0.0
...
```

---

## Step 2: Set Up Google Cloud Account (10 minutes)

### A. Create Google Cloud Account (if you don't have one)
1. Go to: https://console.cloud.google.com
2. Sign in with your Google account (or create one)
3. Accept terms of service
4. **New users get $300 free credits for 90 days!**

### B. Enable Billing
1. In Google Cloud Console, go to "Billing"
2. Link a credit/debit card
3. **Don't worry:** Free tier covers your usage, you won't be charged unless you exceed limits

### C. Create a New Project
1. In Google Cloud Console, click project dropdown (top left)
2. Click "New Project"
3. **Project Name:** `nextfarming-backend`
4. **Project ID:** Will be auto-generated (e.g., `nextfarming-backend-123456`)
5. Click "Create"

**Note your Project ID** - you'll need it!

---

## Step 3: Initialize Google Cloud CLI (5 minutes)

Open **Command Prompt** or **PowerShell** and run:

```bash
# Login to Google Cloud
gcloud auth login
```
- Browser will open
- Sign in with your Google account
- Grant permissions

```bash
# Set your project (replace with your actual Project ID)
gcloud config set project nextfarming-backend-123456

# Verify
gcloud config get-value project
```

```bash
# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

This will take 1-2 minutes.

---

## Step 4: Create Secrets in Google Secret Manager (5 minutes)

Your API credentials need to be stored securely. We'll use Google Secret Manager:

```bash
# Navigate to your backend folder
cd C:\Users\georg\nextfarming-backend

# Create secret for NextFarming client secret
echo f4OThVmuwkLt8TCpmrJq3UAv5obzcInI | gcloud secrets create nextfarming-client-secret --data-file=-

# Create secret for your server secret key
echo 0f51a36dc7e3f1f8dcf0ac6df3f3b6552e9126292cae1fde2c9fd3a7c99b8056 | gcloud secrets create server-secret-key --data-file=-

# Create secret for client ID (optional, not sensitive but for consistency)
echo omya | gcloud secrets create nextfarming-client-id --data-file=-
```

Verify secrets were created:
```bash
gcloud secrets list
```

You should see:
```
NAME                          CREATED              REPLICATION_POLICY
nextfarming-client-id         [timestamp]          automatic
nextfarming-client-secret     [timestamp]          automatic
server-secret-key            [timestamp]          automatic
```

---

## Step 5: Deploy to Cloud Run (5-10 minutes)

Now for the exciting part! Deploy your backend:

```bash
# Make sure you're in the backend folder
cd C:\Users\georg\nextfarming-backend

# Deploy to Cloud Run (this will build and deploy in one command!)
gcloud run deploy nextfarming-api \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets="NEXTFARMING_CLIENT_ID=nextfarming-client-id:latest,NEXTFARMING_CLIENT_SECRET=nextfarming-client-secret:latest,SECRET_KEY=server-secret-key:latest" \
  --set-env-vars="ENVIRONMENT=production,NEXTFARMING_REDIRECT_URI=http://localhost:8080/callback,NEXTFARMING_AUTH_BASE=https://test-account-service.nextfarming.dev/realms/account-service/protocol/openid-connect,NEXTFARMING_API_BASE=https://test-farmmanagement.nextfarming.dev/v2,ALLOWED_ORIGINS=*" \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 60
```

**What this does:**
- Builds your code into a Docker container
- Uploads to Google Cloud
- Creates a Cloud Run service
- Links your secrets securely
- Gives you a public URL

**Note for Windows PowerShell/CMD:**
The above command uses backslashes for line continuation (Unix style). In Windows, you may need to:
1. Remove the backslashes and put everything on one line, OR
2. Use PowerShell's backtick (`) instead of backslash (\)

**One-line version for Windows:**
```bash
gcloud run deploy nextfarming-api --source . --region us-central1 --platform managed --allow-unauthenticated --set-secrets="NEXTFARMING_CLIENT_ID=nextfarming-client-id:latest,NEXTFARMING_CLIENT_SECRET=nextfarming-client-secret:latest,SECRET_KEY=server-secret-key:latest" --set-env-vars="ENVIRONMENT=production,NEXTFARMING_REDIRECT_URI=http://localhost:8080/callback,NEXTFARMING_AUTH_BASE=https://test-account-service.nextfarming.dev/realms/account-service/protocol/openid-connect,NEXTFARMING_API_BASE=https://test-farmmanagement.nextfarming.dev/v2,ALLOWED_ORIGINS=*" --memory 512Mi --cpu 1 --min-instances 0 --max-instances 10 --timeout 60
```

### During deployment, you'll see:
```
Building using Dockerfile and deploying container to Cloud Run service [nextfarming-api]
✓ Creating Container Repository
✓ Uploading sources
✓ Building Container - this may take a few minutes
✓ Pushing container to registry
✓ Deploying revision
✓ Routing traffic
Done.
Service [nextfarming-api] revision [nextfarming-api-00001-abc] has been deployed.
Service URL: https://nextfarming-api-xyz123-uc.a.run.app
```

**Copy your Service URL!** This is your production API endpoint.

---

## Step 6: Test Your Deployed API (5 minutes)

Replace `YOUR_SERVICE_URL` with the URL from the previous step:

```bash
# Test health endpoint (no auth required)
curl https://nextfarming-api-xyz123-uc.a.run.app/health

# Test login
curl -X POST "https://nextfarming-api-xyz123-uc.a.run.app/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo123"}'
```

You should get a token back!

### Test with Python Script:

Update `test_api.py` to use your production URL:

```python
# Change this line:
BASE_URL = "https://nextfarming-api-xyz123-uc.a.run.app"  # Your actual URL

# Then run:
python test_api.py
```

### View API Documentation:

Open in browser:
```
https://nextfarming-api-xyz123-uc.a.run.app/docs
```

You'll see your interactive API documentation!

---

## Step 7: View Deployment Details

### In Google Cloud Console:
1. Go to: https://console.cloud.google.com
2. Navigate to: **Cloud Run** (in left menu)
3. Click on your service: **nextfarming-api**

Here you can see:
- **Metrics:** Request count, latency, errors
- **Logs:** Real-time logs of API calls
- **Revisions:** Deployment history
- **YAML:** Service configuration

### View Logs:
```bash
gcloud run logs read nextfarming-api --region us-central1 --limit 50
```

### View Service Details:
```bash
gcloud run services describe nextfarming-api --region us-central1
```

---

## Cost Breakdown

### Free Tier (Included):
- ✅ **2 million requests** per month
- ✅ **360,000 GB-seconds** of memory
- ✅ **180,000 vCPU-seconds** of compute

### For Your App:
Assuming **10,000 requests/month** (generous estimate):
- **Cost:** $0 (well within free tier)

### After Free Tier (if you grow):
- **Requests:** $0.40 per million
- **Memory:** $0.0000025 per GB-second
- **CPU:** $0.00002400 per vCPU-second

**Example:** 100,000 requests/month = **~$0.50/month**

---

## Updating Your Deployment

When you make changes to your code:

```bash
# Simply redeploy (same command as before)
cd C:\Users\georg\nextfarming-backend

gcloud run deploy nextfarming-api --source . --region us-central1
```

Cloud Run will:
- Build new container
- Deploy new version
- Automatically switch traffic (zero downtime!)
- Keep old version as backup

**Rollback if needed:**
```bash
gcloud run services update-traffic nextfarming-api --to-revisions=PREVIOUS_REVISION_NAME=100 --region us-central1
```

---

## Security Best Practices

### ✅ Already Implemented:
- Secrets in Secret Manager (not in code)
- HTTPS enforced automatically
- JWT authentication on endpoints
- Environment variables for config

### Additional (Optional):
1. **Restrict CORS** - Change `ALLOWED_ORIGINS=*` to specific domains
2. **Add Rate Limiting** - Use Cloud Armor (if needed)
3. **Custom Domain** - Map your own domain name
4. **API Key Authentication** - Add API keys for extra security

---

## Troubleshooting

### Issue: Build fails
**Solution:** Check Dockerfile and requirements.txt
```bash
# View build logs
gcloud builds log $(gcloud builds list --limit=1 --format="value(id)")
```

### Issue: Service crashes on startup
**Solution:** Check environment variables and secrets
```bash
# View service logs
gcloud run logs read nextfarming-api --region us-central1 --limit 100
```

### Issue: "Permission denied" errors
**Solution:** Grant Cloud Run service account access to secrets
```bash
gcloud secrets add-iam-policy-binding nextfarming-client-secret \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Issue: Can't access from desktop app
**Solution:** Update CORS settings and ensure URL is correct

---

## Next Steps After Deployment

1. ✅ **Share your API URL** with team members
2. ✅ **Update desktop app** to use production URL instead of localhost
3. ✅ **Set up monitoring** - Enable Cloud Monitoring alerts
4. ✅ **Custom domain** (optional) - Map `api.yourdomain.com`
5. ✅ **Build web frontend** - Connect to your live API

---

## Useful Commands Cheat Sheet

```bash
# View service URL
gcloud run services describe nextfarming-api --region us-central1 --format="value(status.url)"

# View logs (last 50 lines)
gcloud run logs read nextfarming-api --region us-central1 --limit 50

# View logs (live tail)
gcloud run logs tail nextfarming-api --region us-central1

# List all services
gcloud run services list

# Delete service (if needed)
gcloud run services delete nextfarming-api --region us-central1

# Update secrets
echo "new-secret-value" | gcloud secrets versions add nextfarming-client-secret --data-file=-

# View secret value (for debugging)
gcloud secrets versions access latest --secret="nextfarming-client-secret"
```

---

## Support & Resources

- **Google Cloud Documentation:** https://cloud.google.com/run/docs
- **Pricing Calculator:** https://cloud.google.com/products/calculator
- **Support Forum:** https://stackoverflow.com/questions/tagged/google-cloud-run
- **Your API Docs:** `https://YOUR-SERVICE-URL/docs`

---

## Success Checklist

After completing this guide, you should have:

- ✅ Google Cloud account set up
- ✅ gcloud CLI installed and configured
- ✅ Secrets stored in Secret Manager
- ✅ Backend deployed to Cloud Run
- ✅ Live API URL (e.g., `https://nextfarming-api-xyz.run.app`)
- ✅ API documentation accessible online
- ✅ Test API calls working

**Total cost so far:** $0 (using free tier)

---

**Ready to deploy? Start with Step 1!** 🚀

If you get stuck at any step, just let me know the error message and I'll help you fix it.
