"""
Dependency injection container for clean architecture.
"""
from typing import Callable, TypeVar, Dict, Any, Optional
from functools import lru_cache
import logging

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ..core.settings import Settings
from ..domain.services import (
    IOrganizationDomainService,
    IContractAnalysisDomainService,
    ISecurityDomainService,
    OrganizationDomainService,
    ContractAnalysisDomainService,
    SecurityDomainService
)
from ..infrastructure.repositories import SQLAlchemyUnitOfWork
from ..application.use_cases import (
    OrganizationUseCases,
    ContractUseCases,
    APIKeyUseCases
)


T = TypeVar('T')


class Container:
    """Dependency injection container."""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._session_factory: Optional[async_sessionmaker] = None
        self.logger = logging.getLogger(__name__)
    
    def register_session_factory(self, session_factory: async_sessionmaker):
        """Register SQLAlchemy session factory."""
        self._session_factory = session_factory
    
    def register_singleton(self, interface: type, implementation: Any):
        """Register a singleton service."""
        self._singletons[interface.__name__] = implementation
        self.logger.debug(f"Registered singleton: {interface.__name__}")
    
    def register_transient(self, interface: type, factory: Callable[[], Any]):
        """Register a transient service."""
        self._services[interface.__name__] = factory
        self.logger.debug(f"Registered transient: {interface.__name__}")
    
    def get(self, interface: type) -> Any:
        """Get service instance."""
        service_name = interface.__name__
        
        # Check singletons first
        if service_name in self._singletons:
            return self._singletons[service_name]
        
        # Check transient services
        if service_name in self._services:
            return self._services[service_name]()
        
        # Auto-wire known services
        if service_name == "SQLAlchemyUnitOfWork":
            if not self._session_factory:
                raise ValueError("Session factory not registered")
            return SQLAlchemyUnitOfWork(self._session_factory)
        
        raise ValueError(f"Service not registered: {service_name}")
    
    def configure_services(self):
        """Configure all services and their dependencies."""
        self.logger.info("Configuring dependency injection container...")
        
        # Register domain services
        self.register_transient(
            IOrganizationDomainService,
            lambda: OrganizationDomainService(
                org_repository=None,  # Will be injected via UoW
                user_repository=None  # Will be injected via UoW
            )
        )
        
        self.register_transient(
            IContractAnalysisDomainService,
            lambda: ContractAnalysisDomainService(
                ai_service=None  # Will be injected
            )
        )
        
        self.register_transient(
            ISecurityDomainService,
            lambda: SecurityDomainService(
                api_key_repository=None,  # Will be injected via UoW
                audit_repository=None,    # Will be injected
                cache_service=None        # Will be injected
            )
        )
        
        # Register use cases
        self.register_transient(
            OrganizationUseCases,
            lambda: OrganizationUseCases(
                uow=self.get(SQLAlchemyUnitOfWork),
                org_domain_service=self.get(IOrganizationDomainService),
                security_service=self.get(ISecurityDomainService)
            )
        )
        
        self.register_transient(
            ContractUseCases,
            lambda: ContractUseCases(
                uow=self.get(SQLAlchemyUnitOfWork),
                analysis_service=self.get(IContractAnalysisDomainService),
                security_service=self.get(ISecurityDomainService)
            )
        )
        
        self.register_transient(
            APIKeyUseCases,
            lambda: APIKeyUseCases(
                uow=self.get(SQLAlchemyUnitOfWork),
                security_service=self.get(ISecurityDomainService)
            )
        )
        
        self.logger.info("Dependency injection container configured successfully")


# Global container instance
_container: Optional[Container] = None


def get_container() -> Container:
    """Get the global container instance."""
    global _container
    if _container is None:
        _container = Container()
        _container.configure_services()
    return _container


def configure_container(session_factory: async_sessionmaker) -> Container:
    """Configure the container with session factory."""
    container = get_container()
    container.register_session_factory(session_factory)
    return container
