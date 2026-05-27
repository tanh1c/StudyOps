import httpx
from fastapi import APIRouter, HTTPException

from studyops_core.adapters.ninerouter import NineRouterAdapter

router = APIRouter(prefix='/router', tags=['router'])


def get_router_adapter():
    return NineRouterAdapter()


@router.get('/models')
def list_router_models():
    try:
        return {'models': get_router_adapter().list_model_groups()}
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                'status': 'unavailable',
                'code': exc.response.status_code,
                'message': NineRouterAdapter._error_detail(exc.response),
            },
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail={'status': 'unavailable', 'message': str(exc)},
        ) from exc
