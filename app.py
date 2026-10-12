"""DocuSense - Streamlit UI. All logic lives in src/; this file only wires the interface."""
import json
import os

import pandas as pd
import plotly.express as px
import streamlit as st

from src import database
from src.anomaly_detection import DEFAULT_MODEL_PATH, MIN_TRAIN_RECORDS, load_model
from src.demo_data import demo_records
from src.document_loader import DocumentError
from src.duplicate_detection import find_duplicates
from src.evaluation import validation_outcomes
from src.field_extraction import FIELD_NAMES
from src.ocr_engine import OCRUnavailableError, configure_tesseract, tesseract_available
from src.pipeline import process_document, screen_record, to_db_record
from src.screening import DISCLAIMER
from src.utils import parse_amount, parse_date

DB_PATH = os.environ.get("DOCUSENSE_DB", database.DEFAULT_DB)
AMOUNTS = ("subtotal", "tax", "total")
DATES = ("invoice_date", "due_date")

st.set_page_config(page_title="DocuSense", page_icon="🧾", layout="wide")


def get_conn():
    return database.connect(DB_PATH)


def _cmp(named):
    """Side-by-side field table with string values (Arrow-safe)."""
    return pd.DataFrame({n: {k: ("" if r.get(k) is None else str(r.get(k))) for k in FIELD_NAMES}
                         for n, r in named.items()})


def show_category(cat):
    {"High concern": st.error, "Needs review": st.warning, "Low concern": st.success}[cat](
        f"Screening category: **{cat}**")
    st.caption(DISCLAIMER)


# ----------------------------------------------------------------- sidebar
st.sidebar.title("🧾 DocuSense")
page = st.sidebar.radio("Section", ["Dashboard", "Document processing", "Invoice investigation",
                                    "Model & system evaluation"])
st.sidebar.divider()
st.sidebar.subheader("Settings")
tol_abs = st.sidebar.number_input("Rounding tolerance (absolute)", 0.0, 10.0, 0.05, 0.01,
                                  help="Subtotal+tax vs total differences up to max(abs, relative*total) pass.")
tol_rel = st.sidebar.number_input("Rounding tolerance (relative)", 0.0, 0.05, 0.005, 0.001, format="%.3f")
dup_threshold = st.sidebar.slider("Near-duplicate similarity threshold", 50, 100, 85,
                                  help="Lower = more candidates (more false positives); higher = fewer "
                                       "candidates (more missed near-duplicates). Exact and conflicting "
                                       "matches are reported regardless of threshold.")
tess_cmd = st.sidebar.text_input("Tesseract path (optional)", os.environ.get("TESSERACT_CMD", ""))
max_mb = st.sidebar.number_input("Max upload size (MB)", 1, 50, 10)
st.sidebar.caption("Academic prototype. Alerts are not findings of fraud; a human makes the final decision.")


# ----------------------------------------------------------------- dashboard
def page_dashboard():
    st.title("Dashboard overview")
    conn = get_conn()
    rows = database.fetch_all(conn)
    c1, c2 = st.columns(2)
    if c1.button("Load SYNTHETIC demo records"):
        added = 0
        for rec in demo_records():
            history = database.fetch_all(conn)
            res = screen_record(rec, None, history, tol_abs, tol_rel, dup_threshold)
            if database.insert_record(conn, to_db_record(rec, rec, rec["file_hash"], rec["file_name"],
                                                         rec["text_excerpt"], res, False, "synthetic_demo")):
                added += 1
        st.success(f"Added {added} demo record(s). They are labelled synthetic_demo.")
        st.rerun()
    with c2.expander("Reset / clean up demo database"):
        if st.button("Remove only synthetic demo records"):
            database.delete_source(conn, "synthetic_demo")
            st.rerun()
        confirm = st.checkbox("I understand this deletes ALL stored records")
        if st.button("Reset entire database", disabled=not confirm):
            database.reset_db(conn)
            st.rerun()
    if not rows:
        st.info("No documents processed yet. Upload one under 'Document processing' or load the demo records.")
        return
    df = pd.DataFrame(rows)
    n_demo = int((df["source"] == "synthetic_demo").sum())
    if n_demo:
        st.warning(f"{n_demo} of {len(df)} records are SYNTHETIC demonstration records.")
    anomaly_flags = sum(bool(json.loads(a or "{}").get("flag")) for a in df["anomaly_json"])
    dup_cands = sum(len(json.loads(d or "[]")) > 0 for d in df["duplicate_json"])
    cols = st.columns(6)
    cols[0].metric("Documents", len(df))
    cols[1].metric("All required fields found", int((df["completeness"] >= 1.0).sum()))
    cols[2].metric("Need review / high concern", int((df["screening_category"] != "Low concern").sum()))
    cols[3].metric("Duplicate candidates", dup_cands)
    cols[4].metric("Validation failures", int((df["validation_status"] == "FAIL").sum()))
    cols[5].metric("Anomaly flags", anomaly_flags if load_model() else "n/a (no model)")
    a, b = st.columns(2)
    cat = df["screening_category"].value_counts().reset_index()
    cat.columns = ["category", "count"]
    a.plotly_chart(px.bar(cat, x="category", y="count", title="Screening categories"), width="stretch")
    val = df["validation_status"].value_counts().reset_index()
    val.columns = ["status", "count"]
    b.plotly_chart(px.pie(val, names="status", values="count", title="Overall validation status"),
                   width="stretch")


