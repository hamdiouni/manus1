"""
Alert management system for SLA violations and anomalies.
"""

import asyncio
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import logging
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)

class AlertManager:
    """Manages alert notifications via Telegram and Email."""
    
    def __init__(self):
        self.config = {
            'sla_threshold': 0.8,
            'anomaly_threshold': 0.5,
            'channels': ['telegram', 'email'],
            'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN'),
            'telegram_chat_id': os.getenv('TELEGRAM_CHAT_ID'),
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'email_user': os.getenv('EMAIL_USER'),
            'email_password': os.getenv('EMAIL_PASSWORD'),
            'alert_email': os.getenv('ALERT_EMAIL')
        }
        
        # Rate limiting to prevent spam
        self.last_sla_alert = None
        self.last_anomaly_alert = None
        self.alert_cooldown = 300  # 5 minutes
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update alert configuration."""
        self.config.update(new_config)
        logger.info("Alert configuration updated")
    
    async def send_sla_alert(self, telemetry_id: int, risk_score: float):
        """Send SLA violation alert."""
        # Rate limiting
        now = datetime.now()
        if (self.last_sla_alert and 
            (now - self.last_sla_alert).seconds < self.alert_cooldown):
            return
        
        if risk_score < self.config['sla_threshold']:
            return
        
        self.last_sla_alert = now
        
        message = (
            f"🚨 SLA Violation Alert 🚨\n\n"
            f"High risk SLA violation detected!\n"
            f"Telemetry ID: {telemetry_id}\n"
            f"Risk Score: {risk_score:.2%}\n"
            f"Timestamp: {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Please investigate immediately."
        )
        
        await self._send_alerts(message, "SLA Violation", telemetry_id)
    
    async def send_anomaly_alert(self, anomaly_score: float):
        """Send anomaly detection alert."""
        # Rate limiting
        now = datetime.now()
        if (self.last_anomaly_alert and 
            (now - self.last_anomaly_alert).seconds < self.alert_cooldown):
            return
        
        if anomaly_score < self.config['anomaly_threshold']:
            return
        
        self.last_anomaly_alert = now
        
        message = (
            f"⚠️ Anomaly Detection Alert ⚠️\n\n"
            f"Network anomaly detected!\n"
            f"Anomaly Score: {anomaly_score:.3f}\n"
            f"Timestamp: {now.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Please check network conditions."
        )
        
        await self._send_alerts(message, "Network Anomaly", None)
    
    async def _send_alerts(self, message: str, alert_type: str, telemetry_id: Optional[int]):
        """Send alerts via configured channels."""
        tasks = []
        
        if 'telegram' in self.config['channels']:
            tasks.append(self._send_telegram_alert(message))
        
        if 'email' in self.config['channels']:
            tasks.append(self._send_email_alert(message, alert_type))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_telegram_alert(self, message: str):
        """Send alert via Telegram bot."""
        if not self.config['telegram_bot_token'] or not self.config['telegram_chat_id']:
            logger.warning("Telegram credentials not configured")
            return
        
        try:
            url = f"https://api.telegram.org/bot{self.config['telegram_bot_token']}/sendMessage"
            data = {
                'chat_id': self.config['telegram_chat_id'],
                'text': message,
                'parse_mode': 'HTML'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data)
                response.raise_for_status()
                logger.info("Telegram alert sent successfully")
                
        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {str(e)}")
    
    async def _send_email_alert(self, message: str, subject: str):
        """Send alert via email."""
        if not all([self.config['email_user'], self.config['email_password'], self.config['alert_email']]):
            logger.warning("Email credentials not configured")
            return
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config['email_user']
            msg['To'] = self.config['alert_email']
            msg['Subject'] = f"SLA Platform Alert: {subject}"
            
            # Add body
            msg.attach(MIMEText(message, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
            server.starttls()
            server.login(self.config['email_user'], self.config['email_password'])
            text = msg.as_string()
            server.sendmail(self.config['email_user'], self.config['alert_email'], text)
            server.quit()
            
            logger.info("Email alert sent successfully")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {str(e)}")
    
    async def test_alerts(self):
        """Test alert functionality."""
        test_message = (
            f"🧪 Test Alert 🧪\n\n"
            f"This is a test alert from the SLA Violation Prediction platform.\n"
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"If you receive this message, alerts are working correctly."
        )
        
        await self._send_alerts(test_message, "Test Alert", None)
        logger.info("Test alerts sent")

