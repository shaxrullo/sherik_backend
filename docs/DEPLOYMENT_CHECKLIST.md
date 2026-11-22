# Deployment Checklist

Comprehensive checklist for deploying Backend Sherik to production.

## Pre-Deployment (1-2 Days Before)

### Code Review & Testing

- [ ] All code merged to `main` branch
- [ ] All GitHub Actions tests passing
- [ ] Code review approved by at least 1 person
- [ ] No TODO or FIXME comments remaining
- [ ] Security review completed (bandit passed)
- [ ] Performance testing done on large datasets
- [ ] Load testing completed (target: 100+ concurrent users)

### Database

- [ ] All migrations created and tested locally
- [ ] Migration rollback plan documented
- [ ] Database backup strategy confirmed
- [ ] Database indexes optimized
- [ ] Data validation queries prepared

### Dependencies

- [ ] `requirements.txt` updated
- [ ] All new dependencies reviewed for security
- [ ] Version compatibility verified
- [ ] `pip list` checked for unused packages
- [ ] Python version pinned (3.11)

### Documentation

- [ ] README updated with deployment info
- [ ] API documentation up-to-date
- [ ] Configuration documented in `.env.example`
- [ ] Deployment guide exists
- [ ] Runbook created for common issues

---

## Configuration & Secrets (Day Before)

### Environment Variables

- [ ] `.env.example` updated with all required variables
- [ ] All secrets stored securely (not in git)
- [ ] Sensitive data removed from logs
- [ ] `DEBUG=False` configured for production
- [ ] `ALLOWED_HOSTS` correctly set
- [ ] `CSRF_TRUSTED_ORIGINS` configured
- [ ] `SECRET_KEY` rotated (changed from development)
- [ ] Database URL set correctly
- [ ] Redis URL configured
- [ ] Sentry DSN configured
- [ ] Email service credentials set
- [ ] Third-party API keys stored securely

### Security

- [ ] `SECURE_SSL_REDIRECT=True`
- [ ] `SECURE_HSTS_SECONDS=31536000` (1 year)
- [ ] `SESSION_COOKIE_SECURE=True`
- [ ] `CSRF_COOKIE_SECURE=True`
- [ ] `SECURE_BROWSER_XSS_FILTER=True`
- [ ] `SECURE_CONTENT_TYPE_NOSNIFF=True`
- [ ] `X_FRAME_OPTIONS='DENY'`
- [ ] No debug toolbar in production
- [ ] No test users in production database

### Monitoring & Logging

- [ ] Sentry project created and DSN configured
- [ ] Email notifications configured
- [ ] Slack integration set up (optional)
- [ ] Logging levels configured (not too verbose)
- [ ] Log retention policy set

---

## Infrastructure Setup (Render)

### Web Service

