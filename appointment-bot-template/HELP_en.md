# 📖 Help – Appointment Bot

## Commands
| Command | Action |
|---------|--------|
| `/start` | Main menu |
| `/help` | This guide |
| `/cancel` | Cancel booking |

## Booking Steps
1. Tap **"Book New Appointment"**
2. Choose a **service**
3. Enter the **number of individuals** (1–10)
4. Pick a **date** and a **time** slot
5. Enter your **name & phone** (only once; returning users are fast-tracked)
6. Tap **Confirm**

## My Appointments
Tap **"My Appointments"** to view your upcoming bookings. Past appointments remain
visible for **14 days** before being removed automatically.

## Admin Panel (admins only)
| Action | Description |
|--------|-------------|
| `/admin` | Open the admin panel |
| **Today's Bookings** | View today's appointments, numbered `1, 2, 3 …` per day |
| **Upcoming Bookings** | View all future appointments |
| **Cancel** | Via the cancel button on each booking card |
| **Import Services** | Upload an `.xlsx` / `.csv` file (`title`, `duration_minutes`, `is_active`) |

## Retention Policy
| Scope | Duration |
|-------|----------|
| Admin / general archive | 7 days |
| User history | 14 days |
| Auto-cleanup | Daily at midnight |

## Language
The bot language is set in `.env` via `DEFAULT_LANGUAGE` (`en` or `ar`).
