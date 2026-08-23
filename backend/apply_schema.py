"""
Script pour appliquer le schéma SQL sans Docker
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Configuration de connexion
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'mivie_validation',
    'user': 'mivie_user',
    'password': 'mivie_password_2024'
}

# Schéma SQL complet
SCHEMA_SQL = """
-- Drop existing tables
DROP TABLE IF EXISTS ai_call_log CASCADE;
DROP TABLE IF EXISTS plan_tests CASCADE;
DROP TABLE IF EXISTS validation_plans CASCADE;
DROP TABLE IF EXISTS tests CASCADE;

-- Table: tests
CREATE TABLE tests (
    id SERIAL PRIMARY KEY,
    nom_de_test VARCHAR(500) NOT NULL UNIQUE,
    categorie_de_test VARCHAR(200),
    direction_metier VARCHAR(100),
    repartition VARCHAR(50),
    test_homologation BOOLEAN DEFAULT FALSE,
    pays_commercialisation VARCHAR(200),
    prestation VARCHAR(200),
    sous_prestation VARCHAR(200),
    categorie_vehicule VARCHAR(100),
    strategie_validation VARCHAR(100),
    pourcentage_necessite DECIMAL(5,2),
    prix_euro DECIMAL(10,2),
    jalon VARCHAR(100),
    duree_jours DECIMAL(6,2),
    lieu_realisation VARCHAR(200),
    description_essai TEXT,
    test_mivie VARCHAR(10),
    zone_modification VARCHAR(200),
    niveau_modification VARCHAR(500),
    type_moyen VARCHAR(100),
    moyen_dedie_partage VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_test_mivie ON tests(test_mivie);
CREATE INDEX idx_test_zone ON tests(zone_modification);
CREATE INDEX idx_test_niveau ON tests(niveau_modification);
CREATE INDEX idx_test_homologation ON tests(test_homologation);
CREATE INDEX idx_test_pays ON tests(pays_commercialisation);
CREATE INDEX idx_test_categorie ON tests(categorie_de_test);
CREATE INDEX idx_test_necessite ON tests(pourcentage_necessite);

-- Table: validation_plans
CREATE TABLE validation_plans (
    id SERIAL PRIMARY KEY,
    plan_name VARCHAR(200) NOT NULL,
    vehicle_category VARCHAR(100) NOT NULL,
    is_mivie BOOLEAN NOT NULL,
    modification_zones TEXT[],
    modification_level VARCHAR(50),
    target_markets TEXT[],
    max_budget DECIMAL(10,2),
    max_duration INTEGER,
    strategy_type VARCHAR(50) NOT NULL,
    total_cost DECIMAL(10,2),
    total_duration_physical INTEGER,
    total_duration_engineering INTEGER,
    parallel_capacity INTEGER,
    risk_score DECIMAL(5,2),
    feasibility_status VARCHAR(20),
    score_coverage DECIMAL(5,2),
    score_regulatory DECIMAL(5,2),
    score_safety DECIMAL(5,2),
    score_completeness DECIMAL(5,2),
    score_efficiency DECIMAL(5,2),
    score_timeline DECIMAL(5,2),
    score_budget DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_plan_status ON validation_plans(feasibility_status);
CREATE INDEX idx_plan_strategy ON validation_plans(strategy_type);

-- Table: plan_tests
CREATE TABLE plan_tests (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER NOT NULL REFERENCES validation_plans(id) ON DELETE CASCADE,
    test_id INTEGER NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
    tier INTEGER NOT NULL CHECK (tier IN (1, 2, 3, 4)),
    is_removable BOOLEAN DEFAULT TRUE,
    removal_reason TEXT,
    execution_order INTEGER,
    UNIQUE(plan_id, test_id)
);

CREATE INDEX idx_plan_tests_plan ON plan_tests(plan_id);
CREATE INDEX idx_plan_tests_tier ON plan_tests(tier);

-- Table: ai_call_log
CREATE TABLE ai_call_log (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER REFERENCES validation_plans(id) ON DELETE SET NULL,
    request_type VARCHAR(50) NOT NULL,
    prompt_text TEXT,
    tokens_used INTEGER,
    response_time_ms INTEGER,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_ai_log_created ON ai_call_log(created_at);
CREATE INDEX idx_ai_log_success ON ai_call_log(success);

-- View: weekly_ai_usage
CREATE OR REPLACE VIEW weekly_ai_usage AS
SELECT 
    DATE_TRUNC('week', created_at) AS week_start,
    COUNT(*) AS total_calls,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) AS successful_calls,
    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) AS failed_calls,
    AVG(response_time_ms) AS avg_response_time_ms,
    SUM(tokens_used) AS total_tokens
FROM ai_call_log
GROUP BY DATE_TRUNC('week', created_at)
ORDER BY week_start DESC;

-- View: current_week_ai_usage
CREATE OR REPLACE VIEW current_week_ai_usage AS
SELECT 
    COUNT(*) AS calls_this_week,
    100 - COUNT(*) AS calls_remaining
FROM ai_call_log
WHERE created_at >= DATE_TRUNC('week', NOW());

-- Function: update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers
CREATE TRIGGER update_tests_updated_at
    BEFORE UPDATE ON tests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_plans_updated_at
    BEFORE UPDATE ON validation_plans
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""

def apply_schema():
    """Applique le schéma à la base de données"""
    try:
        print("🔌 Connexion à PostgreSQL...")
        conn = psycopg2.connect(**DB_CONFIG)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        print("📊 Application du schéma SQL...")
        cursor.execute(SCHEMA_SQL)
        
        print("✅ Schéma appliqué avec succès!")
        
        # Vérifier les tables créées
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        
        print("\n📋 Tables créées:")
        for table in tables:
            print(f"  ✓ {table[0]}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("APPLICATION DU SCHÉMA SQL")
    print("="*60)
    
    if apply_schema():
        print("\n✅ Base de données prête à l'emploi!")
        print("\nProchaines étapes:")
        print("  1. Exécuter: python test_setup.py")
        print("  2. Démarrer le backend: python -m app.main")
    else:
        print("\n❌ Échec de l'application du schéma")