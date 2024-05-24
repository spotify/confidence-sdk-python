import uuid
from confidence.confidence import *
import asyncio
import time


def get_flag():
    root = Confidence("API_KEY")
    random_uuid = uuid.uuid4()
    uuid_string = str(random_uuid)
    confidence = root.with_context({"targeting_key": uuid_string})
    confidence.track("navigate", {})

    value = confidence.resolve_string_details("hawkflag.color", "false")
    print(f"Flag value: {value}")


# Another asynchronous function that calls the first one
async def main():
    get_flag()
    print("Finished calling say_hello again")
    get_flag()
    time.sleep(5)


# Run the main function using asyncio.run (Python 3.7+)
if __name__ == "__main__":
    asyncio.run(main())
