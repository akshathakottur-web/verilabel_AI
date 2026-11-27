let mode = "login";        // "login" or "signup"
let loginRole = "customer"; // "customer", "inspector" or "admin"

const title = document.getElementById("title");
const roleTabs = document.getElementById("roleTabs");
const idLabel = document.getElementById("idLabel");
const loginId = document.getElementById("loginId");
const nameHint = document.getElementById("nameHint");
const confirmField = document.getElementById("confirmField");
const submitBtn = document.getElementById("submitBtn");
const switchBox = document.getElementById("switchBox");
const switchText = document.getElementById("switchText");
const switchBtn = document.getElementById("switchBtn");
const staffNote = document.getElementById("staffNote");
const msg = document.getElementById("msg");

// Already signed in? Skip the login page.
const existing = getSession();
if (existing) goHomeForRole(existing.role);

function show(text, ok) {
  msg.className = ok ? "msg success" : "msg";
  msg.textContent = text;
}

// Customers have no ID. Their sign in key is built from their name.
function makeKey(name) {
  return name.trim().toLowerCase().replace(/\s+/g, "_");
}

function render() {
  const signup = mode === "signup";
  const customer = loginRole === "customer";

  title.textContent = signup ? "SIGN UP" : "LOGIN";
  submitBtn.textContent = signup ? "SIGN UP" : "LOGIN";
  roleTabs.classList.toggle("hidden", signup);
  confirmField.classList.toggle("hidden", !signup);
  nameHint.classList.toggle("hidden", !signup);
  idLabel.textContent = customer ? "Name" : "ID";

  // Sign up exists only for customers
  switchBox.classList.toggle("hidden", !customer);
  staffNote.classList.toggle("hidden", customer || signup);
  switchText.textContent = signup ? "Already have an account?" : "New here?";
  switchBtn.textContent = signup ? "Sign in" : "Sign up";

  document.querySelectorAll(".role-tab").forEach(function (tab) {
    const active = tab.dataset.role === loginRole;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", active ? "true" : "false");
  });
  show("", false);
}

document.querySelectorAll(".role-tab").forEach(function (tab) {
  tab.addEventListener("click", function () {
    loginRole = tab.dataset.role;
    render();
  });
});

switchBtn.addEventListener("click", function () {
  mode = mode === "login" ? "signup" : "login";
  loginRole = "customer";
  render();
});

submitBtn.addEventListener("click", async function () {
  const typed = loginId.value.trim();
  const password = document.getElementById("password").value;
  const confirm = document.getElementById("confirm").value;
  const signup = mode === "signup";
  const customer = loginRole === "customer";

  // Checks before calling the server
  if (typed === "") return show(customer ? "Please enter your name." : "Please enter your ID.", false);
  if (password.length < 6) return show("Password must be at least 6 characters.", false);
  if (signup && password !== confirm) return show("The two passwords do not match.", false);

  submitBtn.disabled = true;
  show("", false);

  let result;
  if (signup) {
    result = await apiPost("signup", {
      name: typed,
      user_id: makeKey(typed),
      password: password,
      role: "customer"
    });
  } else {
    result = await apiPost("signin", {
      user_id: customer ? makeKey(typed) : typed,
      password: password
    });
  }
  submitBtn.disabled = false;

  if (!result.ok) {
    const taken = /taken|exist|already/i.test(result.error || "");
    return show(signup && taken ? "This name is already registered. Add your surname or a number." : result.error, false);
  }

  if (signup) {
    mode = "login";
    render();
    show("Account created. Please sign in.", true);
  } else {
    // The contract says signin returns: token + user (name, user_id, role)
    const user = result.data.user || {};
    if (user.role !== loginRole) {
      return show("This is not a " + loginRole + " account. Choose the right tab above.", false);
    }
    saveSession({ token: result.data.token, name: user.name, user_id: user.user_id, role: user.role });
    goHomeForRole(user.role);
  }
});

// Pressing Enter submits the form
document.addEventListener("keydown", function (e) {
  if (e.key === "Enter") submitBtn.click();
});

render();