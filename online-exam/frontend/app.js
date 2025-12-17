// Correct Backend URL
const backendURL = "http://localhost:8081";

// ---------------- SIGNUP ----------------
const signupForm = document.getElementById("signupForm");
if (signupForm) {
    signupForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const fullName = document.getElementById("fullName").value;
        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        const msg = document.getElementById("message");
        msg.className = "msg";
        msg.innerHTML = "";

        try {
            const res = await fetch(`${backendURL}/api/signup`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ fullName, email, password })
            });

            const text = await res.text();

            if (text.toLowerCase().includes("success")) {
                msg.classList.add("success");
                msg.innerHTML = "✅ Signup successful! Redirecting...";
                setTimeout(() => window.location.href = "signin.html", 1500);
            } else {
                msg.classList.add("error");
                msg.innerHTML = "❌ " + text;
            }

        } catch (err) {
            msg.classList.add("error");
            msg.innerHTML = "❌ Server unreachable. Try again.";
        }
    });
}

// ---------------- SIGNIN ----------------
const signinForm = document.getElementById("signinForm");
if (signinForm) {
    signinForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        const email = document.getElementById("email").value;
        const password = document.getElementById("password").value;

        const msg = document.getElementById("message");
        msg.className = "msg";
        msg.innerHTML = "";

        try {
            const res = await fetch(`${backendURL}/api/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password })
            });

            const text = await res.text();

            if (text.toLowerCase().includes("success")) {
                msg.classList.add("success");
                msg.innerHTML = "🎉 Login successful! Redirecting...";
                setTimeout(() => window.location.href = "welcome.html", 1500);
            } else {
                msg.classList.add("error");
                msg.innerHTML = "❌ Invalid credentials. Try again.";
            }

        } catch (err) {
            msg.classList.add("error");
            msg.innerHTML = "❌ Server unreachable. Try again.";
        }
    });
}

