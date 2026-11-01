# Factory Store – Material Inward Management

For Liquid Ring Vacuum Pump Manufacturing | English + Gujarati UI | Material inward register only (no stock tracking).

## Features
- Dashboard: inward entry count, total inward value, vendor count
- Material inward form: material, quantity, unit, vendor name/address, store, brought by, received by, delivery method, unit price, total, bill number, bill PDF/image, remarks
- Search by material, vendor, bill code, brought by, received by
- Date filtering and Excel export
- Private bill storage with short-lived signed links
- Individual email/password login for 5–10 staff members

## Files
- `app.py`: Streamlit application
- `setup.sql`: database, RLS policies and private Storage bucket
- `requirements.txt`: Python dependencies
- `secrets.toml.example`: secrets template

## Setup
1. Create a Supabase project.
2. Open Supabase SQL Editor and run `setup.sql`.
3. In Supabase Authentication settings, enable Email/Password sign-in.
4. In Supabase Authentication -> Users, create/invite an account for each staff member (5–10 people). Give each person their own email and password.
5. In Supabase Project Settings / API, copy Project URL and publishable (or legacy anon) key. Never use the service_role/secret key in this app.
6. Create a GitHub repository and upload `app.py`, `requirements.txt`, and `setup.sql`. Do not upload secrets.
7. In Streamlit Community Cloud, deploy the repository with `app.py` as the main file.
8. In Streamlit app Settings -> Secrets, add the values shown in `secrets.toml.example`.
9. Reboot the app and test with one staff account before inviting the rest.

## Local run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Security
The database and Storage policies allow authenticated users only. Each employee signs in using an individual Supabase Auth account. The app uses the Supabase publishable/anon key; never expose a service_role key. This is a useful starter app, but before production use, test account access, backups, and staff offboarding. All authenticated staff currently share the same read/add permissions; role-based permissions and edit/delete audit trails are not included.
