# LakBayan Backend - AI Agent Instructions

## Project Overview
**LakBayan** is a Django REST API for Philippine transportation data (terminals, routes, stops). The system uses a hierarchical data model (Region → City → Terminal → Route → RouteStop) with user-contributed data requiring admin verification.

## Architecture & Data Model

### Core Data Hierarchy
```
Region (e.g., Metro Manila)
  └─ City (e.g., Quezon City)
      └─ Terminal (bus/jeepney station with lat/lon)
          └─ Route (e.g., "QC Terminal → Makati" via Jeepney)
              └─ RouteStop (individual stops with fares)
```

**Key Models** ([models.py](api/models.py)):
- **Terminal**: Verified/unverified, indexed by `(latitude, longitude)`, unique constraint enforces no duplicate locations
- **Route**: Links terminal → destination with transport mode; requires `added_by` user tracking
- **RouteStop**: Ordered stops per route; auto-fills lat/lon from linked terminal; manual entry allowed
- **CachedExport**: JSONB storage for fast data export (not real-time queries)
- **ModeOfTransport**: Fixed categories (tricycle, bus, jeepney, etc.) with fare types (fixed/distance-based)

**Verification Pattern**: All user contributions (`verified=False` by default) → require admin approval → trigger cache update

## Authentication & User Contributions

### JWT + Email Verification Flow
1. **Registration** ([RegisterView](api/views.py#L35-L71)): Creates user, sends verification email via django-allauth
2. **Login**: Issues JWT access/refresh tokens (via rest_framework_simplejwt)
3. **Email Requirement**: `@email_verified_required` decorator blocks contribution endpoints until user clicks verification link
4. **Profile Changes**: Email changes trigger re-verification; old email is removed from `EmailAddress` model

**Critical Detail**: Uses django-allauth's `EmailAddress` model (separate from Django's `User.email`). Verify contributions check:
```python
if not request.user.emailaddress_set.filter(verified=True).exists():
    return 403  # Email verification required
```

## Contribution System

### Three Endpoints + Two Composite Endpoints
1. **Single Resource** ([contribute_terminal](api/views.py#L584-L604)): Terminal only
2. **Single Resource** ([contribute_route](api/views.py#L606-L626)): Route only  
3. **Single Resource** ([contribute_route_stop](api/views.py#L628-L640)): Stop only
4. **[contribute_complete_route](api/views.py#L642-L668)**: Route + stops (atomic transaction)
5. **[contribute_all](api/views.py#L670-L699)**: Terminal + route + stops (atomic transaction)

**Pattern**: All save with `verified=False`, set `added_by=request.user`. Composite endpoints use `transaction.atomic()` to ensure all-or-nothing saves.

## Caching System (High-Performance)

### JSONB Cache Strategy
- **Legacy endpoints** ([complete_data_export](api/views.py#L472-L497)): Generate on-demand (slow, ~1s+)
- **Modern endpoints** ([cached_complete_export](api/views.py#L992-L1002)): Instant JSONB retrieval
- **Auto-Update Signal** ([models.py](api/models.py#L228-L247)): When admin verifies terminal/route, background thread triggers `python manage.py update_export_cache` (5-minute cooldown via cache key)
- **Cache Storage**: [CachedExport](api/models.py#L176-L224) model; one row per export type; includes metadata (version, file size, record count)

**Why JSONB**: PostgreSQL JSONB = indexed, queryable JSON; DRF Response serializes Python dicts → JSON automatically

## Code Patterns & Conventions

### Serializer Strategy
- **Read-Only by Default**: Most serializers use `read_only_fields = ['id']` for user-submitted data
- **Nested Serialization**: [RegionSerializer](api/serializers.py) includes nested cities/terminals/routes to enable hierarchical exports
- **Validation in Serializer**: Email/username uniqueness checks in serializer `validate_*` methods, not in views
- **Contribution Serializers**: Separate `*ContributionSerializer` classes (e.g., [TerminalContributionSerializer](api/serializers.py)) to distinguish user input from admin-verified data

### View Patterns
- **Generics + APIView**: Use `generics.ListAPIView`, `generics.RetrieveUpdateAPIView` for standard CRUD
- **Function-Based Views**: Use `@api_view()` + `@permission_classes()` for custom logic (e.g., forgot_password, nearby_terminals)
- **Permission Layering**: 
  - `AllowAny` = public
  - `IsAuthenticated` = must be logged in
  - `IsAdminUser` = must be staff (not used much currently)
  - `@email_verified_required` = custom decorator for contributions

### Query Optimization
- **select_related()**: For ForeignKey fields (e.g., terminal → city → region)
- **prefetch_related()**: For reverse relations (e.g., region → cities → terminals → routes → stops)
- **Database Indexes**: Terminal has indexes on (lat/lon), (verified), (city); RouteStop ordered by stop order

## Development Workflow

### Key Commands
```bash
# Run dev server
python manage.py runserver

# Initialize/update database (create/apply migrations)
python manage.py migrate

# Create superuser (admin)
python manage.py createsuperuser

# Manually refresh cache (when testing verification workflows)
python manage.py update_export_cache

# Run tests (if added)
python manage.py test api
```

### Environment Setup
- **.env required** (via python-dotenv): `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS`
- **Email Backend**: Console-only in DEBUG=True (prints to stdout); production requires Anymail + provider config
- **Database**: Defaults to SQLite; production uses PostgreSQL via `dj-database-url` + Supabase

### Admin Verification Workflow
1. Admin navigates to Django admin (`/admin/`) → Terminal/Route list
2. Marks `verified=True` → signal fires → cache update spawns in background thread
3. Frontend checks `/cached/metadata/` to detect new data version → refreshes UI

## Common Gotchas & Extensions

### Email Verification Issues
- **Allauth Configuration**: `ACCOUNT_EMAIL_VERIFICATION = 'mandatory'` in [settings.py](lakbayan/settings.py); without this, contributions won't be blocked
- **Email Sending**: Console backend (dev) only logs; production requires Anymail setup with provider (Resend, SendGrid, etc.)
- **Custom Adapter**: [account_adapter.py](api/account_adapter.py) may contain custom logic for email handling

### Adding Features
- **New Data Types**: Add model → create serializer → create view/viewset → update URLs ([urls.py](api/urls.py))
- **New Contribution Types**: Follow `@email_verified_required` + transaction.atomic() pattern
- **Geo Queries**: Use bounding box (fast) not real distance; example in [nearby_terminals](api/views.py#L443-L467)
- **Admin-Only Actions**: Check `request.user.is_staff` in views; or use `@permission_classes([IsAdminUser])`

### Cache Invalidation
- **Automatic**: Signal on Terminal/Route verify triggers rebuild
- **Manual**: Admin action in CachedExport changelist (if configured)
- **Cooldown**: 5-minute cache key prevents excessive rebuilds; remove if batch operations needed

## Key Files Reference
| File | Purpose |
|------|---------|
| [views.py](api/views.py) | All API endpoints; auth, contributions, exports |
| [models.py](api/models.py) | Data schema; includes signals for cache auto-update |
| [serializers.py](api/serializers.py) | Input validation & JSON transformation |
| [urls.py](api/urls.py) | Route definitions (45+ endpoints) |
| [settings.py](lakbayan/settings.py) | Django config; allauth, CORS, email |
| [update_export_cache.py](api/management/commands/update_export_cache.py) | Cache rebuilder; called by signal or manual |

