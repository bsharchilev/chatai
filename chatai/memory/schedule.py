from crontab import CronTab


_cron_command = '/home/bsharchilev/chatai/chatai-env/bin/python -m chatai.memory.extract'

def create_cron_job(cron: CronTab):
    if not any(job for job in cron if job.command == _cron_command):
        job = cron.new(command=_cron_command)
        job.day.every(1)
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