# ----------------------------------------------------------------- processing
def page_processing():
    st.title("Document processing")
    if not tesseract_available(tess_cmd or None):
        st.warning("Tesseract OCR was not found. Scanned images need it (digital PDFs with a text layer "
                   "work without it). See README for Windows setup.")
    up = st.file_uploader("Upload an invoice (PDF, JPG, PNG)", type=["pdf", "jpg", "jpeg", "png"])
    if up is not None and st.button("Extract fields"):
        configure_tesseract(tess_cmd or None)
        try:
            with st.spinner("Preprocessing and extracting..."):
                st.session_state["doc"] = process_document(up.name, up.getvalue(), max_mb=max_mb)
            st.session_state.pop("result", None)
        except (DocumentError, OCRUnavailableError) as exc:
            st.session_state.pop("doc", None)
            st.error(f"Processing failed: {exc}")
        except Exception as exc:
            st.session_state.pop("doc", None)
            st.error(f"Unexpected error: {exc}")
    doc = st.session_state.get("doc")
    if not doc:
        return
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Preview")
        for i, p in enumerate(doc["pages"]):
            st.image(p, caption=f"Page {i + 1}", width="stretch")
    with right:
        conf = doc["ocr_confidence"]
        st.caption(f"Text source: {doc['text_source']}" + (f" | mean OCR word confidence: {conf:.0f}/100" if conf else ""))
        st.subheader("Extracted fields (editable)")
        st.caption("Rule-based extraction. 'uncertain' values come from fallback heuristics; 'missing' fields "
                   "are left blank, never guessed. Correct anything wrong before validating.")
        ext = doc["extraction"]["fields"]
        corrected = {}
        for name in FIELD_NAMES:
            f = ext[name]
            init = "" if f["value"] is None else str(f["value"])
            corrected[name] = st.text_input(f"{name.replace('_', ' ').title()}  [{f['status']}]", init,
                                            key=f"in_{doc['file_hash']}_{name}", help=f.get("note") or f.get("source"))
        with st.expander("Original OCR text"):
            st.text(doc["extraction"]["raw_text"] or "(empty)")
        if st.button("Run validation & screening", type="primary"):
            rec, errors = {}, []
            for k, v in corrected.items():
                v = v.strip()
                if k in AMOUNTS:
                    rec[k] = parse_amount(v) if v else None
                    if v and rec[k] is None:
                        errors.append(f"{k}: '{v}' is not a number")
                elif k in DATES and v:
                    d = parse_date(v)
                    rec[k] = d.isoformat() if d else v
                else:
                    rec[k] = v or None
            if errors:
                st.error("; ".join(errors))
            else:
                text = doc["extraction"]["raw_text"]
                rec["text_excerpt"] = text
                rec["file_hash"] = doc["file_hash"]
                history = database.fetch_all(get_conn())
                res = screen_record(rec, doc["extraction"], history, tol_abs, tol_rel, dup_threshold)
                changed = any((str(ext[k]["value"] or "") != corrected[k].strip()) for k in FIELD_NAMES)
                st.session_state["result"] = {"rec": rec, "res": res, "changed": changed, "text": text}
    result = st.session_state.get("result")
    if doc and result:
        res, rec = result["res"], result["rec"]
        st.divider()
        show_category(res["screening"]["category"])
        if result["changed"]:
            st.info("Values were manually corrected; both extracted and corrected values are in the export.")
        t1, t2, t3, t4 = st.tabs(["Indicators", "Validation", "Duplicates", "Anomaly"])
        with t1:
            st.dataframe(pd.DataFrame(res["screening"]["indicators"] or [{"source": "-", "level": "-",
                         "detail": "No indicators raised."}]), width="stretch", hide_index=True)
        with t2:
            vdf = pd.DataFrame(res["validation"])
            vdf["values"] = vdf["values"].apply(lambda v: json.dumps(v, default=str))
            st.dataframe(vdf, width="stretch", hide_index=True)
        with t3:
            if not res["duplicates"]:
                st.write("No duplicate candidates among stored records.")
            for d in res["duplicates"]:
                o = d["other"]
                st.markdown(f"**{d['match_type']}** with record #{o['id']} - similarity {d['score']}")
                st.write(d["reasons"])
                st.dataframe(_cmp({"this document": rec, f"record #{o['id']}": o}))
        with t4:
            an = res["anomaly"]
            st.write(an["message"])
            if an["score"] is not None:
                st.metric("Isolation Forest score (lower = more unusual)", an["score"])
        export = {"extracted": {k: v["value"] for k, v in doc["extraction"]["fields"].items()},
                  "corrected": {k: rec.get(k) for k in FIELD_NAMES}, "user_corrected": result["changed"],
                  "validation": res["validation"], "screening": res["screening"],
                  "anomaly": res["anomaly"], "disclaimer": DISCLAIMER}
        st.download_button("Download result (JSON)", json.dumps(export, indent=2, default=str),
                           file_name=f"{os.path.splitext(doc['file_name'])[0]}_docusense.json")
        if st.button("Save to local database"):
            rid = database.insert_record(get_conn(), to_db_record(rec, {k: rec.get(k) for k in FIELD_NAMES},
                                         doc["file_hash"], doc["file_name"], result["text"], res,
                                         result["changed"]))
            st.success(f"Saved as record #{rid}.") if rid else st.warning("This exact file is already stored; nothing was overwritten.")


