#!/usr/bin/env python3
"""
Transaction Simulator for FraudShield AI

Generates realistic financial transactions and sends them to the API.
Used for testing, demos, and populating the system with representative data.

Usage:
    python scripts/simulate_transactions.py --rate 10 --duration 60
    python scripts/simulate_transactions.py --count 100 --fraud-rate 0.05
    python scripts/simulate_transactions.py --demo  # Run the demo scenario
"""

import argparse
import asyncio
import json
import random
import string
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

try:
    import httpx
except ImportError:
    print("httpx is required. Install with: pip install httpx")
    sys.exit(1)


# ─── Configuration ───────────────────────────────────────────────────────────

API_BASE_URL = "http://localhost:8000/api/v1"

# Indian cities with lat/lng
LOCATIONS = [
    {"city": "Mumbai", "lat": 19.0760, "lng": 72.8777},
    {"city": "Delhi", "lat": 28.6139, "lng": 77.2090},
    {"city": "Bangalore", "lat": 12.9716, "lng": 77.5946},
    {"city": "Chennai", "lat": 13.0827, "lng": 80.2707},
    {"city": "Hyderabad", "lat": 17.3850, "lng": 78.4867},
    {"city": "Pune", "lat": 18.5204, "lng": 73.8567},
    {"city": "Kolkata", "lat": 22.5726, "lng": 88.3639},
    {"city": "Ahmedabad", "lat": 23.0225, "lng": 72.5714},
    {"city": "Jaipur", "lat": 26.9124, "lng": 75.7873},
    {"city": "Lucknow", "lat": 26.8467, "lng": 80.9462},
]

# Foreign cities (for anomalous location transactions)
FOREIGN_LOCATIONS = [
    {"city": "Dubai", "lat": 25.2048, "lng": 55.2708},
    {"city": "Singapore", "lat": 1.3521, "lng": 103.8198},
    {"city": "London", "lat": 51.5074, "lng": -0.1278},
    {"city": "New York", "lat": 40.7128, "lng": -74.0060},
    {"city": "Moscow", "lat": 55.7558, "lng": 37.6173},
]

MERCHANT_CATEGORIES = [
    "electronics", "grocery", "restaurant", "travel", "entertainment",
    "clothing", "fuel", "healthcare", "education", "gaming",
    "jewelry", "real_estate", "insurance", "utilities", "retail",
]

HIGH_RISK_CATEGORIES = ["electronics", "jewelry", "gaming", "travel"]

PAYMENT_METHODS = ["card", "upi", "netbanking", "wallet", "bank_transfer"]


# ─── User Profiles ───────────────────────────────────────────────────────────

class UserProfile:
    """Simulated user with spending patterns."""
    
    def __init__(self, user_num: int):
        self.user_id = f"USR-{user_num:05d}"
        self.home_location = random.choice(LOCATIONS)
        self.typical_amount_range = (
            random.uniform(100, 500),
            random.uniform(2000, 10000),
        )
        self.typical_categories = random.sample(MERCHANT_CATEGORIES, k=random.randint(3, 6))
        self.typical_hours = list(range(random.randint(8, 10), random.randint(20, 23)))
        self.devices = [f"DEV-{random.randint(1000, 9999)}" for _ in range(random.randint(1, 3))]
        self.preferred_payment = random.choice(PAYMENT_METHODS)
        self.merchant_ids = [f"MER-{random.randint(1000, 9999)}" for _ in range(random.randint(3, 8))]

    def generate_normal_transaction(self) -> dict:
        """Generate a normal transaction matching user's typical behavior."""
        amount = round(random.uniform(*self.typical_amount_range), 2)
        loc = self.home_location
        # Add small jitter to location
        lat = loc["lat"] + random.uniform(-0.05, 0.05)
        lng = loc["lng"] + random.uniform(-0.05, 0.05)

        return {
            "user_id": self.user_id,
            "amount": amount,
            "currency": "INR",
            "merchant_id": random.choice(self.merchant_ids),
            "merchant_category": random.choice(self.typical_categories),
            "payment_method": self.preferred_payment,
            "device_id": random.choice(self.devices),
            "ip_address": f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "location": {"latitude": round(lat, 4), "longitude": round(lng, 4)},
        }

    def generate_suspicious_transaction(self, attack_type: str = "random") -> dict:
        """Generate a suspicious/fraudulent transaction."""
        if attack_type == "random":
            attack_type = random.choice([
                "high_value", "new_device", "foreign_location",
                "velocity", "unusual_category", "combined",
            ])

        txn = self.generate_normal_transaction()

        if attack_type == "high_value":
            # Transaction 5-20x the user's typical maximum
            txn["amount"] = round(self.typical_amount_range[1] * random.uniform(5, 20), 2)

        elif attack_type == "new_device":
            txn["device_id"] = f"DEV-{random.randint(90000, 99999)}"
            txn["amount"] = round(self.typical_amount_range[1] * random.uniform(2, 5), 2)

        elif attack_type == "foreign_location":
            foreign = random.choice(FOREIGN_LOCATIONS)
            txn["location"] = {"latitude": foreign["lat"], "longitude": foreign["lng"]}
            txn["ip_address"] = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

        elif attack_type == "velocity":
            # Will be sent in rapid succession (caller handles timing)
            txn["amount"] = round(random.uniform(5000, 25000), 2)

        elif attack_type == "unusual_category":
            unusual = [c for c in HIGH_RISK_CATEGORIES if c not in self.typical_categories]
            if unusual:
                txn["merchant_category"] = random.choice(unusual)
            txn["merchant_id"] = f"MER-{random.randint(90000, 99999)}"
            txn["amount"] = round(random.uniform(10000, 50000), 2)

        elif attack_type == "combined":
            # Multiple red flags at once
            foreign = random.choice(FOREIGN_LOCATIONS)
            txn["amount"] = round(self.typical_amount_range[1] * random.uniform(8, 15), 2)
            txn["device_id"] = f"DEV-{random.randint(90000, 99999)}"
            txn["location"] = {"latitude": foreign["lat"], "longitude": foreign["lng"]}
            txn["merchant_category"] = random.choice(HIGH_RISK_CATEGORIES)
            txn["merchant_id"] = f"MER-{random.randint(90000, 99999)}"
            txn["ip_address"] = f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"

        return txn


