import sys
import os
import logging
from unittest.mock import MagicMock

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from governance import AgentContext, AgentContract, DiagnosisReport
from workers.worker_pp import PrizePicksWorker
from workers.worker_fd import FanDuelWorker
from workers.worker_dk import DraftKingsWorker
from workers.worker_baseball import BaseballWorker
from workers.worker_f1 import F1Worker
from workers.worker_tennis import TennisWorker
from workers.worker_nhl import NHLWorker
from workers.worker_nflpenalties import NFLPenaltiesWorker
from workers.worker_nbastuffer import NBAStufferWorker
from workers.worker_nflverse import NFLVerseWorker
from workers.worker_fbref import FBRefWorker
from workers.worker_noaa import NOAAWorker
from workers.worker_ufc import UFCWorker
from workers.worker_esports import EsportsWorker
from workers.worker_chickenstats import ChickenStatsWorker
from workers.worker_rotogrinders import RotoGrindersWorker
from workers.worker_datagolf import DataGolfWorker
from workers.worker_sic import SICWorker
from workers.worker_sec import SECWorker
from workers.worker_umps import UmpsWorker
from workers.worker_platform import PlatformWorker
from workers.worker_scorekeeper import ScorekeeperWorker
from workers.worker_graphql import GraphQLWorker

# Mock Context
contract = AgentContract(
    agent_id="test_agent",
    human_readable_name="Test Agent",
    autonomy_level=2
)
diagnosis = DiagnosisReport(
    problem_summary="Test Run",
    root_cause_hypothesis="Verification",
    confidence=1.0
)
ctx = AgentContext(contract=contract, current_diagnosis=diagnosis, mission_id="test_mission_123")

def verify_worker(worker_class, name):
    try:
        print(f"Instantiating {name}...")
        worker = worker_class(ctx)
        print(f"Successfully instantiated {name}.")
        
        # Verify execute signature
        # We mock run() to avoid actual execution
        worker.run = MagicMock(return_value=True)
        
        # Mock storage/firestore to avoid errors
        worker.upload_json = MagicMock()
        worker.db = MagicMock()
        worker.db.collection.return_value.add.return_value = (None, None)
        
        # Mock bucket for workers that use it directly
        worker.bucket = MagicMock()
        worker.bucket.blob.return_value.upload_from_string.return_value = None
        
        # Mock socketio for Platform/Scorekeeper
        if hasattr(worker, 'sio'):
            worker.sio = MagicMock()
        
        print(f"Running execute() for {name}...")
        result = worker.execute(ctx=ctx)
        
        if isinstance(result, tuple) and len(result) == 2:
            success, report_path = result
            print(f"Verification Successful for {name}: execute() returns (bool, str/None). Result: {result}")
        else:
            print(f"Verification Failed for {name}: execute() did not return tuple. Result: {result}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Verification Failed for {name}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

verify_worker(PrizePicksWorker, "PrizePicksWorker")
verify_worker(FanDuelWorker, "FanDuelWorker")
verify_worker(DraftKingsWorker, "DraftKingsWorker")
verify_worker(BaseballWorker, "BaseballWorker")
verify_worker(F1Worker, "F1Worker")
verify_worker(TennisWorker, "TennisWorker")
verify_worker(NHLWorker, "NHLWorker")
verify_worker(NFLPenaltiesWorker, "NFLPenaltiesWorker")
verify_worker(NBAStufferWorker, "NBAStufferWorker")
verify_worker(NFLVerseWorker, "NFLVerseWorker")
verify_worker(FBRefWorker, "FBRefWorker")
verify_worker(NOAAWorker, "NOAAWorker")
verify_worker(UFCWorker, "UFCWorker")
verify_worker(EsportsWorker, "EsportsWorker")
verify_worker(ChickenStatsWorker, "ChickenStatsWorker")
verify_worker(RotoGrindersWorker, "RotoGrindersWorker")
verify_worker(DataGolfWorker, "DataGolfWorker")
verify_worker(SICWorker, "SICWorker")
verify_worker(SECWorker, "SECWorker")
verify_worker(UmpsWorker, "UmpsWorker")
verify_worker(PlatformWorker, "PlatformWorker")
verify_worker(ScorekeeperWorker, "ScorekeeperWorker")
verify_worker(GraphQLWorker, "GraphQLWorker")
