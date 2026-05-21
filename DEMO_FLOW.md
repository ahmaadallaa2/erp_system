# Demo Flow

Short same-day MVP demo path.

## Core Flow

1. Log in with a user assigned to a company and branch.
2. Open Partners and create a supplier.
3. Open Products and create a stock product.
4. Open Warehouses and create a warehouse.
5. Open Purchase Invoices and create a draft purchase invoice for the supplier.
6. Add the product as a purchase invoice line.
7. Post the purchase invoice.
8. Open Stock Balances and confirm stock increased.
9. Open Partners and create a customer.
10. Open Sales Invoices and create a draft sales invoice for the customer.
11. Add the product as a sales invoice line.
12. Post the sales invoice.
13. Open Stock Balances and confirm stock decreased.
14. Open Payments and create an inbound customer payment.
15. Post the inbound payment.
16. Open Payments and create an outbound supplier payment.
17. Post the outbound payment.
18. Open Dashboard and review sales, purchases, inventory, receivable, payable,
    and low-stock summary values.
19. From a posted invoice or payment, open the linked journal entry drill-down.

## Reversal Flow

1. Cancel a posted sales invoice through the backend API or admin action and show
   the cancelled status, reversing journal entry, and stock restoration.
2. Cancel a posted purchase invoice through the backend API or admin action and
   show the cancelled status, reversing journal entry, and stock reduction.
3. Cancel a posted payment through the backend API or admin action and show the
   cancelled status and reversing journal entry.

## Notes

- Frontend pages expose posting and journal drill-down links.
- Frontend cancel buttons are not exposed yet; use API/admin for reversal demo.