# ─── Simulator Engine ────────────────────────────────────────────────────────

class TransactionSimulator:
    """Generates and sends transactions to the FraudShield AI API."""

    def __init__(self, base_url: str = API_BASE_URL, num_users: int = 20):
        self.base_url = base_url
        self.users = [UserProfile(i) for i in range(1, num_users + 1)]
        self.token: Optional[str] = None
        self.stats = {
            "sent": 0,
            "normal": 0,
            "suspicious": 0,
            "errors": 0,
            "start_time": None,
        }

    async def authenticate(self, client: httpx.AsyncClient) -> bool:
        """Register and login a simulator user."""
        email = "simulator@fraudshield.ai"
        password = "SimulatorPass123!"

        # Try to register (might already exist)
        await client.post(
            f"{self.base_url}/auth/register",
            json={"email": email, "password": password, "full_name": "Transaction Simulator"},
        )

        # Login
        resp = await client.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password},
        )
        if resp.status_code == 200:
            self.token = resp.json()["data"]["access_token"]
            return True
        else:
            print(f"[ERROR] Authentication failed: {resp.status_code} - {resp.text}")
            return False

    async def send_transaction(self, client: httpx.AsyncClient, txn_data: dict, is_suspicious: bool = False) -> bool:
        """Send a single transaction to the API."""
        try:
            resp = await client.post(
                f"{self.base_url}/transactions",
                json=txn_data,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10.0,
            )
            if resp.status_code in (200, 201, 202):
                self.stats["sent"] += 1
                if is_suspicious:
                    self.stats["suspicious"] += 1
                else:
                    self.stats["normal"] += 1

                txn_id = resp.json().get("data", {}).get("transaction_id", "?")
                label = "🔴 SUSPICIOUS" if is_suspicious else "🟢 NORMAL"
                print(
                    f"  {label} | {txn_id} | ₹{txn_data['amount']:>12,.2f} | "
                    f"{txn_data.get('merchant_category', 'N/A'):>15} | "
                    f"{txn_data.get('device_id', 'N/A')}"
                )
                return True
            else:
                self.stats["errors"] += 1
                print(f"  [ERROR] {resp.status_code}: {resp.text[:100]}")
                return False
        except Exception as e:
            self.stats["errors"] += 1
            print(f"  [ERROR] {e}")
            return False

    async def run_continuous(self, rate: float, duration: int, fraud_rate: float = 0.05):
        """Run continuous transaction generation at a specified rate."""
        interval = 1.0 / rate
        end_time = time.time() + duration
        self.stats["start_time"] = time.time()

        print(f"\n{'='*80}")
        print(f"  FraudShield AI — Transaction Simulator")
        print(f"  Rate: {rate} txn/sec | Duration: {duration}s | Fraud rate: {fraud_rate*100:.1f}%")
        print(f"  Target: ~{int(rate * duration)} transactions")
        print(f"{'='*80}\n")

        async with httpx.AsyncClient() as client:
            if not await self.authenticate(client):
                return

            while time.time() < end_time:
                user = random.choice(self.users)
                is_fraud = random.random() < fraud_rate

                if is_fraud:
                    txn_data = user.generate_suspicious_transaction()
                else:
                    txn_data = user.generate_normal_transaction()

                await self.send_transaction(client, txn_data, is_suspicious=is_fraud)
                await asyncio.sleep(interval)

        self._print_summary()

    async def run_batch(self, count: int, fraud_rate: float = 0.05):
        """Generate a batch of transactions."""
        self.stats["start_time"] = time.time()

        print(f"\n{'='*80}")
        print(f"  FraudShield AI — Batch Transaction Simulator")
        print(f"  Count: {count} | Fraud rate: {fraud_rate*100:.1f}%")
        print(f"{'='*80}\n")

        async with httpx.AsyncClient() as client:
            if not await self.authenticate(client):
                return

            for i in range(count):
                user = random.choice(self.users)
                is_fraud = random.random() < fraud_rate

                if is_fraud:
                    txn_data = user.generate_suspicious_transaction()
                else:
                    txn_data = user.generate_normal_transaction()

                await self.send_transaction(client, txn_data, is_suspicious=is_fraud)

        self._print_summary()

    async def run_demo_scenario(self):
        """Run the demo scenario from the project spec.
        
        Step 1: Normal user makes ₹1,200 transaction → Risk: LOW, APPROVED
        Step 2: Same user makes ₹2,000 transaction → Risk: LOW, APPROVED  
        Step 3: Suddenly: ₹95,000 from new device, new location → Risk: HIGH, REVIEW/BLOCK
        """
        print(f"\n{'='*80}")
        print(f"  FraudShield AI — Demo Scenario")
        print(f"  Telling the story of a fraud attempt...")
        print(f"{'='*80}\n")

        demo_user = self.users[0]

        async with httpx.AsyncClient() as client:
            if not await self.authenticate(client):
                return

            # Step 1: Normal transaction
            print("\n📋 Step 1: Normal transaction")
            print(f"   User {demo_user.user_id} buys groceries...\n")
            txn1 = demo_user.generate_normal_transaction()
            txn1["amount"] = 1200.00
            txn1["merchant_category"] = "grocery"
            await self.send_transaction(client, txn1)
            await asyncio.sleep(2)

            # Step 2: Another normal transaction
            print("\n📋 Step 2: Another normal transaction")
            print(f"   User {demo_user.user_id} pays at a restaurant...\n")
            txn2 = demo_user.generate_normal_transaction()
            txn2["amount"] = 2000.00
            txn2["merchant_category"] = "restaurant"
            await self.send_transaction(client, txn2)
            await asyncio.sleep(2)

            # Step 3: Suspicious transaction
            print("\n🚨 Step 3: SUSPICIOUS TRANSACTION")
            print(f"   Suddenly: ₹95,000 from new device in Dubai...\n")
            txn3 = demo_user.generate_suspicious_transaction("combined")
            txn3["amount"] = 95000.00
            await self.send_transaction(client, txn3, is_suspicious=True)
            await asyncio.sleep(1)

            # Step 4: Velocity attack
            print("\n🚨 Step 4: VELOCITY ATTACK")
            print(f"   5 rapid transactions in 10 seconds...\n")
            for i in range(5):
                txn_v = demo_user.generate_suspicious_transaction("velocity")
                await self.send_transaction(client, txn_v, is_suspicious=True)
                await asyncio.sleep(0.5)

        self._print_summary()
        print("\n💡 Open the dashboard to see the fraud alerts!")

    def _print_summary(self):
        """Print simulation summary."""
        elapsed = time.time() - self.stats["start_time"]
        total = self.stats["sent"]
        rate = total / elapsed if elapsed > 0 else 0

        print(f"\n{'='*80}")
        print(f"  Simulation Summary")
        print(f"{'='*80}")
        print(f"  Total sent:      {total}")
        print(f"  Normal:          {self.stats['normal']}")
        print(f"  Suspicious:      {self.stats['suspicious']}")
        print(f"  Errors:          {self.stats['errors']}")
        print(f"  Duration:        {elapsed:.1f}s")
        print(f"  Rate:            {rate:.1f} txn/sec")
        print(f"  Fraud ratio:     {self.stats['suspicious']/total*100:.1f}%" if total else "  Fraud ratio:     N/A")
        print(f"{'='*80}\n")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="FraudShield AI Transaction Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --rate 10 --duration 60       # 10 txn/sec for 60 seconds
  %(prog)s --count 500 --fraud-rate 0.1  # 500 transactions, 10%% fraud
  %(prog)s --demo                         # Run demo scenario
  %(prog)s --rate 100 --duration 30       # Load test: 100 txn/sec
