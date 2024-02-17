from ninja import NinjaAPI
from ninja.security import SessionAuth

api = NinjaAPI(title="Seeya API", version="1.0.0", auth=SessionAuth(csrf=False))

from post.views import router as post_router
from user.views import router as user_router

api.add_router("user/", user_router)
api.add_router("post/", post_router)

from seeya_server.exceptions import api_exception_response


@api.exception_handler(Exception)
def api_exception_handler(request, exc):
    response, status_code = api_exception_response(request, exc)
    return api.create_response(request, response, status=status_code)