# ----------------------------------------------------------------- investigation
def page_investigation():
    st.title("Invoice investigation")
    conn = get_conn()
    rows = database.fetch_all(conn)
    if not rows:
        st.info("No stored invoices yet.")
        return
    df = pd.DataFrame(rows)
    df["duplicate_candidates"] = df["duplicate_json"].apply(lambda s: len(json.loads(s or "[]")))
    df["anomaly"] = df["anomaly_json"].apply(
        lambda s: "flagged" if json.loads(s or "{}").get("flag") else
        ("not flagged" if json.loads(s or "{}").get("scorable") else "not scored"))
    c1, c2, c3, c4 = st.columns(4)
    vs = c1.multiselect("Validation status", sorted(df["validation_status"].dropna().unique()))
    ds = c2.selectbox("Duplicate status", ["any", "has candidates", "none"])
    an = c3.multiselect("Anomaly result", sorted(df["anomaly"].unique()))
    sc = c4.multiselect("Screening category", sorted(df["screening_category"].dropna().unique()))
    if vs: df = df[df["validation_status"].isin(vs)]
    if ds == "has candidates": df = df[df["duplicate_candidates"] > 0]
    if ds == "none": df = df[df["duplicate_candidates"] == 0]
    if an: df = df[df["anomaly"].isin(an)]
    if sc: df = df[df["screening_category"].isin(sc)]
    show = ["id", "source", "vendor", "invoice_number", "invoice_date", "total", "validation_status",
            "duplicate_candidates", "anomaly", "screening_category"]
    st.dataframe(df[show], width="stretch", hide_index=True)
    st.download_button("Export filtered results (CSV)", df[show].to_csv(index=False), "docusense_results.csv")
    if df.empty:
        return
    rid = st.selectbox("Inspect record", df["id"].tolist())
    rec = next(r for r in rows if r["id"] == rid)
    st.subheader(f"Record #{rid}: {rec['vendor']} / {rec['invoice_number']}")
    show_category(rec["screening_category"])
    st.write("**Why it was flagged**")
    st.dataframe(pd.DataFrame(json.loads(rec["indicators_json"] or "[]") or [{"detail": "No indicators."}]),
                 width="stretch", hide_index=True)
    others = [r for r in rows if r["id"] != rid]
    for d in find_duplicates(rec, others, dup_threshold):
        o = d["other"]
        st.markdown(f"**{d['match_type']}** vs record #{o['id']} (similarity {d['score']})")
        st.write(d["reasons"])
        st.dataframe(_cmp({f"#{rid}": rec, f"#{o['id']}": o}))


# ----------------------------------------------------------------- evaluation
def page_evaluation():
    st.title("Model & system evaluation")
    st.info("No single overall accuracy is reported. Each component is described by what can honestly be measured.")
    st.subheader("OCR & field extraction")
    rpt = "reports/extraction_eval.json"
    if os.path.exists(rpt):
        data = json.load(open(rpt))
        st.write(f"Dataset: **{data['dataset']}** - {data['n_documents']} documents ({data['n_failed']} failed)")
        st.caption(data.get("note", ""))
        st.dataframe(pd.DataFrame(data["metrics"]).T, width="stretch")
    else:
        st.write("No evaluation report yet. Run `python scripts/evaluate_model.py` with a ground-truth CSV.")
    st.subheader("Financial validation engine")
    st.write("Rule-based, not a trained classifier. Reliability is shown through unit tests "
             "(`python -m pytest`) and the rule outcomes below.")
    rows = database.fetch_all(get_conn())
    if rows:
        outcomes = validation_outcomes([json.loads(r["validation_json"] or "[]") for r in rows])
        st.dataframe(pd.Series(outcomes, name="count"), width="stretch")
    st.subheader("Duplicate detection")
    st.write("Precision/recall are not reported: no ground-truth duplicate pairs are available. "
             "Similarity weights are transparent heuristics, not validated.")
    st.subheader("Anomaly detection")
    art = load_model()
    if art:
        st.write(f"Isolation Forest loaded: trained on {art['n_train']} records, assumed contamination "
                 f"{art['contamination']}, trained {art['trained_at']}. No labelled fraud data exists, so no "
                 "accuracy/precision/recall is claimed.")
    else:
        st.write(f"No model at `{DEFAULT_MODEL_PATH}`. Training requires >= {MIN_TRAIN_RECORDS} real records "
                 "with total, subtotal and tax. See README.")


{"Dashboard": page_dashboard, "Document processing": page_processing,
 "Invoice investigation": page_investigation, "Model & system evaluation": page_evaluation}[page]()