""",
    )

    parser.add_argument(
        "--rate", type=float, default=5,
        help="Transactions per second (default: 5)",
    )
    parser.add_argument(
        "--duration", type=int, default=30,
        help="Duration in seconds for continuous mode (default: 30)",
    )
    parser.add_argument(
        "--count", type=int, default=None,
        help="Number of transactions for batch mode",
    )
    parser.add_argument(
        "--fraud-rate", type=float, default=0.05,
        help="Fraction of fraudulent transactions (default: 0.05 = 5%%)",
    )
    parser.add_argument(
        "--users", type=int, default=20,
        help="Number of simulated users (default: 20)",
    )
    parser.add_argument(
        "--api-url", type=str, default=API_BASE_URL,
        help=f"API base URL (default: {API_BASE_URL})",
    )
    parser.add_argument(
        "--demo", action="store_true",
        help="Run the demo scenario",
    )

    args = parser.parse_args()

    simulator = TransactionSimulator(base_url=args.api_url, num_users=args.users)

    if args.demo:
        asyncio.run(simulator.run_demo_scenario())
    elif args.count:
        asyncio.run(simulator.run_batch(args.count, args.fraud_rate))
    else:
        asyncio.run(simulator.run_continuous(args.rate, args.duration, args.fraud_rate))


if __name__ == "__main__":
    main()
