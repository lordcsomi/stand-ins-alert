from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from stand_in_notifier import ScheduleEntry, DATABASE_URL  # Replace 'your_module' with the name of your script/module

def clear_entries():
    """Deletes schedule entries for today and tomorrow."""
    # Create database engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    # Get today's and tomorrow's dates
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)

    try:
        # Delete entries for today
        today_deleted = session.query(ScheduleEntry).filter(ScheduleEntry.date == today).delete()
        # Delete entries for tomorrow
        tomorrow_deleted = session.query(ScheduleEntry).filter(ScheduleEntry.date == tomorrow).delete()
        session.commit()
        print(f"Deleted {today_deleted} entries for {today}")
        print(f"Deleted {tomorrow_deleted} entries for {tomorrow}")
    except Exception as e:
        session.rollback()
        print(f"An error occurred: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    clear_entries()
