# BarberTime Requirements

## Problem

Walk-in customers often arrive at a barbershop only to face a 20+ minute wait with no prior warning. Most people would rather skip the visit entirely than wait — but they also don't want the commitment of a booked appointment.

## Core Idea

A lightweight app that lets barbershops broadcast their **current availability and live wait time** to nearby walk-in customers, so customers can decide whether to show up before leaving the house.

## Key Principles

- No appointments — walk-in culture is preserved
- Real-time: wait times must reflect the shop's current state
- Simple for barbers to update (they are busy cutting hair)
- Simple for customers to check (one glance should be enough)

---

## Primary Users

- **Barbershops**: manage their shop, staff, queue, and promotions
- **Customers**: check nearby shops and walk in informed — free, no account required to browse

---

## Business Model

- **Free** for customers
- **Paid subscription** for barbershops via Stripe
  - Price: €15–€20 / month
  - Barbers manage their subscription on a web dashboard (upgrade, cancel, update payment)
  - Stripe API key must be configurable via environment config (not hardcoded)

---

## Core Features

### Barbershop Web Dashboard

- Register and log in to a shop account
- Manage Stripe subscription (subscribe, change plan, cancel)
- Configure shop profile:
  - Shop name, location, opening hours
  - Profile photo
  - Description
  - Price list
- Create and manage employee profiles:
  - Name, photo, role
  - Individual wait time per employee (customers can check wait for a specific barber)
- Update current shop status: open / busy / closed
- Set estimated wait time manually
- Post flash discounts visible to customers (e.g. "Bring a friend – 50% off, next 2 spots only")

### Smart Queue Suggestion

- The system tracks historical queue data per shop and per barber
- On demand or automatically, it suggests a recommended wait time based on past averages (e.g. time of day, day of week)
- Barber can accept the suggestion or override it manually
- Goal: reduce the effort of keeping wait times accurate without removing control

### Real-Time Wait Times

- Wait times update as close to real-time as possible
- Both shop-level and per-employee wait times displayed to customers

### Slot Reservation (Walk-in Intent)

- Customers can reserve the next available slot if they commit to arriving within ~10–15 minutes
- Reservation holds their place in the queue without a formal appointment
- **Anti-abuse: phone number input + rate limiting**
  - Customer enters their phone number to reserve (no SMS sent)
  - Limited to 1 active reservation per phone number per day
  - If they no-show, the slot is released after the window expires
  - Upgrade to SMS OTP only if abuse becomes a real problem after launch

### Flash Discounts

- Barbers can create time-limited or quantity-limited deals
- Example: "Bring a friend – 50% off" or "Next walk-in gets 20% off"
- Shown prominently to customers browsing nearby shops

### Customer-Facing Web App

- Progressive web app (PWA) — no download required
- Browse nearby barbershops (list or map)
- See real-time wait time per shop and per barber
- View shop profile: photo, description, price list, staff
- See active flash discounts
- Reserve next slot with phone number (rate-limited)
- Free, no account required to browse

---

## Configuration

- Stripe API key and secrets stored in `.env`, not hardcoded
- Configurable: reservation window (default 10–15 min), rate limit rules, subscription price tiers

---

## Deployment

- **Single VPS** (e.g. Hetzner CX22, ~€4–6/month)
  - Germany-based: low latency, GDPR-friendly
  - Deployed via Docker
- Revisit cloud scaling only when there are paying customers
- Target running cost: under €10/month at early stage

---

## Customer Acquisition (Separate Tool — Not Part of Main App)

A standalone crawler/outreach tool to find barbershops in Germany and send cold emails with a demo link.

### Approach

- Source data from structured sources (Google Maps API, `gelbeseiten.de`, `yelp.de`)
- Offer a free trial month in every email to lower the barrier
- Start with 20–30 manual sends to refine the pitch before automating

### Legal Compliance (Germany)

- Every email must include: sender's full name, address, and a clear unsubscribe option
- B2B cold email to a public business contact is generally tolerated under UWG if relevant and compliant
- Mass sending without compliance = risk of *Abmahnungen*

### Deliverability

- Dedicated sending domain (not the main product domain)
- SPF, DKIM, DMARC configured before any sending
- Warm up the domain before bulk sends

---

## Open Questions

- Tech stack (backend language, frontend framework, database)
- Map provider for customer-facing shop search (Google Maps API vs. OpenStreetMap/Mapbox)
