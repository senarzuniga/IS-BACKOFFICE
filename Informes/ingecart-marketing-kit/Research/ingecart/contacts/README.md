# Ingecart — Key Contacts

## Overview

This directory stores contact records for Ingecart stakeholders (management,
commercial, technical, and administrative) relevant to IAR's engagement.

> **Privacy:** All contact data stored here is limited to professional
> roles and publicly available or legitimately obtained information.

---

## Contact Register

| Name | Role | Department | Email | Phone | LinkedIn | Source |
|------|------|-----------|-------|-------|---------|--------|
| (Dirección General) | General Management | Executive | — | — | — | Pending |
| (Dirección Comercial) | Commercial Director | Sales | — | — | — | Pending |
| (Dirección Técnica) | Technical Director | Engineering | — | — | — | Pending |

---

## Contact Files

Naming convention: `ingecart_contact_ROLE.json`

Files are populated as contact information is confirmed and validated.

---

## Integration with Supabase

Contact records are synced to the `ingecart_contacts` Supabase table.
Run `python db/seeders/seed_ingecart.py --source contacts` to sync.
