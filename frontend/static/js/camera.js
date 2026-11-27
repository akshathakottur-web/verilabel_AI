// Opens a live camera window. Calls onPhoto(file) after the user clicks Capture.
function openCamera(onPhoto, onError) {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    onError("Camera is not available here. Use Upload photo instead. (Cameras need https or localhost.)");
    return;
  }

  const overlay = document.createElement("div");
  overlay.className = "cam-overlay";
  overlay.innerHTML =
    '<div class="cam-box" role="dialog" aria-label="Camera">' +
      '<video class="cam-video" autoplay playsinline muted></video>' +
      '<div class="cam-actions">' +
        '<button type="button" class="up-btn" id="camCapture">Capture</button>' +
        '<button type="button" class="up-btn up-btn-light" id="camCancel">Cancel</button>' +
      "</div>" +
    "</div>";
  document.body.appendChild(overlay);

  const video = overlay.querySelector("video");
  let stream = null;

  function close() {
    if (stream) stream.getTracks().forEach(function (t) { t.stop(); });
    overlay.remove();
  }

  navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false })
    .then(function (s) { stream = s; video.srcObject = s; })
    .catch(function (err) {
      close();
      if (err && err.name === "NotAllowedError") onError("Camera permission was blocked. Allow the camera in your browser, or use Upload photo.");
      else if (err && err.name === "NotFoundError") onError("No camera was found on this device. Use Upload photo instead.");
      else onError("Could not start the camera. Use Upload photo instead.");
    });

  overlay.querySelector("#camCancel").addEventListener("click", close);

  overlay.querySelector("#camCapture").addEventListener("click", function () {
    if (!video.videoWidth) return; // camera not ready yet
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    canvas.toBlob(function (blob) {
      close();
      if (!blob) { onError("Could not take the photo. Please try again."); return; }
      onPhoto(new File([blob], "camera-photo.jpg", { type: "image/jpeg" }));
    }, "image/jpeg", 0.92);
  });
}