import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backoffice.rd_funding.bootstrap import bootstrap_ingecart


if __name__ == "__main__":
    result = bootstrap_ingecart()
    print(f"INGECART projects: {len(result['projects'])}")
    print(f"Funding calls: {len(result['funding_calls'])}")
    print(f"Project x funding matches: {len(result['matrix'])}")
    print(f"Next missions: {len(result['missions'])}")
