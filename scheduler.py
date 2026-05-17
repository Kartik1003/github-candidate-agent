import schedule, time
from main import run_pipeline

schedule.every().monday.at("06:00").do(run_pipeline)

print("Scheduler running — pipeline fires every Monday at 06:00")
while True:
    schedule.run_pending()
    time.sleep(60)