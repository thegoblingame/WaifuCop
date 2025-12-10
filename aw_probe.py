import sys
from datetime import datetime, timedelta
from aw_client import ActivityWatchClient
from llama_query import query_local_llm
# this is for discord webhook
from discord_notifier import send_discord_message
# This is for standard modal pop-up window. 
from waifu_popup import show_waifu_popup

try:
    minutes = int(sys.argv[1])
except (IndexError, ValueError):
    minutes = 60

def find_window_bucket_id(client: ActivityWatchClient) -> str:
    """
    find the aw-watcher-window bucket for this machine.
    if there are multiple, just pick the first one.
    """
    buckets = client.get_buckets()
    # buckets is a dict: {bucket_id: {...meta...}, ...}

    for bucket_id in buckets.keys():
        if bucket_id.startswith("aw-watcher-window_"):
            return bucket_id

    raise RuntimeError("no aw-watcher-window bucket found; is aw-watcher-window running?")


def get_events_last_minutes(minutes: int):
    # identify this client to the activitywatch server
    client = ActivityWatchClient("waifucop_probe", testing=False)
    client.connect()

    end = datetime.now().astimezone()
    start = end - timedelta(minutes=minutes)

    bucket_id = find_window_bucket_id(client)

    # fetch events from that bucket in the given time window
    events = client.get_events(
        bucket_id=bucket_id,
        start=start,
        end=end,
    )

    return events


def summarize_events(events):
    """
    turn raw events into a compact text summary for an llm prompt.
    bucket by (app, title) with total minutes.
    """
    buckets = {}  # (app, title) -> minutes

    for e in events:
        # aw_core.models.Event: has .data and .duration
        data = getattr(e, "data", {}) or {}
        app = data.get("app", "unknown_app")
        title = data.get("title", "unknown_title")

        duration = getattr(e, "duration", None)
        if duration is None:
            continue

        seconds = (
            duration.total_seconds()
            if hasattr(duration, "total_seconds")
            else float(duration)
        )
        minutes = seconds / 60.0

        if minutes <= 0.3:
            continue

        key = (app, title)
        buckets[key] = buckets.get(key, 0.0) + minutes

    lines = []
    for (app, title), mins in sorted(buckets.items(), key=lambda x: -x[1]):
        lines.append(f"{mins:.1f} min | app={app} | title={title}")

    return "\n".join(lines)


def main(minutes: int):

    events = get_events_last_minutes(minutes)
    summary = summarize_events(events)

    print(summary)
    # print(f"activity summary for last {minutes} minutes:\n")
    nag = query_local_llm(summary)
    print(nag)
    # this is for discord webhook
    # send_discord_message(nag)
    # This is for standard modal pop-up window.
    show_waifu_popup("dmg_waifu.png",nag)


if __name__ == "__main__":
    main(minutes)
