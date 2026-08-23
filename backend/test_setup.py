"""
Test script to verify database connection and data loading
"""

from app.database import check_db_connection, init_db, SessionLocal
from app.models import Test
from app.preprocessing import preprocess_dataframe
from app.config import settings
import pandas as pd


def test_database_connection():
    """Test 1: Database connection"""
    print("\n" + "="*60)
    print("TEST 1: Database Connection")
    print("="*60)
    
    if check_db_connection():
        print("✅ Database connection successful!")
        return True
    else:
        print("❌ Database connection failed!")
        return False


def test_load_initial_data():
    """Test 2: Load and preprocess CSV data"""
    print("\n" + "="*60)
    print("TEST 2: Load Initial Data")
    print("="*60)
    
    try:
        # Read CSV
        df = pd.read_csv(settings.INITIAL_DATA_PATH, encoding='utf-8',sep=';')
        print(f"✅ CSV loaded: {len(df)} rows")
        
        # Preprocess
        df = preprocess_dataframe(df)
        print(f"✅ Data preprocessed: {len(df)} rows")
        
        return True, df
    except Exception as e:
        print(f"❌ Failed to load data: {e}")
        return False, None


def test_insert_to_database(df):
    """Test 3: Insert data into PostgreSQL"""
    print("\n" + "="*60)
    print("TEST 3: Insert Data to Database")
    print("="*60)
    
    try:
        db = SessionLocal()
        
        # Check if data already exists
        existing_count = db.query(Test).count()
        if existing_count > 0:
            print(f"ℹ️  Database already has {existing_count} tests")
            response = input("Clear and reload? (y/n): ")
            if response.lower() == 'y':
                db.query(Test).delete()
                db.commit()
                print("✅ Existing data cleared")
        
        # Insert data
        for idx, row in df.iterrows():
            test = Test(
                nom_de_test=row.get('nom_de_test'),
                categorie_de_test=row.get('categorie_de_test'),
                direction_metier=row.get('direction_metier'),
                repartition=row.get('repartition'),
                test_homologation=row.get('test_homologation', False),
                pays_commercialisation=row.get('pays_commercialisation'),
                prestation=row.get('prestation'),
                sous_prestation=row.get('sous_prestation'),
                categorie_vehicule=row.get('categorie_vehicule'),
                strategie_validation=row.get('strategie_validation'),
                pourcentage_necessite=row.get('pourcentage_necessite'),
                prix_euro=row.get('prix_euro'),
                jalon=row.get('jalon'),
                duree_jours=row.get('duree_jours'),
                lieu_realisation=row.get('lieu_realisation'),
                description_essai=row.get('description_essai'),
                test_mivie=row.get('test_mivie'),
                zone_modification=row.get('zone_modification'),
                niveau_modification=row.get('niveau_modification'),
                type_moyen=row.get('type_moyen'),
                moyen_dedie_partage=row.get('moyen_dedie_partage')
            )
            db.add(test)
        
        db.commit()
        
        final_count = db.query(Test).count()
        print(f"✅ Successfully inserted {final_count} tests into database")
        
        db.close()
        return True
    
    except Exception as e:
        print(f"❌ Database insertion failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "🚀"*30)
    print("CAPGEMINI MI-VIE VALIDATOR - SETUP TEST")
    print("🚀"*30)
    
    # Test 1: Database
    if not test_database_connection():
        print("\n❌ Setup failed at database connection")
        return
    
    # Test 2: Load data
    success, df = test_load_initial_data()
    if not success:
        print("\n❌ Setup failed at data loading")
        return
    
    # Test 3: Insert to DB
    if not test_insert_to_database(df):
        print("\n❌ Setup failed at database insertion")
        return
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - SETUP COMPLETE!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Verify data in database:")
    print("     docker exec -it mivie-postgres psql -U mivie_user -d mivie_validation")
    print("     SELECT COUNT(*) FROM tests;")
    print("  2. Continue with backend routes setup")


if __name__ == "__main__":
    main()