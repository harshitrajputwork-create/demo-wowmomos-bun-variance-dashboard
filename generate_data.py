"""Generates the Wow Momos bun-count pilot CSV (1-24 Sep 2026, 6 stores) in the exact Taqtics export layout.

Logic (matches the form):
  Buns sold            = burgers sold (POS) x 2
  Opening (Bun remaining for this month) = last reported closing - buns sold since that report
  Expected closing     = Opening - Buns sold
  Actual closing       = physical count entered by store
  Actual remaining col = Opening - Actual closing   (buns actually consumed, incl. loss)
  Variance             = Expected closing - Actual closing   (+ve = shortage/loss, -ve = surplus)
"""
import csv, random, datetime as dt, os

random.seed(26)
OUT = os.path.join(os.path.dirname(__file__), "Bun_Variance_Data.csv")

HEADER = ["Submission Id","Submitted For","Store","Entity Id","Area","City","State","Country","Submitted By",
"Submitter Email","Device Info","Time taken (Min)","Total score","Compliance","Started At","Completed At",
"Submission Timezone","Period","Buns allocated for your QSR store for this Month","Comment-0100007",
"Number of burgers sold today as per POS","Comment-0100008",
"Number of buns sold (Auto calculated from POS sales 1 burger = 2 bun)","Comment-0100001",
"Expected closing count of bun in store","Comment-0100003","Actual closing count of bun in store","Comment-0100009",
"Bun remaining for this month","Comment-0100012","Actual Remaining bun from total allocated bun","Comment-0100011",
"Variance","Comment-0100010","Filing Status"]

# name, area, entity, base burgers/day, allocation, staff, story
STORES = [
 ("WOW Momos - Koramangala","Koramangala","WM-BLR-001",190,14000,"Ravi Kumar"),
 ("WOW Momos - Indiranagar","Indiranagar","WM-BLR-002",170,12300,"Sneha Reddy"),
 ("WOW Momos - HSR Layout","HSR Layout","WM-BLR-003",150,10800,"Imran Sheikh"),
 ("WOW Momos - Whitefield","Whitefield","WM-BLR-004",200,13900,"Pradeep Nair"),
 ("WOW Momos - Jayanagar","Jayanagar","WM-BLR-005",170,11100,"Lakshmi Iyer"),
 ("WOW Momos - Electronic City","Electronic City","WM-BLR-006",130,9600,"Arjun Das"),
]

# story[(store_idx, day)] = (loss_buns, comment, count_error)   loss<0 => surplus (unlogged stock came in)
S = {}
def st(i, d, loss, comment="-", cerr=0): S[(i, d)] = (loss, comment, cerr)

# 0 Koramangala - the model store
st(0,12,14,"Tray dropped during evening rush, 14 buns unusable")
st(0,20,8,"Opened pack not used within shift, 8 buns went stale")
# 1 Indiranagar - training wastage then a freezer incident
st(1,8,22,"18 buns wasted in new staff training and 4 got over cooked")
st(1,9,16,"Training day 2: 12 buns wasted while practising assembly, 4 over-toasted")
st(1,10,9,"Training day 3: 9 buns wasted during assembly practice")
st(1,19,30,"Freezer door left ajar overnight, 30 buns went soggy and were discarded")
# 2 HSR - negative variance = stock came in that was never logged
st(2,6,-40,"Received 40 buns from Koramangala store (inter-store transfer), not logged")
st(2,11,-18,"Received 18 buns from Koramangala store, transfer not logged")
st(2,15,0,"-",cerr=12)
st(2,16,0,"Recount done - yesterday's count was 12 high",cerr=0)
st(2,22,6,"-")
# 3 Whitefield - slow-building unexplained loss
for d,l in zip(range(14,22),[6,9,13,17,21,26,30,34]): st(3,d,l,"-")
st(3,22,38,"Manager note: staff meals being issued without a POS entry, will start logging")
st(3,23,12,"Staff meal logging started - 12 buns for staff meals")
st(3,24,8,"Staff meals logged, 8 buns")
# 4 Jayanagar - festival rush, running out of allocation
st(4,13,11,"Festival rush - buns overcooked on grill during peak, 11 wasted")
st(4,17,9,"Buns burnt during rush hour, 9 wasted")
# 5 Electronic City - filing discipline problem
st(5,3,7,"Expired buns from old batch discarded, 7 buns")
st(5,6,10,"Yesterday's entry missed, counted today")
st(5,13,14,"Missed 2 days of entry, counted today")
st(5,21,9,"Yesterday's entry missed, counted today")
MISSED = {5:{5,11,12,20}}
DELAYED_EXTRA = {5:{3,8,16,17,23}}

first = dt.date(2026,9,1)
rows, sid = [], 4900
for i,(name,area,ent,base,alloc,who) in enumerate(STORES):
    true_stock = alloc          # physical stock
    reported = alloc            # last reported closing
    sold_since = 0
    for d in range(1,25):
        day = first + dt.timedelta(days=d-1)
        f = 1.2 if day.weekday()>=4 else 1.0
        if i==4 and d>=11: f *= 1.30 + (0.05 if d in (13,14,15,16) else 0)   # festival demand
        burgers = int(base*f*random.uniform(0.93,1.07))
        sold = burgers*2
        loss, comment, cerr = S.get((i,d), (random.choice([0,0,0,1,2,3]),"-",0))
        opening = reported - sold_since
        expected = opening - sold
        true_stock = true_stock - sold - loss
        sold_since += sold
        missed = d in MISSED.get(i,set())
        sid += 1
        period = f"{day.day} {day:%B} {day.year}  12:30 AM-{day.day} {day:%B} {day.year}  10:29 PM"
        base_row = [f"IPLF{sid}", f"{day.day:02d}-{day:%b}-{day:%y}", name, ent, area, "bangalore","karnataka","india"]
        if missed:
            rows.append(base_row+["-","-","-","-","-","-","-","-","Asia/Calcutta (GMT+5:30)",period,alloc,"-",
                                  burgers,"-",sold,"-","-","-","-","-","-","-","-","-","-","-","MISSED"])
            continue
        actual = true_stock + cerr
        variance = expected - actual
        consumed = opening - actual
        late = (d in DELAYED_EXTRA.get(i,set())) or random.random()<0.08
        h,m = (22,random.randint(35,58)) if late else (21,random.randint(5,59))
        if not late and random.random()<0.35: h,m = 22,random.randint(0,20)
        took = random.randint(3,9)
        end = dt.datetime(day.year,day.month,day.day,h,m)
        start = end - dt.timedelta(minutes=took)
        rows.append(base_row+[who,who.lower().replace(" ",".")+"@wowmomos.in","chrome 153 android 14",took,0,100,
            start.strftime("%d-%m-%Y %H:%M"),end.strftime("%d-%m-%Y %H:%M"),"Asia/Calcutta (GMT+5:30)",period,
            alloc,"-",burgers,"-",sold,"-",expected,"-",actual,"-",opening,"-",consumed,"-",variance,
            comment if abs(variance)>=6 or comment!="-" else "-", "DELAYED" if late else "ON TIME"])
        reported, sold_since = actual, 0

with open(OUT,"w",newline="",encoding="utf-8-sig") as fh:
    w = csv.writer(fh); w.writerow(HEADER); w.writerows(rows)
print(len(rows),"rows ->",OUT)
