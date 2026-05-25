from fastapi import APIRouter

from studyops_core.adapters.mock import MockRouterAdapter

router = APIRouter()


@router.get('/health/services')
def services_health():
    router_status = MockRouterAdapter().health_check()['status']
    return {
        'studyops_core': 'ok',
        'deeptutor': 'mock',
        'hermes': 'mock',
        'router': router_status,
    }
