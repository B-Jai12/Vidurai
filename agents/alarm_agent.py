import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS  = os.getenv("EMAIL_ADDRESS", "jaideep.botla12@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "mangoisdoggo")


# ── EMAIL HELPER ──────────────────────────────────────────────────────────────

def send_email(to_email: str, subject: str, body_html: str) -> bool:
    """Send an HTML email. Returns True on success."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = EMAIL_ADDRESS
        msg["To"]      = to_email

        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())

        return True

    except Exception as e:
        print(f"Email error: {e}")
        return False


# ── REFILL REMINDER ───────────────────────────────────────────────────────────

def send_refill_reminder(medicine_name: str, days_left: int, to_email: str | None = None) -> dict:
    """Send a refill reminder email. Returns dict with 'email' bool."""
    results = {"email": False}

    if not to_email:
        return results

    subject = f"💊 Refill Reminder — {medicine_name}"
    body    = f"""
    <div style="font-family:Arial,sans-serif;max-width:500px;margin:auto;
                border:1px solid #2D3748;border-radius:12px;overflow:hidden;">
        <div style="background:#1A73E8;padding:20px;text-align:center;">
            <h2 style="color:white;margin:0;">💊 Vidur — Refill Reminder</h2>
        </div>
        <div style="padding:24px;background:#1A1A2E;color:#E2E8F0;">
            <p style="font-size:16px;">Hello,</p>
            <p>Your medicine <strong style="color:#63B3ED;">{medicine_name}</strong> needs a refill soon.</p>
            <div style="background:#2D3748;border-left:4px solid #FBBC04;
                        padding:12px 16px;border-radius:8px;margin:16px 0;color:#FEF3C7;">
                ⏰ <strong>{days_left} days</strong> of supply remaining
            </div>
            <p>Please visit your nearest pharmacy to refill on time.</p>
            <p style="color:#A0AEC0;font-size:13px;margin-top:24px;">
                — Vidur Team<br>
                <em>Not a substitute for professional medical advice.</em>
            </p>
        </div>
    </div>
    """
    results["email"] = send_email(to_email, subject, body)
    return results


# ── GENERIC SAVINGS ALERT ─────────────────────────────────────────────────────

def send_generic_savings_alert(medicines: list, to_email: str | None = None) -> dict:
    """Send a generic savings alert email. Returns dict with 'email' bool."""
    results = {"email": False}

    if not to_email or not medicines:
        return results

    rows = ""
    for med in medicines:
        saving = med.get("generic_cost_saving", "")
        if saving and saving != "Not specified":
            rows += f"""
            <tr>
                <td style="padding:10px;border-bottom:1px solid #2D3748;">
                    <strong style="color:#E2E8F0;">{med.get('name','')}</strong><br>
                    <small style="color:#A0AEC0;">Generic: {med.get('generic_name','N/A')}</small>
                </td>
                <td style="padding:10px;border-bottom:1px solid #2D3748;
                            color:#68D391;font-weight:600;">
                    {saving}
                </td>
            </tr>
            """

    if not rows:
        return results

    subject = "💰 Vidur — Generic Medicine Savings Available"
    body    = f"""
    <div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;
                border:1px solid #2D3748;border-radius:12px;overflow:hidden;">
        <div style="background:#34A853;padding:20px;text-align:center;">
            <h2 style="color:white;margin:0;">💰 Save on Your Medicines</h2>
        </div>
        <div style="padding:24px;background:#1A1A2E;color:#E2E8F0;">
            <p>You can save money by switching to <strong>generic equivalents</strong>
               for the following medicines:</p>
            <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                <thead>
                    <tr style="background:#2D3748;">
                        <th style="padding:10px;text-align:left;color:#E2E8F0;">Medicine</th>
                        <th style="padding:10px;text-align:left;color:#E2E8F0;">Saving</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
            <p>Ask your pharmacist for the generic version to save money without
               compromising your health.</p>
            <p style="color:#A0AEC0;font-size:13px;margin-top:24px;">
                — Vidur Team<br>
                <em>Always consult your doctor before switching medicines.</em>
            </p>
        </div>
    </div>
    """
    results["email"] = send_email(to_email, subject, body)
    return results


# ── REFILL STATUS (UI helper) ─────────────────────────────────────────────────

def show_refill_status(medicines: list) -> list:
    """Compute refill status for each medicine. Returns a list of status dicts."""
    status_list = []
    for med in medicines:
        try:
            duration = int(
                str(med.get("duration", "30"))
                .replace(" days", "").replace("days", "").strip()
            )
        except Exception:
            duration = 30

        end_date  = datetime.utcnow() + timedelta(days=duration)
        days_left = (end_date - datetime.utcnow()).days

        if days_left <= 5:
            status = "critical"
        elif days_left <= 10:
            status = "warning"
        else:
            status = "ok"

        status_list.append({
            "name":      med.get("name", ""),
            "days_left": days_left,
            "end_date":  end_date.strftime("%d %b %Y"),
            "status":    status,
            "saving":    med.get("generic_cost_saving", ""),
        })

    return status_list