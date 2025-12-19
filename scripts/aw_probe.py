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

def find_afk_bucket_id(client: ActivityWatchClient) -> str:
    buckets = client.get_buckets()
    for bucket_id in buckets.keys():
        if bucket_id.startswith("aw-watcher-afk_"):
            return bucket_id
    raise RuntimeError("no aw-watcher-afk bucket found; is aw-watcher-afk running?")

def get_afk_fraction(client: ActivityWatchClient, minutes: int) -> float:
    end = datetime.now().astimezone()
    start = end - timedelta(minutes=minutes)

    try:
        bucket_id = find_afk_bucket_id(client)
    except RuntimeError:
        # no afk watcher; treat as 0% afk so we don't break
        return 0.0

    events = client.get_events(bucket_id=bucket_id, start=start, end=end)

    total_window_seconds = minutes * 60.0
    afk_seconds = 0.0

    for e in events:
        data = getattr(e, "data", {}) or {}
        status = data.get("status", "not-afk")

        duration = getattr(e, "duration", None)
        if duration is None:
            continue

        seconds = (
            duration.total_seconds()
            if hasattr(duration, "total_seconds")
            else float(duration)
        )

        # for safety, treat anything that isn't explicit "not-afk" as afk-ish
        if status != "not-afk":
            afk_seconds += seconds

    if total_window_seconds <= 0:
        return 0.0

    return min(1.0, afk_seconds / total_window_seconds)

def get_events_last_minutes(minutes: int):
    # identify this client to the activitywatch server
    client = ActivityWatchClient("waifucop_probe", testing=False)
    client.connect()

    afk_frac = get_afk_fraction(client, minutes)
    print(f"afk fraction for last {minutes} min: {afk_frac:.2f}")

    # if user was afk for > 50% of the window, bail out
    if afk_frac > 0.5:
        print("mostly afk this interval; skipping nag.")
        return

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
    if not events:
            print("no events for this interval (afk or empty); skipping nag.")
            return

    summary = summarize_events(events)

    print(summary)
    # print(f"activity summary for last {minutes} minutes:\n")
    nag = query_local_llm(summary)
    print(nag)
    # this is for discord webhook
    # send_discord_message(nag)
    # This is for standard modal pop-up window.
    show_waifu_popup("happy_waifu.png",nag)


if __name__ == "__main__":
    main(minutes)
