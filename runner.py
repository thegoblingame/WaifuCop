import schedule
import time
import sys
from aw_probe import main as probe_main

try:
    minutes = int(sys.argv[1])
except (IndexError, ValueError):
    minutes = 60

def job():
    print("running aw_probe...")
    probe_main(minutes)
    print("done.\n")

def run_every(minutes: int):
    schedule.every(minutes).minutes.do(job)

    print(f"starting scheduler: running every {minutes} minutes")
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":

    run_every(minutes)