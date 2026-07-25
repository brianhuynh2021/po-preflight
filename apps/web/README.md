# Preflight Web Prototype

This application is the interactive customer-facing prototype for PO Preflight. It is intentionally backed by realistic synthetic data so the complete workflow can be demonstrated without customer credentials or an ERP connection.

## Demonstrated workflows

- Operations overview and attention queue
- Searchable purchase-order queue
- Order header and normalized line-item review
- Catalog, price, inventory, and unknown-SKU findings
- Controlled approval with a required exception note
- Change requests and blocked-order behavior
- Upload interaction and processing confirmation
- Catalog, validation-rule, and audit-log views

## Run locally

```bash
npm install
npm run dev
```

Open the local URL printed by the development server.

## Validate

```bash
npm test
```

This prototype does not persist browser actions after a reload and does not call the production Preflight API. The production application will replace the synthetic in-memory data with authenticated API calls.
