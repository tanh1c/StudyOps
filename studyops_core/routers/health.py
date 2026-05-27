from fastapi import APIRouter

from studyops_core.adapters.ninerouter import NineRouterAdapter

router = APIRouter()


def get_router_adapter():
    return NineRouterAdapter()


@router.get('/health/services')
def services_health():
    router_health = get_router_adapter().health_check()
    return {
        'studyops_core': 'ok',
        'deeptutor': 'mock',
        'hermes': 'mock',
        'router': router_health['status'],
        'router_detail': router_health,
    }
