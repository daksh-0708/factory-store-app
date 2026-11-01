import io
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Factory Store | ફેક્ટરી સ્ટોર", page_icon="🏭", layout="wide")

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; max-width: 1250px;}
div[data-testid="stMetric"] {background: #f4f7fb; padding: 12px; border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

st.title("🏭 Factory Store Management")
st.caption("Material Inward Register | મટિરિયલ આવક રજિસ્ટર")

# Configure these values in Streamlit Cloud -> App settings -> Secrets.
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]  # Use Supabase publishable/anon key, NOT service_role.
except Exception:
    st.error("Configuration missing. Add SUPABASE_URL and SUPABASE_KEY in Streamlit Secrets.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Individual staff login through Supabase Auth.
if "auth_tokens" not in st.session_state:
    st.session_state.auth_tokens = None

if not st.session_state.auth_tokens:
    st.subheader("Login | લૉગિન")
    email = st.text_input("Work email | કર્મચારી ઈમેલ")
    password = st.text_input("Password | પાસવર્ડ", type="password")
    if st.button("Login / પ્રવેશ", type="primary"):
        try:
            auth_result = supabase.auth.sign_in_with_password(
                {"email": email.strip(), "password": password}
            )
            st.session_state.auth_tokens = {
                "access_token": auth_result.session.access_token,
                "refresh_token": auth_result.session.refresh_token,
            }
            st.rerun()
        except Exception:
            st.error("Login failed. Check your email and password. | ઈમેલ અથવા પાસવર્ડ તપાસો.")
    st.info("દરેક કર્મચારી માટે Supabase Authentication માં અલગ account બનાવો.")
    st.stop()

try:
    supabase.auth.set_session(
        st.session_state.auth_tokens["access_token"],
        st.session_state.auth_tokens["refresh_token"]
    )
except Exception:
    st.session_state.auth_tokens = None
    st.warning("Session expired. Please login again. | સેશન પૂર્ણ થયું છે.")
    st.rerun()

with st.sidebar:
    st.header("Menu | મેનુ")
    page = st.radio(
        "Choose page",
        ["Dashboard | ડેશબોર્ડ", "New Inward Entry | નવી એન્ટ્રી", "Search Records | રેકોર્ડ શોધો"]
    )
    st.divider()
    st.caption("Liquid Ring Vacuum Pump Manufacturing")
    if st.button("Logout | બહાર નીકળો"):
        try:
            supabase.auth.sign_out()
        finally:
            st.session_state.auth_tokens = None
            st.rerun()

def fetch_entries():
    result = (
        supabase.table("material_entries")
        .select("*")
        .order("id", desc=True)
        .limit(5000)
        .execute()
    )
    return pd.DataFrame(result.data or [])

def upload_bill(uploaded_file):
    if uploaded_file is None:
        return None
    now = datetime.now(ZoneInfo("Asia/Kolkata"))
    safe_name = uploaded_file.name.replace("/", "_").replace("\\", "_")
    path = f"{now:%Y/%m}/{now:%Y%m%d_%H%M%S}_{safe_name}"
    supabase.storage.from_("bills").upload(
        path,
        uploaded_file.getvalue(),
        file_options={"content-type": uploaded_file.type, "upsert": "false"}
    )
    return path

def money(value):
    try:
        return f"₹{float(value):,.2f}"
    except (TypeError, ValueError):
        return "₹0.00"

if page.startswith("Dashboard"):
    st.subheader("Dashboard | ડેશબોર્ડ")
    try:
        df = fetch_entries()
        if df.empty:
            st.info("No entries yet. Add the first material inward entry. | હજી કોઈ એન્ટ્રી નથી.")
        else:
            total_value = pd.to_numeric(df["total_price"], errors="coerce").fillna(0).sum()
            vendors = df["vendor_name"].fillna("").nunique()
            c1, c2, c3 = st.columns(3)
            c1.metric("Total inward entries | કુલ એન્ટ્રી", f"{len(df):,}")
            c2.metric("Total purchase value | કુલ કિંમત", money(total_value))
            c3.metric("Vendors | વેન્ડર", f"{vendors:,}")
            st.markdown("**Latest entries | તાજેતરની એન્ટ્રી**")
            display_cols = ["entry_date", "material_name", "quantity", "unit", "vendor_name",
                            "store_name", "brought_by", "bill_code", "total_price"]
            st.dataframe(df[[c for c in display_cols if c in df.columns]].head(15),
                         use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Could not load records: {e}")
        st.caption("Check that the SQL setup has been completed and the Supabase keys are correct.")

elif page.startswith("New Inward"):
    st.subheader("New Material Inward Entry | નવી મટિરિયલ એન્ટ્રી")
    st.caption("Fields marked * are required | * વાળા ફીલ્ડ જરૂરી છે")
    with st.form("inward_form", clear_on_submit=True):
        a, b = st.columns(2)
        material = a.text_input("Material name * | મટિરિયલનું નામ")
        quantity = b.number_input("Quantity * | જથ્થો", min_value=0.001, value=1.0, step=1.0)
        unit = a.selectbox("Unit | એકમ", ["Nos", "Kg", "Meter", "Liter", "Set", "Box", "Other"])
        vendor = b.text_input("Vendor name * | વેન્ડરનું નામ")
        address = st.text_area("Vendor address | વેન્ડરનું સરનામું")
        c, d = st.columns(2)
        store = c.text_input("Store name | કયા સ્ટોરમાંથી / કયા સ્ટોરમાં")
        brought_by = d.text_input("Brought by | કોણ લઈને આવ્યું")
        received_by = c.text_input("Received by | કોણે સ્વીકાર્યું")
        through = d.selectbox("Through | કયા માધ્યમથી આવ્યું",
                              ["Transport", "Courier", "Company vehicle", "Vendor delivery", "Self", "Other"])
        e, f = st.columns(2)
        unit_price = e.number_input("Unit price (₹) | એકમની કિંમત", min_value=0.0, step=10.0)
        bill_code = f.text_input("Bill number / code | બિલ નંબર / કોડ")
        bill_file = st.file_uploader("Upload bill | બિલ અપલોડ કરો", type=["pdf", "jpg", "jpeg", "png"])
        notes = st.text_area("Remarks | નોંધ")
        total_price = quantity * unit_price
        st.info(f"Total amount | કુલ રકમ: **{money(total_price)}**")
        save = st.form_submit_button("Save Entry | એન્ટ્રી સેવ કરો", type="primary", use_container_width=True)

    if save:
        if not material.strip() or not vendor.strip():
            st.error("Material name and Vendor name are required. | મટિરિયલ અને વેન્ડરનું નામ જરૂરી છે.")
        else:
            bill_path = None
            try:
                now = datetime.now(ZoneInfo("Asia/Kolkata"))
                if bill_file is not None:
                    bill_path = upload_bill(bill_file)
                record = {
                    "entry_date": now.date().isoformat(),
                    "entry_time": now.strftime("%H:%M:%S"),
                    "material_name": material.strip(),
                    "quantity": float(quantity),
                    "unit": unit,
                    "vendor_name": vendor.strip(),
                    "vendor_address": address.strip(),
                    "store_name": store.strip(),
                    "brought_by": brought_by.strip(),
                    "received_by": received_by.strip(),
                    "through": through,
                    "unit_price": float(unit_price),
                    "total_price": float(total_price),
                    "bill_code": bill_code.strip(),
                    "bill_path": bill_path,
                    "notes": notes.strip(),
                }
                supabase.table("material_entries").insert(record).execute()
                st.success("Entry saved successfully! | એન્ટ્રી સફળતાપૂર્વક સેવ થઈ.")
            except Exception as e:
                st.error(f"Save failed: {e}")
                st.warning("If bill upload succeeded but saving failed, an unused file may remain in Storage.")

elif page.startswith("Search Records"):
    st.subheader("Search Material Records | મટિરિયલ રેકોર્ડ શોધો")
    try:
        df = fetch_entries()
        if df.empty:
            st.info("No records found. | કોઈ રેકોર્ડ મળ્યો નથી.")
        else:
            x, y = st.columns(2)
            query = x.text_input("Search material / vendor / bill code | શોધો")
            date_from = y.date_input("From date | શરૂઆતની તારીખ", value=None)
            date_to = st.date_input("To date | અંતિમ તારીખ", value=None)
            if query:
                fields = ["material_name", "vendor_name", "bill_code", "brought_by", "received_by"]
                mask = pd.Series(False, index=df.index)
                for col in fields:
                    mask |= df[col].fillna("").astype(str).str.contains(query, case=False, regex=False)
                df = df[mask]
            if date_from:
                df = df[df["entry_date"] >= date_from.isoformat()]
            if date_to:
                df = df[df["entry_date"] <= date_to.isoformat()]

            st.write(f"Records found | મળેલા રેકોર્ડ: **{len(df)}**")
            show_cols = ["id", "entry_date", "entry_time", "material_name", "quantity", "unit",
                         "vendor_name", "vendor_address", "store_name", "brought_by", "received_by",
                         "through", "unit_price", "total_price", "bill_code", "notes"]
            st.dataframe(df[[c for c in show_cols if c in df.columns]],
                         use_container_width=True, hide_index=True)

            excel = io.BytesIO()
            with pd.ExcelWriter(excel, engine="openpyxl") as writer:
                df.drop(columns=["bill_path"], errors="ignore").to_excel(writer, index=False, sheet_name="Material Inward")
            st.download_button(
                "Download Excel | Excel ડાઉનલોડ",
                data=excel.getvalue(),
                file_name="Factory_Material_Inward.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )

            st.markdown("**Bill files | બિલ ફાઇલો**")
            bill_rows = df[df["bill_path"].notna() & (df["bill_path"].astype(str) != "")]
            if bill_rows.empty:
                st.caption("No bill uploaded for these records. | બિલ અપલોડ કરેલ નથી.")
            for _, row in bill_rows.iterrows():
                label = f"Entry #{row['id']} — {row.get('bill_code') or row.get('material_name')}"
                if st.button(f"Create secure bill link: {label}", key=f"bill_{row['id']}"):
                    try:
                        signed = supabase.storage.from_("bills").create_signed_url(str(row["bill_path"]), 300)
                        url = signed.get("signedURL") or signed.get("signedUrl")
                        if url:
                            st.link_button("Open bill (link valid for 5 minutes) | બિલ ખોલો", url)
                        else:
                            st.error("Could not create bill link.")
                    except Exception as e:
                        st.error(f"Bill link error: {e}")
    except Exception as e:
        st.error(f"Could not load records: {e}")
        st.caption("Check database setup, RLS policy and Supabase configuration.")
