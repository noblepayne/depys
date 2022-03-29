import fastapi.responses

import depys.utils


router = depys.utils.make_router_dep(prefix="/async")


@router.get("/get_ip", response_class=fastapi.responses.Response)
async def async_route(asyncsession=depys.utils.Depends()):
    return (await asyncsession.get("https://icanhazip.com")).text.strip()
