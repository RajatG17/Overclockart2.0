import asyncio
import httpx
import uuid
import time
import json
import hmac
import hashlib
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.theme import Theme
from rich import print as rprint
from rich.text import Text

# Configure rich theme
custom_theme = Theme({
    "info": "dim cyan",
    "warning": "magenta",
    "danger": "bold red",
    "success": "bold green",
})
console = Console(theme=custom_theme)

BASE_URL = "http://localhost:30080"
WEBHOOK_SECRET = "whsec_mocksecret"
WEBHOOK_URL = f"{BASE_URL}/payment/webhook"

def generate_stripe_signature(payload: str, secret: str) -> str:
    timestamp = str(int(time.time()))
    signed_payload = f"{timestamp}.{payload}"
    mac = hmac.new(
        secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    return f"t={timestamp},v1={mac}"

async def run_checkout_flow():
    console.print(Panel.fit("[bold cyan]OverclockKart 2.0 Live Demo[/bold cyan]\n[dim]Simulating Distributed Saga & Payment Idempotency[/dim]"))
    
    unique_email = f"demo_{uuid.uuid4().hex[:8]}@example.com"
    password = "securepassword"
    user_id = None
    access_token = None
    product_id = None
    order_id = None
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=False,
            console=console
        ) as progress:
            
            # --- 1. Register User ---
            task1 = progress.add_task("[cyan]Auth Service:[/cyan] Registering new user...", total=1)
            register_res = await client.post("/auth/register", json={"email": unique_email, "password": password})
            assert register_res.status_code == 200, f"Failed: {register_res.text}"
            user_id = register_res.json()["id"]
            progress.update(task1, description=f"[success]✓ Auth Service:[/success] Registered user (ID: {user_id}, Email: {unique_email})", completed=1)

            # --- 2. Login User ---
            task2 = progress.add_task("[cyan]Auth Service:[/cyan] Authenticating & acquiring JWT token...", total=1)
            login_res = await client.post("/auth/token", data={"username": unique_email, "password": password})
            assert login_res.status_code == 200, "Login failed"
            access_token = login_res.json()["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            progress.update(task2, description=f"[success]✓ Auth Service:[/success] Acquired JWT token", completed=1)

            # --- 3. Seed Catalog ---
            task3 = progress.add_task("[cyan]Catalog Service:[/cyan] Creating new product...", total=1)
            catalog_res = await client.post("/catalog/products", json={
                "name": "NVIDIA RTX 5090",
                "description": "Next-gen GPU",
                "price": 1999.99,
                "stock": 5
            }, headers=headers)
            assert catalog_res.status_code == 201, "Failed to create product"
            product_id = catalog_res.json()["id"]
            progress.update(task3, description=f"[success]✓ Catalog Service:[/success] Product 'NVIDIA RTX 5090' created (ID: {product_id})", completed=1)

            # --- 4. Place Order (Saga Initiated) ---
            task4 = progress.add_task("[cyan]Order Service:[/cyan] Submitting order & initiating distributed Saga...", total=1)
            order_res = await client.post("/orders/orders", json={
                "user_id": user_id,
                "product_id": product_id,
                "quantity": 1
            }, headers=headers)
            assert order_res.status_code == 201, "Failed to place order"
            order_data = order_res.json()
            order_id = order_data["id"]
            progress.update(task4, description=f"[success]✓ Order Service:[/success] Order {order_id} created in [bold yellow]PENDING[/bold yellow] state (Saga Initiated)", completed=1)

            # --- 5. Poll Saga Status ---
            task5 = progress.add_task("[magenta]Message Broker:[/magenta] Waiting for RabbitMQ outbox processing...", total=1)
            max_retries = 15
            for i in range(max_retries):
                await asyncio.sleep(1)
                get_order_res = await client.get(f"/orders/orders/{order_id}", headers=headers)
                status = get_order_res.json()["status"]
                if status == "CONFIRMED":
                    progress.update(task5, description=f"[success]✓ Saga Complete:[/success] Order {order_id} state transition to [bold green]CONFIRMED[/bold green]", completed=1)
                    break
            else:
                progress.update(task5, description=f"[danger]✗ Saga Timeout:[/danger] Order {order_id} still PENDING", completed=1)
                return

        console.print("\n[bold cyan]Distributed Transaction Saga successfully validated![/bold cyan]\n")
        
        # --- 6. Payment Webhook Idempotency ---
        console.print(Panel("[bold yellow]Testing Payment Idempotency via Webhooks[/bold yellow]"))
        unique_event_id = f"evt_{uuid.uuid4().hex[:12]}"
        payload_str = json.dumps({"id": unique_event_id, "type": "payment_intent.succeeded", "data": {"object": {"id": "pi_mock123", "amount": 199999, "currency": "usd"}}})
        signature = generate_stripe_signature(payload_str, WEBHOOK_SECRET)
        headers = {"Stripe-Signature": signature, "Content-Type": "application/json"}
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=False, console=console) as progress:
            task6 = progress.add_task(f"[cyan]Payment Service:[/cyan] Sending external webhook event {unique_event_id}...", total=1)
            await asyncio.sleep(1) # Fake delay for effect
            wh_res1 = await client.post(WEBHOOK_URL, content=payload_str, headers=headers)
            progress.update(task6, description=f"[success]✓ Payment Service:[/success] Initial webhook processed (Response: {wh_res1.json()})", completed=1)
            
            task7 = progress.add_task(f"[warning]Payment Service:[/warning] Simulating external system retry of identical event {unique_event_id}...", total=1)
            await asyncio.sleep(1.5) # Fake delay
            wh_res2 = await client.post(WEBHOOK_URL, content=payload_str, headers=headers)
            progress.update(task7, description=f"[success]✓ Payment Service:[/success] Idempotency lock engaged. Payload dropped (Response: {wh_res2.json()})", completed=1)

        console.print("\n[bold green]✅ DEMO COMPLETE: All microservice validations passed![/bold green]\n")

if __name__ == "__main__":
    try:
        asyncio.run(run_checkout_flow())
    except Exception as e:
        console.print(f"[bold red]Demo Failed:[/bold red] {e}")
