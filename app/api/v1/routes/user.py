from app.api.deps import get_current_organization
from app.db.schemas.organization import OrganizationResponse
from fastapi import APIRouter, Depends

router = APIRouter(
    prefix="/organizations",
    tags=["organizations"],
    dependencies=[Depends(get_current_organization)],
)


@router.get("/me", response_model=OrganizationResponse)
def get_organization_profile(organization=Depends(get_current_organization)) -> OrganizationResponse:
    return OrganizationResponse.from_orm(organization)