from fastapi import APIRouter

from app.api.v1 import experiments, exports, files, health, polyelectrolytes, samples, scans

router = APIRouter()
router.include_router(health.router)
router.include_router(polyelectrolytes.router)
router.include_router(experiments.router)
router.include_router(samples.router)
router.include_router(scans.router)
router.include_router(exports.router)
router.include_router(files.router)
