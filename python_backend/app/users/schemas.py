from pydantic import BaseModel

class UserResponse(BaseModel):
    id: int
    supabase_uid: str
    email: str
    role: str

    model_config = {"from_attributes": True}
