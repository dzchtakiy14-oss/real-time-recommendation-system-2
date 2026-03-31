from pydantic import BaseModel 
from typing import List 

#=======================
# Recommendations Models
#=======================
class ItemRecommended(BaseModel):
    item_id: int 
    title: str

class ResponseRecommendations(BaseModel):
    recommendations: List[ItemRecommended]

class RequestRecommendations(BaseModel):
    user_id: int


#=======================
# Interactions Models
#=======================
class RequestInteractions(BaseModel):
    user_id: int
    item_id: int 