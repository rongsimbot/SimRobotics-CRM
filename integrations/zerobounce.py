#!/usr/bin/env python3
"""ZeroBounce Email Validation for SimRobotics CRM"""
import sys, json, requests, time

ZB_API_KEY = '11bd8545466c4a32b99a9446fc28632c'
ZB_VALIDATE_URL = 'https://api.zerobounce.net/v2/validate'
ZB_CREDITS_URL = 'https://api.zerobounce.net/v2/getcredits'

def get_credits():
    resp = requests.get(f'{ZB_CREDITS_URL}?api_key={ZB_API_KEY}')
    return resp.json()

def validate_email(email, ip_address=''):
    """Validate a single email. Returns dict with status, sub_status, etc."""
    params = {'api_key': ZB_API_KEY, 'email': email}
    if ip_address:
        params['ip_address'] = ip_address
    resp = requests.get(ZB_VALIDATE_URL, params=params)
    if resp.status_code == 200:
        return resp.json()
    else:
        return {'address': email, 'status': 'error', 'error': resp.text}

def validate_batch(emails, delay=0.5):
    """Validate a list of emails with rate limiting. Returns list of result dicts."""
    results = []
    for i, email in enumerate(emails):
        try:
            result = validate_email(email)
            result['index'] = i
            results.append(result)
            status_icon = '✓' if result.get('status') == 'valid' else '✗'
            print(f"  [{i+1}/{len(emails)}] {status_icon} {email} → {result.get('status', 'error')}")
            time.sleep(delay)
        except Exception as e:
            results.append({'address': email, 'status': 'error', 'error': str(e)})
            print(f"  [{i+1}/{len(emails)}] ✗ {email} → error: {e}")
    return results

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'help'
    if cmd == 'credits':
        print(json.dumps(get_credits(), indent=2))
    elif cmd == 'validate' and len(sys.argv) > 2:
        print(json.dumps(validate_email(sys.argv[2]), indent=2))
    else:
        print("Usage: python3 zerobounce.py credits | validate <email>")
