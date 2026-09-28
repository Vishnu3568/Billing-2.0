from fastapi import APIRouter, HTTPException, status

router = APIRouter()


@router.post("/login", tags=["Auth"])
def login_placeholder():
    """Placeholder endpoint for future JWT login."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication workflow is not yet implemented in Step 2 foundation."
    )
