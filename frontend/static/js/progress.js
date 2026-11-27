(function () {
  const user = requireLogin(["customer"]);
  if (!user) return;
  renderNavbar("upload");

  const id = new URLSearchParams(window.location.search).get("id");
  const statusText = document.getElementById("statusText");
  const msg = document.getElementById("msg");
  const failActions = document.getElementById("failActions");
  const ORDER = ["queued", "processing", "done"];
  const MAX_TRIES = 60; // 60 checks x 2 seconds = 2 minutes
  let tries = 0;

  function fail(text) {
    statusText.textContent = "";
    msg.textContent = text;
    failActions.classList.remove("hidden");
  }

  function markStep(status) {
    const current = ORDER.indexOf(status);
    ORDER.forEach(function (name, index) {
      const li = document.getElementById("step-" + name);
      li.className = index < current ? "done" : (index === current ? "active" : "");
    });
  }

  async function check() {
    tries++;
    const res = await apiGet("scan", id);
    if (!res.ok) return fail(res.error);

    const status = res.data.status;
    markStep(status);

    if (status === "done" || status === "low_quality") {
      window.location.replace(CONFIG.PAGES.result + "?id=" + encodeURIComponent(id));
      return;
    }
    if (status === "failed") return fail("We could not read this photo. Please try another one.");
    if (tries >= MAX_TRIES) return fail("This is taking too long. Please try again in a few minutes.");
    setTimeout(check, 2000);
  }

  if (!id) return fail("No scan selected. Please upload a photo first.");
  check();
})();