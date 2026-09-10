"""Import verified ECOS monthly core series into Firestore without exposing the key."""

from app.core.config import get_settings
from app.schemas import DataCreate
from app.services.ecos import fetch_verified_core_series
from app.services.repository import FirestoreRepository


def main() -> None:
    settings = get_settings()
    if not settings.firebase_service_account_json or not settings.ecos_api_key:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON과 ECOS_API_KEY를 .env에 설정하세요.")
    repository = FirestoreRepository(settings.firebase_service_account_json)
    records = fetch_verified_core_series(settings.ecos_api_key)
    existing_keys = {
        (str(item["date"]), item["indicator"])
        for item in repository.list_data()
    }
    created = 0
    skipped = 0
    for record in records:
        key = (str(record["date"]), record["indicator"])
        if key in existing_keys:
            skipped += 1
            continue
        repository.create_data(DataCreate(**record))
        created += 1
    print(
        "ECOS 월별 관측값 동기화 완료: "
        f"신규 {created}건, 기존 날짜·지표 중복 건너뜀 {skipped}건"
    )


if __name__ == "__main__":
    main()
