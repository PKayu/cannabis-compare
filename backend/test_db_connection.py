import socket
import sys
import os
from urllib.parse import urlparse

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings

def check_connectivity():
    print("\n🕵️ Testing Database Connectivity...")
    
    db_url = settings.database_url
    if not db_url:
        print("❌ DATABASE_URL is not set in settings.")
        return

    try:
        result = urlparse(db_url)
        host = result.hostname
        port = result.port or 5432
        
        print(f"Target Host: {host}")
        
        # 1. Test Database Port
        print(f"\n[1] Testing Database Port ({port})...")
        try:
            sock = socket.create_connection((host, port), timeout=5)
            print(f"   ✅ SUCCESS: Connected to {host}:{port}")
            sock.close()
        except Exception as e:
            print(f"   ❌ FAILED: {e}")
            
            # 2. Test HTTPS Port (Diagnostic)
            print(f"\n[2] Testing HTTPS Port (443) for diagnostics...")
            try:
                sock = socket.create_connection((host, 443), timeout=5)
                print(f"   ✅ SUCCESS: Connected to {host}:443")
                print("\n   🔍 DIAGNOSIS: Your internet works, but ports 5432/6543 are blocked.")
                print("   👉 CAUSE: Corporate Firewall, ISP Block, or Supabase Network Restrictions.")
            except Exception as e:
                print(f"   ❌ FAILED: {e}")
                print("\n   🔍 DIAGNOSIS: Cannot reach Supabase at all (No Internet or DNS failure).")

    except Exception as e:
        print(f"❌ Error parsing URL: {e}")

if __name__ == "__main__":
    check_connectivity()