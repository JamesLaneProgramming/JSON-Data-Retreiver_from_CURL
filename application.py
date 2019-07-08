import os
from project import application

def main():
    #scheduler = BackgroundScheduler()
    #scheduler.add_job(func=check_overdue_assignments, trigger="interval", days=1)
    #scheduler.start()
    application.debug = True
    port = int(os.environ.get('PORT', 5000))
    application.run(host='0.0.0.0', port=port, use_reloader=False)

if __name__ == "__main__":
    main()
