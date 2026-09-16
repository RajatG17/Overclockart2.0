EVENT_ROUTING_KEYS = {
    "InventoryReserved": "inventory.reserved",
    "InventoryReservationFailed": "inventory.reservation_failed",
    "InventoryReleased": "inventory.released",
}

def routing_key_for(event_type: str) -> str:
    try:
        return EVENT_ROUTING_KEYS[event_type]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported event type: {event_type}"
        ) from exc