- [ ] Service created on Render
- [ ] Region selected (closest to target users)
- [ ] Python version set to 3.11
- [ ] Environment variables added to Render dashboard
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`

### Database

- [ ] PostgreSQL database created
- [ ] Database name, user, password set
- [ ] Database URL added to Render environment
- [ ] Backup schedule configured (daily)
- [ ] Connection pooling enabled
- [ ] Max connections: 10-20

### Redis Cache

- [ ] Redis instance created (if using caching)
- [ ] Redis URL configured
- [ ] Memory size adequate (at least 512MB)
- [ ] Eviction policy: `allkeys-lru`

### Storage (Optional)

- [ ] Supabase bucket created (for media files)
- [ ] Supabase URL and key configured
- [ ] Media folder structure created
- [ ] CORS settings configured for media access
- [ ] CDN enabled (if available)

### DNS & SSL

- [ ] Custom domain configured
- [ ] DNS records updated
- [ ] SSL certificate auto-generated (Render handles)
- [ ] SSL renewal configured
- [ ] Certificate validation passed

---

## Pre-Deployment Testing (2-3 Hours Before)

### Staging Deployment

- [ ] Deploy to staging environment first
- [ ] Staging URL accessible
- [ ] All endpoints tested in staging
- [ ] Database migrations run successfully
- [ ] Static files collected and served
- [ ] Media uploads working
- [ ] Authentication working
- [ ] Email notifications sent successfully

### Health Checks

- [ ] Health endpoint returns 200: `/health/`
- [ ] Readiness endpoint returns 200: `/ready/`
- [ ] Liveness endpoint returns 200: `/alive/`
- [ ] Database connection working
- [ ] Redis connection working
- [ ] API endpoints responding
- [ ] Load balancer health checks passing

### Critical Features Test

- [ ] User registration working
- [ ] User login working
- [ ] Listing creation working
- [ ] Listing search/filtering working
- [ ] Matching algorithm working
- [ ] Favorites adding/removing working
- [ ] Admin panel accessible
- [ ] API documentation accessible

### Browser Testing

- [ ] Chrome latest version
- [ ] Firefox latest version
- [ ] Safari latest version
- [ ] Mobile browsers (iOS, Android)
- [ ] No console errors
- [ ] No network errors
- [ ] Response times acceptable (<2 seconds)

---

## Deployment Day (Execution)

### Pre-Deployment Announcement

- [ ] Notify users of deployment window (if applicable)
- [ ] Set status page to "Maintenance"
- [ ] Prepare rollback plan
- [ ] Team available during deployment
- [ ] Ensure no customers on the system (if possible)

### Deployment Steps

1. **Backup Current State**
   ```bash
   # Take database backup
   pg_dump production_db > backup_$(date +%s).sql
   ```

2. **Stop Services (Graceful)**
   ```bash
   # Render automatically handles zero-downtime deploys
   # But ensure no long-running requests are stuck
   ```

3. **Run Migrations**
   ```bash
   # Connect to Render service
   # Run migrations
   python manage.py migrate --noinput
   ```

4. **Collect Static Files**
   ```bash
   # Already handled by build command on Render
   python manage.py collectstatic --noinput
   ```

5. **Clear Cache** (if needed)
   ```bash
   # Clear Redis cache
   python manage.py shell
   >>> from django.core.cache import cache
   >>> cache.clear()
   ```

6. **Deploy New Code**
   ```bash
   # Push to main branch
   git push origin main
   # Render automatically deploys
   ```

7. **Verify Deployment**
   - [ ] Deployment completed successfully
   - [ ] No deployment errors in logs
   - [ ] Service is running (check status)
   - [ ] Health checks passing

### Post-Deployment Verification (30 minutes)

- [ ] Application is online
- [ ] All endpoints responding
- [ ] Database queries working
- [ ] No error spikes in Sentry
- [ ] Response times normal
- [ ] Load balancer health good
- [ ] All team members confirm system is working
- [ ] Check logs for any warnings/errors

### Rollback Plan

If critical issues found:

```bash
# Option 1: Render deploy previous version
# In Render dashboard:
# 1. Go to Deployments
# 2. Find previous successful deploy
# 3. Click "Redeploy"

