(function () {
  // Only customers can use this page. These two helpers come from layout.js.
  if (typeof requireLogin === "function") {
    const user = requireLogin(["customer"]);
    if (!user) return;
  }
  if (typeof renderNavbar === "function") renderNavbar("upload");

  const MAX_MB = 10; // Ask Member 1 for the real limit
  const ALLOWED = ["image/jpeg", "image/png", "image/webp"];
  const WAIT_SECONDS = 15;
  let chosenFile = null;

  const cameraBtn = document.getElementById("cameraBtn");
  const fileBtn = document.getElementById("fileBtn");
  const fileInput = document.getElementById("fileInput");
  const preview = document.getElementById("preview");
  const previewBox = document.getElementById("previewBox");
  const uploadBtn = document.getElementById("uploadBtn");
  const msg = document.getElementById("msg");

  function showError(text) { msg.textContent = text; }

  function resetButton() {
    uploadBtn.disabled = false;
    uploadBtn.textContent = "Check this label";
  }

  // Called for both the camera photo and the chosen file.
  function useFile(file) {
    msg.textContent = "";
    if (!file) return;
    if (ALLOWED.indexOf(file.type) === -1) {
      showError("Please choose a JPG, PNG or WEBP image.");
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      showError("The photo is larger than " + MAX_MB + " MB. Please choose a smaller one.");
      return;
    }
    chosenFile = file;
    preview.src = URL.createObjectURL(file);
    previewBox.classList.remove("hidden");
    uploadBtn.disabled = false;
  }

  cameraBtn.addEventListener("click", function () {
    if (typeof openCamera !== "function") {
      showError("Camera file is missing. Check that /static/js/camera.js loads.");
      return;
    }
    openCamera(useFile, showError);
  });

  fileBtn.addEventListener("click", function () { fileInput.click(); });
  fileInput.addEventListener("change", function (e) { useFile(e.target.files[0]); });

  uploadBtn.addEventListener("click", async function () {
    msg.textContent = "";
    if (!chosenFile) { showError("Please choose or take a photo first."); return; }
    if (typeof apiUpload !== "function") {
      showError("apiUpload is missing in api.js.");
      return;
    }

    uploadBtn.disabled = true;
    uploadBtn.textContent = "Uploading...";

    // Never wait forever: give up after WAIT_SECONDS and say what to check.
    const timeout = new Promise(function (resolve) {
      setTimeout(function () {
        resolve({ ok: false, error: "No answer after " + WAIT_SECONDS + " seconds. Open DevTools > Console and send me the red text." });
      }, WAIT_SECONDS * 1000);
    });

    let res;
    try {
      res = await Promise.race([apiUpload(chosenFile), timeout]);
    } catch (err) {
      res = { ok: false, error: "Upload failed: " + (err && err.message ? err.message : err) };
    }

    if (!res || !res.ok) {
      resetButton();
      showError((res && res.error) || "Upload failed. Please try again.");
      return;
    }

    const scanId = res.data && (res.data.scan_id || res.data.id);
    if (!scanId) {
      resetButton();
      showError("The server did not return a scan id. Check the upload answer in api.js.");
      return;
    }

    const page = (typeof CONFIG !== "undefined" && CONFIG.PAGES && CONFIG.PAGES.progress)
      ? CONFIG.PAGES.progress
      : "/templates/progress.html";
    window.location.href = page + "?id=" + encodeURIComponent(scanId);
  });
})();