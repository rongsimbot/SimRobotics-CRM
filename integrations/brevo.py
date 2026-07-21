#!/usr/bin/env python3
"""Brevo Transactional Email Integration for SimRobotics CRM"""
import os, sys, json, requests, html, socket

# Brevo API key - set via environment variable BREVO_API_KEY
BREVO_API_KEY = os.environ.get('BREVO_API_KEY', '')
BREVO_API_URL = 'https://api.brevo.com/v3/smtp/email'

# Force IPv4 for Brevo API (server's IPv6 address not authorized in Brevo IP whitelist)
_orig_getaddrinfo = socket.getaddrinfo
def _getaddrinfo_v4(host, port, family=0, *args, **kwargs):
    return _orig_getaddrinfo(host, port, socket.AF_INET, *args, **kwargs)

def _use_ipv4():
    socket.getaddrinfo = _getaddrinfo_v4

def _restore_dns():
    socket.getaddrinfo = _orig_getaddrinfo

def _sanitize_html(html_content):
    """Ensure HTML is properly formatted for sending via Brevo.
    Unescapes any entity-encoded HTML tags (&lt; &gt;) that may have been
    double-escaped during template editing."""
    if not html_content:
        return html_content
    sanitized = html.unescape(html_content)
    if '&lt;' in sanitized or '&gt;' in sanitized:
        sanitized = html.unescape(sanitized)
    return sanitized

def send_email(sender_name, sender_email, to_email, to_name, subject, html_content, text_content='', cc=None, reply_to=None):
    """Send a single transactional email via Brevo."""
    headers = {
        'accept': 'application/json',
        'api-key': BREVO_API_KEY,
        'content-type': 'application/json'
    }
    payload = {
        'sender': {'name': sender_name, 'email': sender_email},
        'to': [{'email': to_email, 'name': to_name}],
        'subject': subject,
        'htmlContent': html_content,
    }
    if text_content:
        payload['textContent'] = text_content
    if cc:
        payload['cc'] = [{'email': e} for e in (cc if isinstance(cc, list) else [cc])]
    if reply_to:
        payload['replyTo'] = {'email': reply_to}
    
    _use_ipv4()
    try:
        resp = requests.post(BREVO_API_URL, headers=headers, json=payload)
    finally:
        _restore_dns()
    data = resp.json()
    if resp.status_code == 201:
        return {'success': True, 'message_id': data.get('messageId', '')}
    else:
        return {'success': False, 'error': data.get('message', str(resp.status_code)), 'details': data}

def send_batch(sender_name, sender_email, recipients, subject_template, html_template, text_template='', cc=None):
    """Send personalized emails via Brevo batch API."""
    _use_ipv4()
    try:
        results = _send_batch_inner(sender_name, sender_email, recipients, subject_template, html_template, text_template, cc)
    finally:
        _restore_dns()
    return results

def _send_batch_inner(sender_name, sender_email, recipients, subject_template, html_template, text_template='', cc=None):
    results = []
    for i, r in enumerate(recipients):
        first = r.get('first_name', '')
        last = r.get('last_name', '')
        company = r.get('company', '')
        full_name = f"{first} {last}".strip()
        
        subject = subject_template.replace('{first_name}', first)
        subject = subject.replace('{last_name}', last)
        subject = subject.replace('{company}', company)
        
        html = html_template.replace('{first_name}', first)
        html = html.replace('{last_name}', last)
        html = html.replace('{company}', company)
        
        text = ''
        if text_template:
            text = text_template.replace('{first_name}', first)
            text = text.replace('{last_name}', last)
            text = text.replace('{company}', company)
        
        result = send_email(sender_name, sender_email, r['email'], full_name, subject, _sanitize_html(html), text, cc)
        result['email'] = r['email']
        result['contact_name'] = full_name
        results.append(result)
        
        status = '✓' if result['success'] else '✗'
        print(f"  [{i+1}/{len(recipients)}] {status} {r['email']} - {full_name}")
    
    return results

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'help'
    if cmd == 'test':
        result = send_email(
            'Ronnie Gaines', 'rong@simrobotics.com',
            sys.argv[2] if len(sys.argv) > 2 else 'rong@simrobotics.com',
            sys.argv[3] if len(sys.argv) > 3 else 'Ronnie Gaines',
            'Brevo CR Integration Test',
            '<html><body><h2>SimRobotics CRM Campaign System</h2><p>Brevo integration is live.</p></body></html>'
        )
        print(json.dumps(result, indent=2))
    elif cmd == 'account':
        _use_ipv4()
        try:
            resp = requests.get('https://api.brevo.com/v3/account', headers={'api-key': BREVO_API_KEY})
            print(json.dumps(resp.json(), indent=2))
        finally:
            _restore_dns()
    else:
        print("Usage: python3 brevo.py [test <email> [name]] | account")
