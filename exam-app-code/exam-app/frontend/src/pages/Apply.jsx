import { useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../components/Layout";
import { api } from "../lib/api";

const BLANK = {
  full_name: "", email: "", phone: "", dob: "",
  address: "", qualification: "", id_proof_type: "Aadhaar", id_proof_number: "",
};

// Mirrors the server's rules so people get told before they submit, not after.
// The server re-checks everything — this is courtesy, not security.
const ID_RULES = {
  "Aadhaar": [/^[2-9]\d{11}$/, "12 digits, not starting with 0 or 1", "234567890123"],
  "PAN": [/^[A-Z]{5}\d{4}[A-Z]$/, "Five letters, four digits, one letter", "ABCDE1234F"],
  "Passport": [/^[A-PR-WY][1-9]\d\s?\d{4}[1-9]$/, "One letter followed by seven digits", "A1234567"],
  "Driving Licence": [/^[A-Z]{2}\d{2}\s?\d{11}$/, "State code, RTO code, then 11 digits", "MP09 20230012345"],
  "Voter ID": [/^[A-Z]{3}\d{7}$/, "Three letters followed by seven digits", "ABC1234567"],
};

// Defined at module scope on purpose. Nesting this inside Apply() would give it
// a new identity every render, remounting the input and stealing focus mid-typing.
function Field({ name, label, hint, err, touched, children }) {
  return (
    <div className="field">
      <label htmlFor={name}>{label} <span style={{ color: "var(--fail)" }}>*</span></label>
      {children}
      {err && touched
        ? <p className="field-err">{err}</p>
        : hint && <p className="field-hint">{hint}</p>}
    </div>
  );
}

function ageFrom(iso) {
  const b = new Date(iso), t = new Date();
  let a = t.getFullYear() - b.getFullYear();
  const m = t.getMonth() - b.getMonth();
  if (m < 0 || (m === 0 && t.getDate() < b.getDate())) a--;
  return a;
}

function validate(f) {
  const e = {};

  const name = f.full_name.trim().replace(/\s+/g, " ");
  if (!name) e.full_name = "Enter your full name.";
  else if (!/^[A-Za-z][A-Za-z .'-]*$/.test(name)) e.full_name = "Letters, spaces, and . ' - only.";
  else if (!/[A-Za-z]{2}/.test(name)) e.full_name = "Enter your full name.";

  const email = f.email.trim();
  if (!email) e.email = "Enter your email address.";
  else if (!/^[^\s@]+@[^\s@]+\.[A-Za-z]{2,}$/.test(email)) e.email = "That doesn't look like a valid email address.";

  const phone = f.phone.replace(/[\s\-()]/g, "").replace(/^(\+91|0091|0)/, "");
  if (!f.phone.trim()) e.phone = "Enter your mobile number.";
  else if (!/^[6-9]\d{9}$/.test(phone)) e.phone = "Enter a 10-digit Indian mobile number starting with 6, 7, 8 or 9.";

  if (!f.dob) e.dob = "Enter your date of birth.";
  else {
    const a = ageFrom(f.dob);
    if (new Date(f.dob) > new Date()) e.dob = "Date of birth cannot be in the future.";
    else if (a < 15) e.dob = "Candidates must be at least 15 years old.";
    else if (a > 100) e.dob = "Check the date — that age looks wrong.";
  }

  if (!f.address.trim()) e.address = "Enter your address.";
  else if (f.address.trim().length < 5) e.address = "Enter a fuller address.";

  if (!f.qualification.trim()) e.qualification = "Enter your highest qualification.";
  else if (f.qualification.trim().length < 2) e.qualification = "Enter your highest qualification.";

  const rule = ID_RULES[f.id_proof_type];
  const num = f.id_proof_number.trim().toUpperCase().replace(/\s/g, "");
  if (!num) e.id_proof_number = "Enter your ID proof number.";
  else if (rule && !rule[0].test(num)) e.id_proof_number = `${rule[1]} — e.g. ${rule[2]}`;

  return e;
}

export default function Apply() {
  const [form, setForm] = useState(BLANK);
  const [errs, setErrs] = useState({});
  const [touched, setTouched] = useState({});
  const [err, setErr] = useState("");
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => {
    const next = { ...form, [k]: e.target.value };
    setForm(next);
    if (touched[k]) setErrs(validate(next));
  };
  const blur = (k) => () => {
    setTouched({ ...touched, [k]: true });
    setErrs(validate(form));
  };

  const submit = async (e) => {
    e.preventDefault();
    setErr("");
    const found = validate(form);
    setErrs(found);
    setTouched(Object.fromEntries(Object.keys(BLANK).map((k) => [k, true])));
    if (Object.keys(found).length) {
      setErr("Check the highlighted fields.");
      return;
    }
    setBusy(true);
    try {
      await api.post("/auth/apply", form);
      setDone(true);
    } catch (e2) {
      setErr(e2.message);
    } finally {
      setBusy(false);
    }
  };

  if (done) {
    return (
      <Layout narrow>
        <div className="card" style={{ marginTop: 40 }}>
          <p className="eyebrow">Received</p>
          <h2 style={{ margin: "10px 0 12px" }}>Your application is with the administrator</h2>
          <p className="sub">
            You'll be contacted at <b>{form.email.trim().toLowerCase()}</b> once it's reviewed. If approved,
            you'll get a password and a verification code — you need both to sit the exam.
          </p>
          <div className="btn-row" style={{ marginTop: 22 }}>
            <Link to="/" className="btn btn-ghost">Back to home</Link>
            <Link to="/login" className="btn btn-primary">Sign in</Link>
          </div>
        </div>
      </Layout>
    );
  }

  const cls = (k) => (errs[k] && touched[k] ? "bad" : "");
  const rule = ID_RULES[form.id_proof_type];

  return (
    <Layout narrow>
      <p className="eyebrow">Step 1 of 4</p>
      <h1 style={{ margin: "10px 0 8px" }}>Application form</h1>
      <p className="sub" style={{ marginBottom: 26 }}>
        An administrator reviews every application by hand. Every field is required, and
        the details must match your ID.
      </p>

      <form className="card" onSubmit={submit} noValidate>
        {err && <div className="alert alert-error">{err}</div>}

        <Field name="full_name" label="Full name" hint="As printed on your ID" err={errs.full_name} touched={touched.full_name}>
          <input id="full_name" className={cls("full_name")} value={form.full_name}
                 onChange={set("full_name")} onBlur={blur("full_name")} />
        </Field>

        <div className="grid2">
          <Field name="email" label="Email" hint="Credentials are sent here" err={errs.email} touched={touched.email}>
            <input id="email" type="email" className={cls("email")} value={form.email}
                   onChange={set("email")} onBlur={blur("email")} placeholder="you@example.com" />
          </Field>
          <Field name="phone" label="Mobile number" hint="10 digits, Indian number" err={errs.phone} touched={touched.phone}>
            <input id="phone" inputMode="tel" className={cls("phone")} value={form.phone}
                   onChange={set("phone")} onBlur={blur("phone")} placeholder="9876543210" />
          </Field>
        </div>

        <div className="grid2">
          <Field name="dob" label="Date of birth" err={errs.dob} touched={touched.dob}>
            <input id="dob" type="date" className={cls("dob")} value={form.dob}
                   onChange={set("dob")} onBlur={blur("dob")}
                   max={new Date().toISOString().split("T")[0]} />
          </Field>
          <Field name="qualification" label="Highest qualification" err={errs.qualification} touched={touched.qualification}>
            <input id="qualification" className={cls("qualification")} value={form.qualification}
                   onChange={set("qualification")} onBlur={blur("qualification")}
                   placeholder="B.Tech, B.Sc, 12th…" />
          </Field>
        </div>

        <div className="grid2">
          <Field name="id_proof_type" label="ID proof type" err={errs.id_proof_type} touched={touched.id_proof_type}>
            <select id="id_proof_type" value={form.id_proof_type}
                    onChange={(e) => {
                      const next = { ...form, id_proof_type: e.target.value };
                      setForm(next);
                      if (touched.id_proof_number) setErrs(validate(next));
                    }}>
              {Object.keys(ID_RULES).map((t) => <option key={t}>{t}</option>)}
            </select>
          </Field>
          <Field name="id_proof_number" label="ID proof number" hint={rule ? `e.g. ${rule[2]}` : ""} err={errs.id_proof_number} touched={touched.id_proof_number}>
            <input id="id_proof_number" className={cls("id_proof_number")} value={form.id_proof_number}
                   onChange={set("id_proof_number")} onBlur={blur("id_proof_number")}
                   placeholder={rule ? rule[2] : ""} />
          </Field>
        </div>

        <Field name="address" label="Address" err={errs.address} touched={touched.address}>
          <textarea id="address" className={cls("address")} value={form.address}
                    onChange={set("address")} onBlur={blur("address")} />
        </Field>

        <button className="btn btn-primary btn-wide" disabled={busy}>
          {busy ? "Sending…" : "Send application"}
        </button>
      </form>
    </Layout>
  );
}
