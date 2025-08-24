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

from bot.config import BOT_TOKEN, OWNER_TG_ID
from bot.db import init_db, ensure_owner_full_perms
from .handlers import (
    start,
    echo_handler,
    insert_sub_conv,
    insert_sub_private,
    ingestion_handler,
    insert_group_conv,
    insert_group_private,
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
        except Exception as e:
            logging.debug("windows policy failed: %s", e)

    # تأكد من وجود event loop للـ MainThread (مهم لبايثون 3.12)
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # تهيئة قاعدة البيانات وضمان صلاحيات المالك
    loop.run_until_complete(init_db())
    loop.run_until_complete(ensure_owner_full_perms(OWNER_TG_ID))

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # أوامر خاصة
    app.add_handler(CommandHandler("start", start, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("insert_group", insert_group_private, filters.ChatType.PRIVATE))
    app.add_handler(CommandHandler("insert_sub", insert_sub_private, filters.ChatType.PRIVATE))

    # أوامر المجموعات
    app.add_handler(insert_group_conv)
    app.add_handler(insert_sub_conv)

    # أوامر المشرفين
    app.add_handler(admins_conv)
    app.add_handler(approvals_handler)
    app.add_handler(approval_callback)
    app.add_handler(
        MessageHandler(filters.ALL & filters.ChatType.GROUPS, moderation_handler),
        group=-1,
    )
    app.add_handler(
        MessageHandler(
            filters.ChatType.GROUPS
            & (filters.Regex("#") | filters.CaptionRegex("#"))
            & ~filters.COMMAND,
            ingestion_handler,
        ),
        group=1,
    )
    app.add_handler(
        MessageHandler(
            filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, echo_handler
        )
    )

    app.job_queue.run_daily(purge_temp_archives, time=time(hour=0, minute=0))

    print(
        "\n".join(
            [
                "📟 bot wiring:",
                "  /start -> private",
                "  /insert_group -> groups",
                "  /insert_sub -> groups",
                "  /approvals -> private",
                "  /admins -> private",
                "  ingestion (#) -> groups",
                "  unknown-text -> private only",
            ]
        )
    )
    app.run_polling()


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\nBot stopped by user")
