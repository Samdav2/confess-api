
from fastapi import APIRouter, Request, status
import logging
from typing import Any, Dict

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/kudi-sms", status_code=status.HTTP_200_OK)
@router.post("/kudi-sms", status_code=status.HTTP_200_OK)
async def kudi_sms_callback(request: Request) -> Dict[str, str]:
    """
    Callback endpoint for Kudi SMS delivery reports.
    Accepts both GET and POST.
    """

    # Log query parameters (usually for GET)
    query_params = dict(request.query_params)
    if query_params:
        logger.info(f"Kudi SMS Callback Query Params: {query_params}")

    # Log body (usually for POST)
    try:
        body = await request.json()
        logger.info(f"Kudi SMS Callback JSON Body: {body}")
    except Exception:
        # Body might be form-data or empty
        try:
            form = await request.form()
            if form:
                 logger.info(f"Kudi SMS Callback Form Data: {form}")
        except Exception:
             pass

    return {"status": "received"}
