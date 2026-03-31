import time
from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from latency import compute_latency
from App.models import ResponseRecommendations
from App.models import RequestRecommendations
from App.models import RequestInteractions
from App.servers.saver_interactions import element_preserver
from App.servers.recommendation_engine import update_user_vec
from latency import recording_latency

# ==============
# Create Router
# ==============
router_recommender = APIRouter()


# ===========================
# Create Recommender End-Point
# ===========================
@router_recommender.post("/recommender", response_model=ResponseRecommendations)
async def Recommender(req: RequestRecommendations):
    start = time.perf_counter()
    recommendations = update_user_vec(req.user_id)
    duration = time.perf_counter() - start
    key = "latency:recommender:function"
    recording_latency(duration, key)
    return {"recommendations": recommendations}


# ===================================
# Create Interactions Saver End-Point
# ===================================
@router_recommender.post("/saver_interactions")
async def interactions_saver(inter: RequestInteractions):
    start_time = float(time.perf_counter())

    element_preserver(inter.user_id, inter.item_id)
    duration = float(time.perf_counter()) - start_time
    key = "latency:saver_interaction"
    recording_latency(duration, key)
    return {"message": "success"}


# Monitoring
@router_recommender.get("/latency")
async def get_latency():
    rec_p50, rec_p95, rec_p99, int_p50, int_p95, int_p99 = compute_latency()
    return {
        "rec_p50": rec_p50,
        "rec_p95": rec_p95,
        "rec_p99": rec_p99,
        "int_p50": int_p50,
        "int_p95": int_p95,
        "int_p99": int_p99,
    }
