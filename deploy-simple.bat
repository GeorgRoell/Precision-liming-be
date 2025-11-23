@echo off
echo Starting deployment to Google Cloud Run...
echo This will take 3-5 minutes...
echo.

gcloud run deploy nextfarming-api --source . --region us-central1 --platform managed --allow-unauthenticated --set-secrets="NEXTFARMING_CLIENT_ID=nextfarming-client-id:latest,NEXTFARMING_CLIENT_SECRET=nextfarming-client-secret:latest,SECRET_KEY=server-secret-key:latest" --set-env-vars="ENVIRONMENT=production,NEXTFARMING_REDIRECT_URI=http://localhost:8080/callback,NEXTFARMING_AUTH_BASE=https://test-account-service.nextfarming.dev/realms/account-service/protocol/openid-connect,NEXTFARMING_API_BASE=https://test-farmmanagement.nextfarming.dev/v2,ALLOWED_ORIGINS=*" --memory 512Mi --cpu 1 --min-instances 0 --max-instances 10 --timeout 60

pause
