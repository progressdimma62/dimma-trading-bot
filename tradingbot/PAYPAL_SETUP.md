# PayPal Integration Setup Guide

## Overview
Your Progress Trading Bot now supports PayPal deposits and withdrawals. Follow these steps to enable real money transfers.

## Quick Setup

### 1. Get PayPal Developer Credentials

1. Visit [PayPal Developer Portal](https://developer.paypal.com)
2. Log in with your PayPal account (create one if needed)
3. Go to **Apps & Credentials** → Select **Sandbox** tab
4. Under "Sandbox Business Account", find your **Client ID** and **Secret**
5. Copy these credentials

### 2. Set Environment Variables (Windows)

**Option A: Permanent (Recommended)**
1. Press `Windows Key + X` → Select "System"
2. Click "Advanced system settings" → "Environment Variables"
3. Click "New" under "User variables"
4. Add these variables:
   - **Variable name:** `PAYPAL_CLIENT_ID`
   - **Variable value:** Your Client ID from step 1
5. Click "New" again and add:
   - **Variable name:** `PAYPAL_CLIENT_SECRET`
   - **Variable value:** Your Secret from step 1
6. Click OK and restart your terminal/IDE

**Option B: Temporary (For Testing)**
Run this in PowerShell before starting the app:
```powershell
$env:PAYPAL_CLIENT_ID = "YOUR_CLIENT_ID_HERE"
$env:PAYPAL_CLIENT_SECRET = "YOUR_CLIENT_SECRET_HERE"
```

### 3. Start the App
```bash
python app.py
```

## Using PayPal Features

### Deposit via PayPal
1. Log in to your trading bot
2. Go to Dashboard → Account Management
3. Enter amount and click **PayPal Deposit**
4. You'll be redirected to PayPal to approve the payment
5. Once approved, funds are automatically added to your account

### Withdraw to PayPal
1. Go to Dashboard → Account Management
2. Enter amount and your PayPal email address
3. Click **Withdraw to PayPal**
4. Funds will be transferred to your PayPal account

## Important Notes

✅ **Sandbox Mode**: Currently set to sandbox for testing  
✅ **No Real Transactions**: Sandbox mode uses test accounts  
✅ **Test Accounts**: Available in PayPal Developer Portal  

## Switching to Production (LIVE)

When you're ready for real money:

1. Get **Live** credentials from PayPal Developer Portal
2. Set the environment variables to your Live credentials
3. In `app.py`, change line 18:
   ```python
   'mode': 'live',  # Change from 'sandbox' to 'live'
   ```

⚠️ **WARNING**: Live mode will process REAL money transfers!

## Troubleshooting

**"Payment creation failed"**
- Check that PayPal credentials are set correctly
- Verify you're using Sandbox mode for testing
- Check your PayPal Developer Portal for any account issues

**"Insufficient balance error"**
- Make sure you have enough funds in your trading bot account
- For withdrawals, ensure your PayPal email is correct

**"Connection refused"**
- Verify PayPal API is accessible (check internet connection)
- Confirm your PayPal account is in good standing

## API Endpoints

Your app now includes these PayPal endpoints:

- `POST /api/paypal_deposit` - Create PayPal payment
- `GET /paypal_return` - Handle PayPal approval
- `GET /paypal_cancel` - Handle payment cancellation
- `POST /api/paypal_withdraw` - Create payout to PayPal

## Security Notes

- ✅ Credentials stored in environment variables (not in code)
- ✅ PayPal handles PCI compliance
- ✅ Never share your Secret key
- ✅ Always use HTTPS in production

## Support

For PayPal API documentation: https://developer.paypal.com/docs/api/
For issues with the trading bot: Check the logs

---
**Ready to go!** Your bot now supports real money transfers via PayPal.
