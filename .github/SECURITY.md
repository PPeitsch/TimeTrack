# Security Policy for TimeTrack

## Supported Versions

Only the latest release receives security fixes.

| Version        | Supported |
| -------------- | --------- |
| Latest release | Yes       |
| Older          | No        |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, report them privately through
[GitHub's private vulnerability reporting](https://github.com/PPeitsch/TimeTrack/security/advisories/new)
or by email to pablo.peitsch@gmail.com.

You should receive a response within a few days. Please include:

* Type of issue
* Location of affected code
* Steps to reproduce
* Potential impact
* Possible solutions if you have any

## Security Practices

- Every page and API requires a login; forms and state-changing requests are protected
  against CSRF, and failed logins are rate limited.
- The app refuses to start without a `SECRET_KEY` outside debug mode, and never runs the
  Werkzeug debugger unless `FLASK_DEBUG=1`.
- Session cookies are `HttpOnly` and `SameSite=Lax`; set `SESSION_COOKIE_SECURE=true` behind
  HTTPS.
- Uploaded files are size-limited and deleted after import.
- Dependencies are pinned in `requirements.txt`.

When self-hosting, put TimeTrack behind HTTPS and keep `DEMO_MODE` off unless the instance
is meant to be public.

## Acknowledgments

We're grateful to those who report vulnerabilities responsibly. We will acknowledge your contribution (with your permission) in our release notes.
