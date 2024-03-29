import logging
from http import HTTPStatus
from typing import List

from django.db import transaction
from django.http import HttpRequest, StreamingHttpResponse
from ninja import File, Form, Router, UploadedFile

import challenge
from challenge.models import Challenge, ChallengeStatus
from challenge.schemas import ChallengeAcceptSchema, ChallengeSchema
from post.models import Post
from post.schemas import PostWithChallengeInfoSchema, PostWithDistanceSchema
from seeya_server.exceptions import ErrorResponseSchema, SeeyaApiError

logger = logging.getLogger(__name__)


router = Router(tags=["challenge"])


@router.post(
    "",
    response={
        201: ChallengeSchema,
        frozenset((401, 403, 404)): ErrorResponseSchema,
    },
)
def accept_challenge(request: HttpRequest, body: ChallengeAcceptSchema):
    user = request.user
    post_id = body.post_id

    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        raise SeeyaApiError("존재하지 않는 챌린지입니다.", HTTPStatus.NOT_FOUND)

    if post.author == user:
        raise SeeyaApiError(
            "자신의 게시물에는 도전할 수 없습니다.", HTTPStatus.FORBIDDEN
        )

    challenge, created = Challenge.objects.get_or_create(user=user, post=post)

    if not created:
        raise SeeyaApiError("이미 도전 중인 챌린지입니다.", HTTPStatus.FORBIDDEN)

    return HTTPStatus.CREATED, challenge


@router.post(
    "/{int:challenge_id}/submit",
    response={
        200: ChallengeSchema,
        frozenset((403, 404)): ErrorResponseSchema,
    },
)
@transaction.atomic
def submit_challenge(
    request: HttpRequest,
    challenge_id: int,
    image: UploadedFile = File(...),
):
    user = request.user
    challenge = Challenge.objects.filter(id=challenge_id).first()
    if not challenge:
        raise SeeyaApiError("존재하지 않는 챌린지입니다.", HTTPStatus.NOT_FOUND)

    challenge.image = image
    challenge.save()
    post = challenge.post
    post.challenge_count += 1
    post.save()

    return HTTPStatus.OK, challenge


@router.get(
    "/{int:challenge_id}/evaluate",
    auth=None,
)
async def evaluate_challenge(request: HttpRequest, challenge_id: int):
    challenge = (
        await Challenge.objects.filter(id=challenge_id).select_related("post").afirst()
    )
    if not challenge:
        raise SeeyaApiError("존재하지 않는 챌린지입니다.", HTTPStatus.NOT_FOUND)

    post = challenge.post
    post_image = post.image
    challenge_image = challenge.image

    # get image bytes from imagefield
    post_image_bytes = post_image.read()
    challenge_image_bytes = challenge_image.read()

    from challenge.services import evaluate_challenge

    try:
        response = StreamingHttpResponse(
            evaluate_challenge(challenge_id, post_image_bytes, challenge_image_bytes)
        )
    except Exception as e:
        logger.error(e)

        raise SeeyaApiError("오류가 발생했습니다.", HTTPStatus.BAD_REQUEST)
    return response


@router.get(
    "/{int:challenge_id}",
    response={
        200: ChallengeSchema,
        frozenset((404, 403)): ErrorResponseSchema,
    },
)
def get_challenge(request: HttpRequest, challenge_id: int):
    challenge = Challenge.objects.filter(id=challenge_id).first()
    if not challenge:
        raise SeeyaApiError("존재하지 않는 챌린지입니다.", HTTPStatus.NOT_FOUND)
    return challenge


@router.get(
    "",
    response={
        200: List[PostWithChallengeInfoSchema],
        frozenset((404, 403)): ErrorResponseSchema,
    },
)
def list_challenges(request: HttpRequest, latitude: float, longitude: float):
    user = request.user
    posts = (
        Post.filter_with_distance(latitude, longitude, 5000)
        .prefetch_related("accepted_users")
        .order_by("-like_count", "distance")[:8]
    )
    for post in posts:
        post._user = user
    return posts


@router.get(
    "/today",
    response={
        200: PostWithChallengeInfoSchema,
        frozenset((404, 403)): ErrorResponseSchema,
    },
)
def get_today_challenges(request: HttpRequest, latitude: float, longitude: float):
    posts = (
        Post.filter_with_distance(latitude, longitude, 5000)
        .filter(author__is_superuser=True)
        .select_related("author")
    )
    if not posts.exists():
        raise SeeyaApiError("근처에 오늘의 챌린지가 없습니다.", HTTPStatus.NOT_FOUND)
    post = posts.first()
    post._user = request.user
    return post