# Option 2: Git rollback
git revert <commit-hash>
git push origin main
```

---

## Post-Deployment (Day After)

### Monitoring

- [ ] Monitor error rate (target: <0.1%)
- [ ] Monitor response times (target: <1 second)
- [ ] Monitor CPU usage (target: <70%)
- [ ] Monitor memory usage (target: <80%)
- [ ] Monitor database connections (target: <8/10)
- [ ] Check Sentry for new issues
- [ ] Check logs for warnings
- [ ] Monitor user feedback channels

### Performance Analysis

- [ ] Database query times acceptable
- [ ] API response times acceptable
- [ ] No N+1 query problems
- [ ] Cache hit rate > 50%
- [ ] Matching algorithm performance good
- [ ] Media serving optimized

### User Testing

- [ ] Confirm users can login
- [ ] Confirm users can create listings
- [ ] Confirm matching works
- [ ] Confirm favorites work
- [ ] No new support tickets about bugs

### Documentation Update

- [ ] Update deployment log with:
  - Deployment time
  - Version deployed
  - Databases migrated
  - Key changes
  - Deployment status
- [ ] Document any issues encountered
- [ ] Update runbook if needed

---

## Production Configuration Checklist

### Django Settings

- [ ] `DEBUG = False`
- [ ] `ALLOWED_HOSTS` configured properly
- [ ] `SECURE_SSL_REDIRECT = True`
- [ ] `SECURE_HSTS_SECONDS` set
- [ ] `CSRF_COOKIE_SECURE = True`
- [ ] `SESSION_COOKIE_SECURE = True`
- [ ] `SESSION_COOKIE_HTTPONLY = True`
- [ ] `CSRF_COOKIE_HTTPONLY = True`
- [ ] `SECRET_KEY` changed from default
- [ ] `LOGGING` configured
- [ ] `CACHES` configured for Redis
- [ ] `EMAIL_BACKEND` configured
- [ ] Database connection settings correct
- [ ] `STATIC_ROOT` configured
- [ ] `MEDIA_ROOT` configured

### Environment Variables Checklist

```bash
# Required for production
DEBUG=False
SECRET_KEY=<strong-random-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://host:6379/1
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx
ENVIRONMENT=production

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com (or your provider)
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Storage (Optional - for Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1N...
SUPABASE_BUCKET=media

# Google Auth (Optional)
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com

# Admin
ADMIN_URL=secret-admin-path/
```

---

## Common Issues & Troubleshooting

### Deployment Fails

```bash
# Check deployment logs
# In Render: Logs tab
# Look for syntax errors, missing dependencies, etc.

# Common causes:
# 1. Missing environment variable
# 2. Database migration error
# 3. Missing dependency in requirements.txt
# 4. Python version mismatch
```

### Database Connection Error

```bash
# Check DATABASE_URL format
postgresql://user:password@host:5432/dbname

# Verify credentials are correct
# Check if database exists
# Check firewall/network permissions
```

### Static Files Not Serving

```bash
# Collect static files manually
python manage.py collectstatic --noinput

# Check STATIC_ROOT and STATIC_URL
# Verify WhiteNoise middleware installed
```

### High Error Rate

```bash
# Check Sentry dashboard for error details
# Check application logs
# Check database logs for slow queries
# Monitor for resource exhaustion
```

### Slow Performance

```bash
# Check database query performance
# Check Redis cache hit rate
# Check API response times
# Look for N+1 queries
# Check if database indexes are created
```

---

## Disaster Recovery

### Database Corruption

1. Stop application
2. Restore from latest backup
3. Run migrations
4. Verify data integrity
5. Restart application

### Complete System Failure

1. Provision new infrastructure
2. Restore database from backup
3. Deploy application code
4. Configure environment variables
5. Run migrations
6. Verify system is operational

### Data Loss

1. Contact Render support
2. Restore from backup if available
3. Notify users if data affected
4. Implement data recovery procedures

---

## Post-Mortem

After deployment, create a post-mortem if any issues occurred:

- [ ] What went wrong
- [ ] Root cause analysis
- [ ] How it was resolved
- [ ] Prevention measures
- [ ] Team learnings
- [ ] Update documentation/runbooks

---

## Maintenance Schedule

### Weekly

- [ ] Review error logs
- [ ] Check database size
- [ ] Monitor storage usage
- [ ] Check SSL certificate expiration

### Monthly

- [ ] Database optimization (ANALYZE, VACUUM)
- [ ] Security updates check
- [ ] Dependency updates check
- [ ] Performance review
- [ ] Capacity planning review

### Quarterly

- [ ] Disaster recovery test
- [ ] Security audit
- [ ] Performance optimization review
- [ ] Architecture review

---

## Contacts & Escalation

- **Deployment Manager**: [Name]
- **Backend Lead**: [Name]
- **DevOps/Infrastructure**: [Name]
- **On-Call Support**: [Rotation]

---

## Sign-Off

- [ ] Deployment approved by: ___________
- [ ] Deployed by: ___________
- [ ] Verified by: ___________
- [ ] Date: ___________
- [ ] Time: ___________
- [ ] Environment: Production
- [ ] Version Deployed: ___________
- [ ] Rollback Required: Yes / No

---

## Deployment Log

| Date | Version | Status | Deployed By | Notes |
|------|---------|--------|------------|-------|
| | | | | |
| | | | | |
| | | | | |

---

For support or questions about deployment: [contact info]
