# SendGrid Setup Guide

This guide will help you set up SendGrid for email notifications in the Utah Cannabis Aggregator application.

## Step 1: Create SendGrid Account

1. Go to https://signup.sendgrid.com/
2. Click "Start for Free"
3. Fill out the registration form:
   - Email address
   - Password
   - Username
4. Verify your email address (check your inbox for verification email)

## Step 2: Complete Account Setup

1. Log in to your SendGrid dashboard
2. Complete the "Get Started" wizard:
   - Select your email sending goal: "Transactional Email"
   - Describe your use case: "Product alerts and notifications"
   - Skip integration for now (we'll configure it manually)

## Step 3: Create API Key

1. In the SendGrid dashboard, navigate to **Settings** → **API Keys**
2. Click "Create API Key" button
3. Configure the API key:
   - **API Key Name**: `Utah Cannabis Aggregator - Alerts`
   - **API Key Permissions**: Select "Full Access" or "Mail Send" (recommended)
4. Click "Create & View"
5. **IMPORTANT**: Copy the API key immediately - it will only be shown once!
   - It will look like: `SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

## Step 4: Add API Key to Backend

1. Open `backend/.env` file
2. Add or update the following line:
   ```
   SENDGRID_API_KEY=SG.your-actual-api-key-here
   ```
3. Save the file

## Step 5: Verify Sender Identity

SendGrid requires sender verification to prevent spam:

1. In SendGrid dashboard, go to **Settings** → **Sender Authentication**
2. Click "Verify a Single Sender"
3. Fill out the form:
   - **From Name**: `Utah Cannabis Aggregator`
   - **From Email Address**: Use a real email you own (e.g., `alerts@yourdomain.com` or your personal email for testing)
   - **Reply To**: Same as from email
   - **Company Address**: Your address
   - **Nickname**: `Cannabis Alerts`
4. Click "Create"
5. Check your email and click the verification link
6. Update `backend/.env` with the verified email:
   ```
   NOTIFICATION_EMAIL_SENDER=alerts@yourdomain.com
   ```

## Step 6: Test Email Sending

1. Start the backend server:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. Test the email service with a simple Python script:
   ```python
   # test_email.py
   import os
   from sendgrid import SendGridAPIClient
   from sendgrid.helpers.mail import Mail

   message = Mail(
       from_email=os.getenv('NOTIFICATION_EMAIL_SENDER'),
       to_emails='your-email@example.com',  # Replace with your email
       subject='Test Email from Utah Cannabis Aggregator',
       html_content='<strong>This is a test email!</strong>'
   )

   try:
       sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
       response = sg.send(message)
       print(f"Email sent! Status code: {response.status_code}")
   except Exception as e:
       print(f"Error: {e}")
   ```

3. Run the test:
   ```bash
   python test_email.py
   ```

4. Check your inbox for the test email

## Step 7: Configure Alert Frequency

The alert checker runs on a schedule. Configure the interval in `backend/.env`:

```
# Check for alerts every 1 hour (default)
ALERT_CHECK_INTERVAL_HOURS=1

# For testing, you can set it to check more frequently (every 15 minutes):
ALERT_CHECK_INTERVAL_HOURS=0.25
```

## Step 8: Start Alert Scheduler

The alert scheduler needs to be started when the application starts. Add this to your backend startup:

```python
# In backend/main.py or startup script
from services.scheduler import start_alert_scheduler

# Start the alert scheduler
alert_scheduler = start_alert_scheduler()
```

## Free Tier Limits

SendGrid Free Plan includes:
- **100 emails per day**
- All email types (marketing and transactional)
- Basic email analytics
- Email API access

This is sufficient for testing and small-scale deployment. For production:
- Monitor your email usage in SendGrid dashboard
- Upgrade to a paid plan if you exceed 100 emails/day
- Consider implementing daily digest emails to reduce email volume

## Troubleshooting

### Error: "The from email does not contain a valid address"
- Make sure you've verified your sender email in SendGrid
- Check that `NOTIFICATION_EMAIL_SENDER` in `.env` matches the verified email

### Error: "Permission denied"
- Your API key may not have Mail Send permissions
- Create a new API key with "Mail Send" or "Full Access" permissions

### Emails not being sent
1. Check backend logs for errors
2. Verify `SENDGRID_API_KEY` is set correctly in `.env`
3. Check SendGrid dashboard → Activity for delivery status
4. Make sure alert scheduler is running

### Emails going to spam
- Complete sender authentication (SPF, DKIM) in SendGrid dashboard
- Use a custom domain instead of personal email
- Avoid spam trigger words in subject lines

## Production Recommendations

1. **Use a custom domain**: Set up `alerts@yourdomain.com` instead of personal email
2. **Enable Domain Authentication**: In SendGrid → Settings → Sender Authentication → Authenticate Your Domain
3. **Monitor email delivery**: Check SendGrid Activity Feed regularly
4. **Implement unsubscribe**: Add unsubscribe link to emails (required for compliance)
5. **Rate limiting**: Consider implementing rate limits to prevent email spam
6. **Upgrade plan**: If you have more than 100 users or frequent alerts

## Support

- SendGrid Documentation: https://docs.sendgrid.com/
- SendGrid Support: https://support.sendgrid.com/
- API Reference: https://docs.sendgrid.com/api-reference/mail-send/mail-send

---

**Last Updated**: January 25, 2026
