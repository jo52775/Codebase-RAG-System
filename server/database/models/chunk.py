from database.database import Base
from sqlalchemy import Integer, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
import uuid
from pgvector.sqlalchemy import Vector

class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vector: Mapped[list[float]] = mapped_column(Vector(1024), nullable=False)
    raw_code_text: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    start_line: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_line: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    entity_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    code_repository: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __table_args__ = (
        Index(
            "ix_code_chunks_vector",
            vector,
            postgresql_using="hnsw",
            postgresql_ops={"vector": "vector_cosine_ops"},
        ),
    )