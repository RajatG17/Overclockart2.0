EVENT_ROUTING_KEYS = {
    "OrderCreated": "order.created",
    "InventoryReservationRequested": "inventory.reserve.requested",
    "PaymentRequested": "payment.requested",
    "InventoryReleaseRequested": "inventory.release.requested",
}

def routing_key_for(event_type: str) -> str:
    try:
        return EVENT_ROUTING_KEYS[event_type]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported event type: {event_type}"
        ) from exc