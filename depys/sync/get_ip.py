import fastapi.responses
import depys.utils


router = depys.utils.make_router_dep(prefix="/sync")


@router.get("/get_ip", response_class=fastapi.responses.Response)
def sync_route(syncsession=depys.utils.Depends()):
    return syncsession.get("https://icanhazip.com").text.strip()
