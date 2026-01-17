"""
Telegram Notifier
Handles Telegram notifications and confirmations
"""

import asyncio
from typing import Optional
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes


class TelegramNotifier:
    """Handles Telegram notifications and user confirmations"""
    
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.bot = Bot(token=token)
        self.confirmation_response = None
        self.confirmation_event = None
    
    async def send_message(self, message: str) -> bool:
        """
        Send a message via Telegram
        
        Args:
            message: Message text to send
            
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message
            )
            return True
        except Exception as e:
            print(f"Error sending Telegram message: {e}")
            return False
    
    async def request_confirmation(
        self,
        message: str,
        timeout_minutes: int = 15
    ) -> bool:
        """
        Request user confirmation via Telegram with approve/decline buttons
        
        Args:
            message: Confirmation message
            timeout_minutes: Timeout in minutes
            
        Returns:
            True if approved, False if declined or timeout
        """
        try:
            # Create inline keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✅ Approve", callback_data="approve"),
                    InlineKeyboardButton("❌ Decline", callback_data="decline")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            # Reset confirmation state
            self.confirmation_response = None
            self.confirmation_event = asyncio.Event()
            
            # Send message with buttons
            sent_message = await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                reply_markup=reply_markup
            )
            
            # Create application for handling callbacks
            application = Application.builder().token(self.token).build()
            
            # Add callback handler
            application.add_handler(
                CallbackQueryHandler(self._handle_confirmation_callback)
            )
            
            # Start application
            await application.initialize()
            await application.start()
            
            # Wait for response with timeout
            try:
                await asyncio.wait_for(
                    self.confirmation_event.wait(),
                    timeout=timeout_minutes * 60
                )
                result = self.confirmation_response == "approve"
            except asyncio.TimeoutError:
                await self.send_message("⏱️ Confirmation timeout - operation cancelled")
                result = False
            finally:
                # Cleanup
                await application.stop()
                await application.shutdown()
            
            # Edit message to remove buttons
            try:
                status = "✅ Approved" if result else "❌ Declined"
                await self.bot.edit_message_text(
                    chat_id=self.chat_id,
                    message_id=sent_message.message_id,
                    text=f"{message}\n\n{status}"
                )
            except:
                pass
            
            return result
            
        except Exception as e:
            print(f"Error requesting confirmation: {e}")
            return False
    
    async def _handle_confirmation_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle confirmation button callback"""
        query = update.callback_query
        await query.answer()
        
        self.confirmation_response = query.data
        self.confirmation_event.set()
    
    async def send_file(self, file_path: str, caption: Optional[str] = None) -> bool:
        """
        Send a file via Telegram
        
        Args:
            file_path: Path to file to send
            caption: Optional caption for the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(file_path, 'rb') as file:
                await self.bot.send_document(
                    chat_id=self.chat_id,
                    document=file,
                    caption=caption
                )
            return True
        except Exception as e:
            print(f"Error sending file: {e}")
            return False
    
    async def send_progress_update(self, current: int, total: int, operation: str):
        """
        Send a progress update message
        
        Args:
            current: Current item number
            total: Total number of items
            operation: Description of the operation
        """
        percentage = (current / total) * 100
        message = f"📊 {operation}\nProgress: {current}/{total} ({percentage:.1f}%)"
        
        await self.send_message(message)
