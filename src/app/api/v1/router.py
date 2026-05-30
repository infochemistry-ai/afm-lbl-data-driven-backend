from fastapi import APIRouter

from app.api.v1 import experiments, health, polyelectrolytes, samples

router = APIRouter()
router.include_router(health.router)
router.include_router(polyelectrolytes.router)
router.include_router(experiments.router)
router.include_router(samples.router)
