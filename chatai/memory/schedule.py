from crontab import CronTab


_cron_command = """
cd /home/bsharchilev/chatai &&
source chatai-env/bin/activate &&
source /home/bsharchilev/.env &&
python -m chatai.memory.extract'
"""

def create_cron_job(cron: CronTab):
    if not any(job for job in cron if job.command == _cron_command):
        job = cron.new(command=_cron_command)
        job.setall('30 11 * * *')
        cron.write()
        print("Cron job created")
    else:
        print("Cron job already exists")

def remove_cron_job(cron: CronTab):
    for job in cron:
        if job.command == _cron_command:
            cron.remove(job)
            print("Cron job removed.")
    cron.write()

def get_shutdown_handler(cron: CronTab):
    def shutdown_handler(signum, frame):
        print("Shutting down the web service...")
        remove_cron_job(cron)
        exit(0)
    return shutdown_handler