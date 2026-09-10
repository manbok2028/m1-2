"""Run once after Firebase setup to load the reproducible 120-point seed series."""

from app.core.config import get_settings
from app.schemas import DataCreate
from app.services.repository import FirestoreRepository
from app.services.sample_data import make_sample_records


def main() -> None:
    settings = get_settings()
    if not settings.firebase_credentials:
        raise RuntimeError("Firebase 서비스 계정을 .env에 설정하세요.")
    repository = FirestoreRepository(settings.firebase_credentials)
    if repository.list_data():
        print("data 컬렉션에 이미 데이터가 있어 시드 생성을 건너뜁니다.")
        return
    for item in make_sample_records():
        repository.create_data(DataCreate(**item))
    print("Firestore data 컬렉션에 120건을 저장했습니다.")


if __name__ == "__main__":
    main()
