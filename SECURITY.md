# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it by [creating an issue](../../issues/new) with the label "security" or email the maintainer directly.

**Please do not create public issues for serious security vulnerabilities.**

## Security Measures

### API Keys and Secrets

- All sensitive keys are stored in GitHub Secrets (encrypted at rest)
- Local development uses `.env` files (git-ignored)
- Service role keys used for GitHub Actions (write access)
- Anonymous keys used for local development (read access)

### Access Control

- Supabase Row Level Security (RLS) enabled on all tables
- GitHub Actions secrets only accessible to repository collaborators
- Branch protection rules enforce code review

### Dependencies

- Dependabot alerts enabled for vulnerability scanning
- Regular dependency updates via automated PRs
- Minimal dependency footprint to reduce attack surface

### Data Protection

- All data stored in Supabase (encrypted in transit and at rest)
- No sensitive data logged in GitHub Actions workflows
- Database connection pooling with proper timeout handling

## Secrets Configuration

For GitHub Actions to work, configure these secrets in repository settings:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key (NOT anon key)
- `GEMINI_API_KEY` - Google Gemini API key
- `ELEVENLABS_API_KEY` - ElevenLabs API key (optional)

## Best Practices

1. **Never commit secrets** to version control
2. **Use service role keys** only in secure environments (GitHub Actions)
3. **Rotate keys regularly** and update in GitHub Secrets
4. **Monitor Dependabot alerts** and apply security patches promptly
5. **Review pull requests** before merging to protected branches

## Incident Response

In case of suspected security incident:

1. Revoke potentially compromised keys immediately
2. Rotate all API keys and update GitHub Secrets
3. Review access logs in Supabase dashboard
4. Update this document with lessons learned