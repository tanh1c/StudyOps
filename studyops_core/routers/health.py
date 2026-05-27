from fastapi import APIRouter

from studyops_core.adapters.deeptutor import DeepTutorAdapter
from studyops_core.adapters.hermes import HermesAdapter
from studyops_core.adapters.ninerouter import NineRouterAdapter
from studyops_core.config import settings

router = APIRouter()


def get_router_adapter():
    return NineRouterAdapter()


def get_deeptutor_adapter():
    return DeepTutorAdapter()


def get_hermes_adapter():
    return HermesAdapter()


@router.get('/health/services')
def services_health():
    router_health = get_router_adapter().health_check()
    deeptutor_health = get_deeptutor_adapter().health_check()
    hermes_health = get_hermes_adapter().health_check() if settings.hermes_enabled else {'status': 'mock', 'enabled': False}
    return {
        'studyops_core': 'ok',
        'deeptutor': deeptutor_health['status'],
        'deeptutor_detail': deeptutor_health,
        'hermes': hermes_health['status'],
        'hermes_detail': hermes_health,
        'router': router_health['status'],
        'router_detail': router_health,
    }
