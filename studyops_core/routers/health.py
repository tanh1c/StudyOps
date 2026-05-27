from fastapi import APIRouter

from studyops_core.adapters.deeptutor import DeepTutorAdapter
from studyops_core.adapters.ninerouter import NineRouterAdapter

router = APIRouter()


def get_router_adapter():
    return NineRouterAdapter()


def get_deeptutor_adapter():
    return DeepTutorAdapter()


@router.get('/health/services')
def services_health():
    router_health = get_router_adapter().health_check()
    deeptutor_health = get_deeptutor_adapter().health_check()
    return {
        'studyops_core': 'ok',
        'deeptutor': deeptutor_health['status'],
        'deeptutor_detail': deeptutor_health,
        'hermes': 'mock',
        'router': router_health['status'],
        'router_detail': router_health,
    }
