# main.py
# نقطة الدخول للبوت (وضع Reply Keyboard)
# يعتمد على NavigationState لإدارة حالة التنقل لكل مستخدم

import os
import asyncio
import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from bot.config import BOT_TOKEN
from bot.db import init_db
from .handlers import (
    start,
    echo_handler,
    insert_sub_conv,
    ingestion_handler,
    insert_group_conv,
    admins_conv,
    approvals_handler,
    approval_callback,
    moderation_handler,
)
from .jobs import purge_temp_archives
from datetime import time

# --------------------------------------------------------------------------
# إعداد التسجيل لرؤية الرسائل التفصيلية
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# --------------------------------------------------------------------------
def main():
    # سياسة loop مناسبة لويندوز
    if os.name == "nt":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        except Exception:
            pass

    # تأكد من وجود event loop للـ MainThread (مهم لبايثون 3.12)
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # تهيئة قاعدة البيانات
    loop.run_until_complete(init_db())

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(insert_group_conv)
    app.add_handler(admins_conv)
    app.add_handler(insert_sub_conv)
    app.add_handler(approvals_handler)
    app.add_handler(approval_callback)
    app.add_handler(
        MessageHandler(filters.ALL & filters.ChatType.GROUPS, moderation_handler),
        group=-1,
    )
    app.add_handler(
        MessageHandler(filters.Entity("hashtag"), ingestion_handler),
        group=1,
    )
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_handler))

    app.job_queue.run_daily(purge_temp_archives, time=time(hour=0, minute=0))

    print("✅ Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\nBot stopped by user")
