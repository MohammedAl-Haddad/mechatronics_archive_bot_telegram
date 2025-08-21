import asyncio
import json

from bot.seed_loader import (
    load_structure,
    load_years_and_lecturers,
    load_materials,
)


async def main():
    payload = json.load(open("seed_data.json", encoding="utf-8"))
    await load_structure(payload["levels"])
    await load_years_and_lecturers(payload["years"], payload["lecturers"])
    await load_materials(payload["materials"])


if __name__ == "__main__":
    asyncio.run(main())

