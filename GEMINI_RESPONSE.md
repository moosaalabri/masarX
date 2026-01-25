Plan:

1.  **Add Configuration:** I have added a new field `enable_payment` (checkbox) to the **Platform Profile** model.
2.  **Enforce Logic:** I updated the payment initiation view (`initiate_payment`) to check this flag. If disabled, users cannot start a payment.
3.  **Update UI:** I updated the **Shipper Dashboard** to hide the "Pay Now" button if payments are disabled.
4.  **Deploy:** Created migrations and restarted the server.

Changed (if any):

*   `core/models.py`: Added `enable_payment` boolean field to `PlatformProfile`.
*   `core/views.py`: Added a check in `initiate_payment` to block payments if disabled.
*   `core/templates/core/shipper_dashboard.html`: Wrapped the "Pay Now" button in a conditional check.

Notes:

*   **Action Required:** Go to **Django Admin > Platform Profiles**. You will see a new checkbox **Enable Payment**.
    *   **Checked:** Users can pay.
    *   **Unchecked:** The "Pay Now" button disappears, and direct URL access is blocked.

Next: You can test this by toggling the checkbox in the admin and refreshing your dashboard. What's next?

Reminder: click Save in the editor to sync changes.