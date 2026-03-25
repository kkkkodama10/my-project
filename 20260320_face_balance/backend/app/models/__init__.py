from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# 全モデルをここでインポートすることで Alembic の autogenerate が検出できる
from app.models.person import Person  # noqa: E402, F401
from app.models.image import Image, ImageStatus  # noqa: E402, F401
from app.models.feature import Feature  # noqa: E402, F401
from app.models.person_feature import PersonFeature, AggregationMethod  # noqa: E402, F401
from app.models.comparison import Comparison, SimilarityMethod  # noqa: E402, F401
