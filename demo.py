import asyncio
import uuid

from confidence.confidence import Confidence


async def get_flag():
    root = Confidence("API_CLIENT")
    random_uuid = uuid.uuid4()
    uuid_string = str(random_uuid)
    confidence = root.with_context({"targeting_key": uuid_string})
    confidence.with_context({"app": "python"}).track("navigate", {})
    print("Tracked navigate event")

    value = confidence.resolve_string_details("hawkflag.color", "False")
    print(f"Flag value: {value}")


# Another asynchronous function that calls the first one
async def main():
    await get_flag()
    print("Finished calling get_flag")
    await asyncio.sleep(5)
    print("Finished sleeping for 1 seconds")


def sync_main():
    print("Running main asynchronously")


# Run the main function using asyncio.run (Python 3.7+)
if __name__ == "__main__":
    asyncio.run(main())
    sync_main()
