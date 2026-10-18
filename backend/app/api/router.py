from fastapi import APIRouter

from app.api import routes_auth, routes_dashboard, routes_health, routes_jobs, routes_matching, routes_resumes

api_router = APIRouter(prefix="/api")
for r in (routes_auth.router, routes_resumes.router, routes_jobs.router, routes_matching.router,
          routes_dashboard.router, routes_health.router):
    api_router.include_router(r)
