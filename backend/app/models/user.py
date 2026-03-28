from typing import Optional, List

from sqlalchemy import String, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    oauth_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    oauth_subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    interviews: Mapped[List["Interview"]] = relationship(
        "Interview",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="Interview.created_at.desc()",
    )

    __table_args__ = (
        Index("idx_user_oauth", "oauth_provider", "oauth_subject"),
        Index("idx_user_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, provider={self.oauth_provider})>"

    @property
    def display_name(self) -> str:
        return self.name or self.email.split("@")[0]

    @property
    def is_oauth_user(self) -> bool:
        return self.oauth_provider is not None

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "email": self.email,
            "name": self.name,
            "display_name": self.display_name,
            "oauth_provider": self.oauth_provider,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def create_from_jwt(cls, email: str, name: str = None, oauth_provider: str = None, oauth_subject: str = None) -> "User":
        return cls(email=email, name=name, oauth_provider=oauth_provider, oauth_subject=oauth_subject, is_active=True)

    def update_from_jwt(self, name: str = None) -> None:
        if name and name != self.name:
            self.name = name
