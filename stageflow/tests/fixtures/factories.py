import factory
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker

from app.core.security import hash_password
from app.models.application import Application
from app.models.offer import Offer
from app.models.user import User
from app.schemas.application import ApplicationStatus
from app.schemas.offer import OfferStatus
from app.schemas.user import RoleName

fake = Faker("fr_FR")


class UserFactory(SQLAlchemyModelFactory):
	class Meta:
		model = User
		sqlalchemy_session_persistence = "flush"

	email = factory.LazyFunction(lambda: fake.email())
	full_name = factory.LazyFunction(lambda: fake.name())
	hashed_password = factory.LazyFunction(lambda: hash_password("password123"))
	role = RoleName.student
	is_active = True


class OfferFactory(SQLAlchemyModelFactory):
	class Meta:
		model = Offer
		sqlalchemy_session_persistence = "flush"

	company = factory.SubFactory(UserFactory, role=RoleName.company)
	title = factory.LazyFunction(lambda: f"Stage {fake.job()}")
	mission = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=3))
	skills = factory.LazyFunction(lambda: ["Python", "FastAPI", "SQLAlchemy"])
	status = OfferStatus.published


class ApplicationFactory(SQLAlchemyModelFactory):
	class Meta:
		model = Application
		sqlalchemy_session_persistence = "flush"

	student = factory.SubFactory(UserFactory, role=RoleName.student)
	offer = factory.SubFactory(OfferFactory)
	cover_letter = factory.LazyFunction(lambda: fake.paragraph(nb_sentences=4))
	status = ApplicationStatus.pending
