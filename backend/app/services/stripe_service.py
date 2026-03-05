import stripe
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.shop import Shop

stripe.api_key = settings.STRIPE_SECRET_KEY


async def create_customer(shop: Shop) -> str:
    customer = stripe.Customer.create(email=shop.email, name=shop.name)
    return customer.id


async def create_checkout_session(customer_id: str, success_url: str, cancel_url: str) -> str:
    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": settings.STRIPE_PRICE_ID, "quantity": 1}],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.url


async def create_portal_session(customer_id: str, return_url: str) -> str:
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )
    return session.url


async def cancel_subscription(subscription_id: str) -> None:
    stripe.Subscription.cancel(subscription_id)


async def handle_webhook_event(payload: bytes, sig_header: str, db: AsyncSession) -> None:
    from sqlalchemy import select
    from app.models.shop import Shop

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (stripe.error.SignatureVerificationError, ValueError):
        raise ValueError("Invalid webhook signature")

    data = event["data"]["object"]
    event_type = event["type"]

    subscription_id = None
    customer_id = None
    status = None

    if event_type == "checkout.session.completed":
        customer_id = data.get("customer")
        subscription_id = data.get("subscription")
        if subscription_id:
            sub = stripe.Subscription.retrieve(subscription_id)
            status = sub["status"]
    elif event_type in ("customer.subscription.updated", "customer.subscription.deleted", "customer.subscription.created"):
        subscription_id = data["id"]
        customer_id = data["customer"]
        status = data["status"]
    elif event_type == "invoice.payment_succeeded":
        subscription_id = data.get("subscription")
        customer_id = data["customer"]
        if subscription_id:
            sub = stripe.Subscription.retrieve(subscription_id)
            status = sub["status"]
    elif event_type == "invoice.payment_failed":
        subscription_id = data.get("subscription")
        customer_id = data["customer"]
        status = "past_due"

    if customer_id:
        result = await db.execute(select(Shop).where(Shop.stripe_customer_id == customer_id))
        shop = result.scalar_one_or_none()
        if shop:
            if subscription_id:
                shop.stripe_subscription_id = subscription_id
            if status:
                shop.subscription_status = status
            await db.commit()
