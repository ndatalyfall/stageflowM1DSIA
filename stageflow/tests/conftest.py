import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.user import User
from app.schemas.user import RoleName

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine():
	"""Cree le moteur de base de donnees de test synchrone en memoire."""
	engine = create_engine(
		TEST_DATABASE_URL,
		connect_args={"check_same_thread": False},
		poolclass=StaticPool,
	)
	yield engine
	engine.dispose()


@pytest.fixture
def db_session(test_engine) -> Session:
	"""Session de base de donnees synchrone isolee pour chaque test."""
	Base.metadata.create_all(bind=test_engine)
	TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, expire_on_commit=False)
	session = TestSessionLocal()
	try:
		yield session
	finally:
		session.close()
		Base.metadata.drop_all(bind=test_engine)


@pytest_asyncio.fixture
async def make_client(db_session: Session):
	"""Factory pour creer des instances AsyncClient distinctes et isolees."""
	clients: list[AsyncClient] = []

	async def _make_client(user: User | None = None) -> AsyncClient:
		def override_get_db():
			try:
				yield db_session
			finally:
				pass

		app.dependency_overrides[get_db] = override_get_db

		headers = {}
		if user:
			token = create_access_token(subject=str(user.id), role=user.role.value)
			headers["Authorization"] = f"Bearer {token}"

		ac = AsyncClient(
			transport=ASGITransport(app=app),
			base_url="http://test",
			headers=headers,
		)
		clients.append(ac)
		return ac

	yield _make_client

	for ac in clients:
		await ac.aclose()
	app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(make_client) -> AsyncClient:
	"""Client HTTP anonyme (sans header d'autorisation)."""
	return await make_client()


def _create_test_user(db: Session, email: str, full_name: str, role: RoleName) -> User:
	"""Helper pour creer un utilisateur en base."""
	user = User(
		email=email,
		full_name=full_name,
		hashed_password=hash_password("password123"),
		role=role,
		is_active=True,
	)
	db.add(user)
	db.commit()
	db.refresh(user)
	return user


@pytest_asyncio.fixture
async def student_user(db_session: Session) -> User:
	"""Creer un etudiant de test."""
	return _create_test_user(db_session, "student@example.com", "Etudiant Test", RoleName.student)


@pytest_asyncio.fixture
async def student_client(make_client, student_user: User) -> AsyncClient:
	"""Client HTTP authentifie en tant qu'etudiant."""
	return await make_client(student_user)


@pytest_asyncio.fixture
async def company_user(db_session: Session) -> User:
	"""Creer une entreprise de test."""
	return _create_test_user(db_session, "company@example.com", "Entreprise Test", RoleName.company)


@pytest_asyncio.fixture
async def company_client(make_client, company_user: User) -> AsyncClient:
	"""Client HTTP authentifie en tant qu'entreprise."""
	return await make_client(company_user)


@pytest_asyncio.fixture
async def manager_user(db_session: Session) -> User:
	"""Creer un responsable pedagogique de test."""
	return _create_test_user(db_session, "manager@example.com", "Manager Test", RoleName.program_manager)


@pytest_asyncio.fixture
async def manager_client(make_client, manager_user: User) -> AsyncClient:
	"""Client HTTP authentifie en tant que responsable pedagogique."""
	return await make_client(manager_user)


@pytest_asyncio.fixture
async def admin_user(db_session: Session) -> User:
	"""Creer un administrateur de test."""
	return _create_test_user(db_session, "admin@example.com", "Admin Test", RoleName.admin)


@pytest_asyncio.fixture
async def admin_client(make_client, admin_user: User) -> AsyncClient:
	"""Client HTTP authentifie en tant qu'administrateur."""
	return await make_client(admin_user)
