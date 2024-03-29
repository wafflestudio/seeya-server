import logging
import base64
import io
from PIL import Image

from openai import AsyncClient
from openai.types.chat import ChatCompletionChunk

from django.conf import settings
from asgiref.sync import sync_to_async
from challenge.models import Challenge, ChallengeStatus

logger = logging.getLogger(__name__)


def encode_image_to_base64(image: Image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()


def convert_to_base64(image_bytes: bytes, resize: int = 512):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image = image.resize((resize, resize))
    return encode_image_to_base64(image)


async def evaluate_challenge(
    challenge_id: int, image_1_bytes: bytes, image_2_bytes: bytes
):
    async_client = AsyncClient(api_key=settings.OPENAI_API_KEY)

    RESIZING_SIZE = 512
    base64_image_1 = convert_to_base64(image_1_bytes, resize=RESIZING_SIZE)
    base64_image_2 = convert_to_base64(image_2_bytes, resize=RESIZING_SIZE)

    v2 = f"""describe 2 image of place or object in college campus. think about detailed analysis of place and object, background information of each image, but do not write the description to output.
Them measure similarity (in integer, range from 0 to 100) of 2 images. 
Similaity should be measured by following priority.
1. same place or object
2. same background
Time, weather, small objects, and people can be ignored if images are representing same place or object.
show output similarity after `similarity:`. after that, add 2~3 sentence description of second image's characteristic and reasoning for the similarity after `result:`. do not mention `두 번째` in output. response should use friendly, casual tone, and use `~해요`체.
    """

    def image_dict(encoded_image, resize: int = 768):
        return {"image": encoded_image, "resize": resize}

    PROMPT_MESSAGES = [
        {
            "role": "user",
            "content": [
                v2,
                image_dict(base64_image_1, resize=RESIZING_SIZE),
                image_dict(base64_image_2, resize=RESIZING_SIZE),
            ],
        }
    ]
    params = {
        "model": "gpt-4-vision-preview",
        "messages": PROMPT_MESSAGES,
        "max_tokens": 500,
        "stream": True,
    }

    subscription = await async_client.chat.completions.create(**params)

    answer = ""
    async for chunk in subscription:
        chunk: ChatCompletionChunk
        try:
            answer_delta = chunk.choices[0].delta.content
            if answer_delta is not None:
                answer += answer_delta
        except Exception as e:
            raise e
        else:
            if answer_delta:
                yield answer_delta

    try:
        similarity = int(answer.split("similarity:")[1].split("result:")[0].strip())
        result = answer.split("result:")[1].strip()
    except Exception as e:
        similarity = 0
        result = "유사도를 측정할 수 없어요."

    logger.info(
        f"challenge_id: {challenge_id}, similarity: {similarity}, result: {result}"
    )

    await sync_to_async(save_challenge_result)(
        challenge_id=challenge_id, similarity=similarity, result=result
    )


def save_challenge_result(challenge_id: int, similarity: int, result: str):
    try:
        challenge = Challenge.objects.get(id=challenge_id)
        challenge.similarity = similarity
        challenge.result = result
        challenge.status = ChallengeStatus.COMPLETED
        challenge.save()
    except Exception as e:
        import traceback

        traceback.print_exc()
        print(e)
