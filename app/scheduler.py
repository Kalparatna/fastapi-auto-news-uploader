import threading
import time
from datetime import datetime, timedelta
from app.mongodb_service import MongoDBService
from app.tasks import fetch_and_post_cricket_news, cleanup_old_articles
import logging

logger = logging.getLogger(__name__)

class MongoDBScheduler:
    def __init__(self):
        self.mongodb_service = MongoDBService()
        self.running = False
        self.thread = None
        
    def setup_scheduled_tasks(self):
        """Setup scheduled tasks using MongoDB service"""
        try:
            self.mongodb_service.setup_scheduled_tasks()
            logger.info("✅ Scheduled tasks setup completed")
        except Exception as e:
            logger.error(f"❌ Error setting up scheduled tasks: {e}")
    
    def should_run_task(self, task):
        now = datetime.utcnow().replace(second=0, microsecond=0)
        schedule = task['schedule']
        task_time = now.replace(hour=schedule['hour'], minute=schedule['minute'])
        
        # Allow 2 minutes tolerance
        time_diff = abs((now - task_time).total_seconds())
        if time_diff > 120:
            return False
        
        last_run = task.get('last_run')
        if last_run:
            last_run_dt = last_run if isinstance(last_run, datetime) else datetime.fromisoformat(last_run)
            
            task_name = task.get('name', '')
            if 'cleanup' in task_name:
                min_interval = 23 * 3600  # 23 hours for daily tasks
            else:
                min_interval = 50 * 60    # 50 minutes for hourly tasks
            
            if (now - last_run_dt).total_seconds() < min_interval:
                return False
        
        return True
    
    def run_task(self, task):
        """Execute the scheduled task"""
        task_name = task.get('task', 'unknown')
        task_display_name = task.get('name', task_name)
        
        try:
            logger.info(f"🚀 STARTING scheduled task: {task_display_name}")
            start_time = datetime.utcnow()
            
            result = None
            if task_name == 'fetch_and_post_cricket_news':
                result = fetch_and_post_cricket_news()
            elif task_name == 'cleanup_old_articles':
                result = cleanup_old_articles()
            else:
                logger.error(f"❌ Unknown task: {task_name}")
                return
            
            try:
                self.mongodb_service.update_task_last_run(task['name'])
            except Exception as e:
                logger.error(f"❌ Failed to update last run time: {e}")
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"✅ COMPLETED task: {task_display_name} in {duration:.1f}s")
            logger.info(f"📊 Task result: {result}")
            
        except Exception as e:
            logger.error(f"❌ FAILED task {task_display_name}: {e}")
            
            try:
                self.mongodb_service.update_task_last_run(task['name'])
            except:
                pass
    
    def scheduler_loop(self):
        """Main scheduler loop"""
        logger.info("🕐 MongoDB Scheduler loop started")
        loop_count = 0
        
        while self.running:
            try:
                loop_count += 1
                current_time = datetime.utcnow()
                
                if loop_count % 10 == 0:
                    logger.info(f"💓 Scheduler heartbeat #{loop_count} at {current_time.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                
                tasks = self.mongodb_service.get_scheduled_tasks()
                
                if not tasks and loop_count % 10 == 0:
                    logger.warning("⚠️ No scheduled tasks found")
                
                for task in tasks:
                    if self.should_run_task(task):
                        logger.info(f"🎯 Task '{task['name']}' is due to run!")
                        task_thread = threading.Thread(
                            target=self.run_task,
                            args=(task,),
                            name=f"Task-{task['name']}"
                        )
                        task_thread.daemon = True
                        task_thread.start()
                
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"❌ Error in scheduler loop: {e}")
                time.sleep(30)
        
        logger.info("🛑 Scheduler loop ended")
    
    def start(self):
        """Start the scheduler"""
        if not self.running:
            logger.info("🔄 Starting the MongoDB Scheduler...")
            self.running = True
            try:
                self.setup_scheduled_tasks()
            except Exception as e:
                logger.error(f"❌ Failed to set up scheduled tasks: {e}")
                self.running = False
                return

            try:
                self.thread = threading.Thread(target=self.scheduler_loop)
                self.thread.daemon = True
                self.thread.start()
                logger.info("📅 MongoDB Scheduler started successfully")
            except Exception as e:
                logger.error(f"❌ Failed to start scheduler thread: {e}")
                self.running = False

    def stop(self):
        """Stop the scheduler"""
        logger.info("🛑 Stopping the MongoDB Scheduler...")
        self.running = False
        if self.thread:
            self.thread.join()
            logger.info("✅ Scheduler stopped")

# Global scheduler instance
scheduler = MongoDBScheduler()
