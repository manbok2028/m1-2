from fastapi import APIRouter, HTTPException, status

from app.dependencies import repository
from app.schemas import DataCreate, DataRecord, DataSummary, DataUpdate, StatisticsResponse
from app.services.analysis import build_summary, monthly_average

router = APIRouter(prefix="/api/data", tags=["data"])


@router.post("", response_model=DataRecord, status_code=status.HTTP_201_CREATED)
def create_data(payload: DataCreate):
    return repository().create_data(payload)


@router.get("", response_model=list[DataRecord])
def list_data():
    return repository().list_data()


@router.get("/summary", response_model=DataSummary)
def data_summary():
    records = repository().list_data()
    if not records:
        raise HTTPException(status_code=404, detail="요약할 거시경제 지표 데이터가 없습니다.")
    return build_summary(records)


@router.get("/statistics", response_model=StatisticsResponse)
def data_statistics():
    records = repository().list_data()
    if not records:
        raise HTTPException(status_code=404, detail="통계를 만들 거시경제 지표 데이터가 없습니다.")
    return {"summary": build_summary(records), "monthly_average": monthly_average(records)}


@router.put("/{record_id}", response_model=DataRecord)
def update_data(record_id: str, payload: DataUpdate):
    record = repository().update_data(record_id, payload)
    if record is None:
        raise HTTPException(status_code=404, detail="수정할 데이터를 찾지 못했습니다.")
    return record


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_data(record_id: str):
    if not repository().delete_data(record_id):
        raise HTTPException(status_code=404, detail="삭제할 데이터를 찾지 못했습니다.")
