from database.database import Base
from sqlalchemy import BigInteger, String, Text, Index, ForeignKey, Computed
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import TSVECTOR
from typing import Optional
import uuid

class ClassModel(Base):
    __tablename__ = "Classes"

    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    semantic_search_vector: Mapped[list[float]] = mapped_column(Vector(1024), nullable=False)
    entity_name: Mapped[str] = mapped_column(String, nullable=False)
    fqn: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    raw_code_text: Mapped[str] = mapped_column(String, nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    skeleton_text: Mapped[str] = mapped_column(Text, nullable=False)
    start_line: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    end_line: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    code_repository: Mapped[str] = mapped_column(String, nullable=False)
    text_search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('english', coalesce(entity_name, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(fqn, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(filename, '')), 'B') || "
            "setweight(to_tsvector('english', coalesce(raw_code_text, '')), 'D')",
            persisted=True,
        ),
        nullable=True,
    )

    functions: Mapped[list["FunctionModel"]] = relationship(
        "FunctionModel", 
        back_populates="parent_class"
    )

    __table_args__ = (
        Index(
            "idx_class_search_vector",
            text_search_vector,
            postgresql_using="gin",
        ),
    )


class FunctionModel(Base):
    __tablename__ = "Functions"

    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4())
    )
    semantic_search_vector: Mapped[list[float]] = mapped_column(Vector(1024), nullable=False)
    entity_name: Mapped[str] = mapped_column(String, nullable=False)
    raw_code_text: Mapped[str] = mapped_column(String, nullable=False)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    entity_fqn: Mapped[str] = mapped_column(String, nullable=False)
    parent_fqn: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    parent_class_fqn: Mapped[Optional[str]] = mapped_column(
        String, 
        ForeignKey("Classes.fqn"), 
        nullable=True
    )
    start_line: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    end_line: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    code_repository: Mapped[str] = mapped_column(String, nullable=False)
    text_search_vector: Mapped[str] = mapped_column(
            TSVECTOR,
            Computed(
                "setweight(to_tsvector('english', coalesce(entity_name, '')), 'A') || "
                "setweight(to_tsvector('english', coalesce(entity_fqn, '')), 'A') || "
                "setweight(to_tsvector('english', coalesce(filename, '')), 'B') || "
                "setweight(to_tsvector('english', coalesce(raw_code_text, '')), 'D')",
                persisted=True,
            ),
            nullable=True,
        )

    parent_class: Mapped[Optional["ClassModel"]] = relationship(
        "ClassModel", 
        back_populates="functions"
    )

    __table_args__ = (
        Index(
            "ix_functions_vector",
            semantic_search_vector,
            postgresql_using="hnsw",
            postgresql_ops={"vector": "vector_cosine_ops"},
        ),
        Index(
            "idx_function_search_vector",
            text_search_vector,
            postgresql_using="gin",
        ),
    )