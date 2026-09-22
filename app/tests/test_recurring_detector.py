import sys
import os
import uuid
from decimal import Decimal

# Ensure python path includes project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.transaction import Transaction
from app.models.subscription import Subscription
from app.services.mock_generator_service import MockGeneratorService
from app.services.recurring_detector_service import RecurringDetectorService

def run_test():
    print("--- STARTING MODULE 8 RECURRING PAYMENT DETECTOR TEST ---")
    db = SessionLocal()
    try:
        # Create or fetch test user
        test_user = db.query(User).filter(User.email == "detector_test@example.com").first()
        if not test_user:
            test_user = User(
                id=uuid.uuid4(),
                email="detector_test@example.com",
                phone_number="+919876543210",
                full_name="Detector Test User",
                is_active=True
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)

        print(f"Test User ID: {test_user.id}")

        # Clean old transactions and subscriptions for clean test run
        db.query(Transaction).filter(Transaction.user_id == test_user.id).delete()
        db.query(Subscription).filter(Subscription.user_id == test_user.id).delete()
        db.commit()

        # Step 1: Generate Mock Transactions
        print("Generating mock bank transaction dataset (6 months)...")
        gen_result = MockGeneratorService.generate_mock_dataset(
            db=db,
            user_id=test_user.id,
            months=6,
            include_emi=True,
            include_anomaly=True
        )
        print(f"Generated {gen_result['total_transactions_created']} raw transactions.")

        # Step 2: Execute Recurring Detection Algorithm
        print("\nExecuting Recurring Payment Detection Algorithm...")
        det_result = RecurringDetectorService.detect_recurring_payments(
            db=db,
            user_id=test_user.id,
            amount_tolerance_pct=0.10,
            monthly_date_tolerance_days=3,
            yearly_date_tolerance_days=10,
            auto_create_subscriptions=True
        )

        print("\n--- DETECTION ALGORITHM RESULTS ---")
        print(f"Detected Patterns Count: {det_result['detected_count']}")
        print(f"Updated Labeled Transactions: {det_result['updated_transactions_count']}")
        
        for item in det_result["detected_subscriptions"]:
            print(f" -> Merchant: {item['merchant_name']:<25} | Freq: {item['billing_frequency']:<8} | Amount: ₹{item['expected_amount']:<8} | Confidence: {item['confidence_score']}% | Status: {item['status']}")

        # Verify labeled transactions in DB
        labeled_txs = db.query(Transaction).filter(
            Transaction.user_id == test_user.id,
            Transaction.is_labeled_recurring == True
        ).all()
        print(f"\nTotal transactions marked with is_labeled_recurring=True: {len(labeled_txs)}")

        # Verify pending subscriptions created in DB
        pending_subs = db.query(Subscription).filter(
            Subscription.user_id == test_user.id,
            Subscription.status == "pending_confirmation"
        ).all()
        print(f"Total Subscriptions created in DB with status='pending_confirmation': {len(pending_subs)}")

        assert det_result["detected_count"] > 0, "Error: Expected to detect at least 1 recurring payment pattern!"
        assert len(labeled_txs) > 0, "Error: Expected labeled transactions in database!"
        assert len(pending_subs) > 0, "Error: Expected auto-created pending subscriptions!"

        print("\n✅ MODULE 8 RECURRING DETECTION ALGORITHM TEST PASSED SUCCESSFULLY!")

    finally:
        db.close()

if __name__ == "__main__":
    run_test()
