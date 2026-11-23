import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.gtfs import load_feed
t = load_feed(Path("data/hito-03/replay/fomento_transit.zip"), network_id="10")
pd = lambda v: datetime.strptime(v, "%Y%m%d").date()
vf = min(pd(c.start_date) for c in t.calendar)
vu = max(pd(c.end_date) for c in t.calendar)
today = datetime.now(ZoneInfo("Europe/Madrid")).date()
print(f"GTFS del kit: vigencia {vf} .. {vu}; hoy {today}; "
      f"{'VÁLIDO para live' if vf <= today <= vu else 'FUERA DE VIGENCIA -> live falla al arrancar'}")
print(f"servicios en calendar.txt: {len(t.calendar)}")
