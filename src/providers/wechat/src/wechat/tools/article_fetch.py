from pydantic import BaseModel, HttpUrl, Field, ValidationError

from mcp_server.core.errors import ERROR_INVALID_INPUT
from mcp_server.core.response import fail_error


class ArticleFetchIn(BaseModel):
    url: HttpUrl
    timeout: int = Field(default=10, ge=1, le=60)


def article_fetch(ctx, payload: dict):
    try:
        data = ArticleFetchIn.model_validate(payload)
    except ValidationError as e:
        return fail_error(ERROR_INVALID_INPUT, str(e))

    resp = ctx.http.get(str(data.url), timeout=data.timeout)
    return {"status": resp.status_code}
