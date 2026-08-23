"""
SQLAlchemy ORM models for database tables
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DECIMAL, Text, 
    TIMESTAMP, ForeignKey, ARRAY, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Test(Base):
    """Main test catalog table"""
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Core Information
    nom_de_test = Column(String(500), nullable=False, unique=True, index=True)
    categorie_de_test = Column(String(200), index=True)
    direction_metier = Column(String(100))
    repartition = Column(String(50))
    
    # Homologation & Markets
    test_homologation = Column(Boolean, default=False, index=True)
    pays_commercialisation = Column(String(200), index=True)
    
    # Prestation Details
    prestation = Column(String(200))
    sous_prestation = Column(String(200))
    
    # Vehicle Information
    categorie_vehicule = Column(String(100))
    strategie_validation = Column(String(100))
    
    # Test Requirements
    pourcentage_necessite = Column(DECIMAL(5, 2), index=True)
    prix_euro = Column(DECIMAL(10, 2))
    jalon = Column(String(100))
    duree_jours = Column(DECIMAL(6, 2))
    lieu_realisation = Column(String(200))
    description_essai = Column(Text)
    
    # Mi-Vie Specific
    test_mivie = Column(String(10), index=True)
    zone_modification = Column(String(200), index=True)
    niveau_modification = Column(String(500), index=True)
    
    # Resources
    type_moyen = Column(String(100))
    moyen_dedie_partage = Column(String(50))
    
    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    plan_tests = relationship("PlanTest", back_populates="test", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Test(id={self.id}, nom='{self.nom_de_test}')>"


class ValidationPlan(Base):
    """User-created validation plans"""
    __tablename__ = "validation_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Plan Information
    plan_name = Column(String(200), nullable=False)
    vehicle_category = Column(String(100), nullable=False)
    is_mivie = Column(Boolean, nullable=False)
    
    # Modification Details
    modification_zones = Column(ARRAY(Text))
    modification_level = Column(String(50))
    target_markets = Column(ARRAY(Text))
    
    # Constraints
    max_budget = Column(DECIMAL(10, 2))
    max_duration = Column(Integer)
    
    # Strategy
    strategy_type = Column(String(50), nullable=False, index=True)
    
    # Calculated Results
    total_cost = Column(DECIMAL(10, 2))
    total_duration_physical = Column(Integer)
    total_duration_engineering = Column(Integer)
    parallel_capacity = Column(Integer)
    risk_score = Column(DECIMAL(5, 2))
    feasibility_status = Column(String(20), index=True)
    
    # Scoring Breakdown
    score_coverage = Column(DECIMAL(5, 2))
    score_regulatory = Column(DECIMAL(5, 2))
    score_safety = Column(DECIMAL(5, 2))
    score_completeness = Column(DECIMAL(5, 2))
    score_efficiency = Column(DECIMAL(5, 2))
    score_timeline = Column(DECIMAL(5, 2))
    score_budget = Column(DECIMAL(5, 2))
    
    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    plan_tests = relationship("PlanTest", back_populates="plan", cascade="all, delete-orphan")
    ai_calls = relationship("AICallLog", back_populates="plan")
    
    def __repr__(self):
        return f"<ValidationPlan(id={self.id}, name='{self.plan_name}', status='{self.feasibility_status}')>"


class PlanTest(Base):
    """Many-to-many relationship between plans and tests"""
    __tablename__ = "plan_tests"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("validation_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    
    # Test Classification
    tier = Column(Integer, CheckConstraint("tier IN (1, 2, 3, 4)"), nullable=False, index=True)
    is_removable = Column(Boolean, default=True)
    removal_reason = Column(Text)
    
    # Execution Order
    execution_order = Column(Integer)
    
    # Relationships
    plan = relationship("ValidationPlan", back_populates="plan_tests")
    test = relationship("Test", back_populates="plan_tests")
    
    def __repr__(self):
        return f"<PlanTest(plan_id={self.plan_id}, test_id={self.test_id}, tier={self.tier})>"


class AICallLog(Base):
    """Track Capgemini AI API usage"""
    __tablename__ = "ai_call_log"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("validation_plans.id", ondelete="SET NULL"))
    
    # Request Details
    request_type = Column(String(50), nullable=False)
    prompt_text = Column(Text)
    
    # Response Details
    tokens_used = Column(Integer)
    response_time_ms = Column(Integer)
    success = Column(Boolean, nullable=False, index=True)
    error_message = Column(Text)
    
    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    
    # Relationships
    plan = relationship("ValidationPlan", back_populates="ai_calls")
    
    def __repr__(self):
        return f"<AICallLog(id={self.id}, type='{self.request_type}', success={self.success})>"