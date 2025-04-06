document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("video-form");
  const submitButton = document.getElementById("submit-button");
  const loadingIndicator = document.getElementById("loading-indicator");
  const resultDiv = document.getElementById("result");
  const resultMessage = document.getElementById("result-message");
  const downloadLink = document.getElementById("download-link");
  const generateAgainButton = document.getElementById("generate-again-button");
  const errorMessageDiv = document.getElementById("error-message");
  const errorText = document.getElementById("error-text");
  const errorAgainButton = document.getElementById("error-again-button");

  const gameCards = document.querySelectorAll(".game-card");
  const selectedGameInput = document.getElementById("selected_game");
  const gameError = document.getElementById("game-error");

  const musicVolumeSlider = document.getElementById("music-volume");
  const musicVolumeValue = document.getElementById("music-volume-value");

  // Progress elements
  const progressFetch = document.getElementById("progress-fetch");
  const progressAudio = document.getElementById("progress-audio");
  const progressWords = document.getElementById("progress-words");
  const progressVideo = document.getElementById("progress-video");
  const currentStepText = document.getElementById("current-step-text");
  const progressLog = document.getElementById("progress-log");

  let pollingInterval = null;
  let previousLogs = [];

  // --- UI Interaction ---

  // Update music volume slider value display
  musicVolumeSlider.addEventListener("input", (event) => {
    musicVolumeValue.textContent = `${event.target.value}%`;
  });

  // Game card selection
  gameCards.forEach((card) => {
    card.addEventListener("click", () => {
      gameCards.forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      selectedGameInput.value = card.getAttribute("data-game");
      gameError.classList.add("hidden"); // Hide error on selection
    });
  });

  // Show form, hide others
  function showForm() {
    form.classList.remove("hidden");
    submitButton.classList.remove("hidden");
    loadingIndicator.classList.add("hidden");
    resultDiv.classList.add("hidden");
    errorMessageDiv.classList.add("hidden");
    submitButton.disabled = false;

    // Reset progress elements
    progressFetch.style.width = "0%";
    progressAudio.style.width = "0%";
    progressWords.style.width = "0%";
    progressVideo.style.width = "0%";
    currentStepText.textContent = "Initializing pipeline...";
    progressLog.innerHTML =
      '<div class="log-entry">Starting video generation pipeline...</div>';
    previousLogs = [];
  }

  // Show loading
  function showLoading() {
    form.classList.add("hidden");
    submitButton.classList.add("hidden");
    resultDiv.classList.add("hidden");
    errorMessageDiv.classList.add("hidden");
    loadingIndicator.classList.remove("hidden");
    submitButton.disabled = true; // Disable button while loading
  }

  // Show result
  function showResult(message, filename) {
    form.classList.add("hidden");
    submitButton.classList.add("hidden");
    loadingIndicator.classList.add("hidden");
    errorMessageDiv.classList.add("hidden");
    resultMessage.textContent = message;
    downloadLink.href = `/download/${filename}`; // Set download URL

    // Set video player source
    const videoPlayer = document.getElementById("result-video");
    videoPlayer.src = `/download/${filename}`; // Use the download URL as source
    videoPlayer.load(); // Important: load the new source

    resultDiv.classList.remove("hidden");
    submitButton.disabled = false;
  }

  // Show error
  function showError(message) {
    form.classList.add("hidden");
    submitButton.classList.add("hidden");
    loadingIndicator.classList.add("hidden");
    resultDiv.classList.add("hidden");
    errorText.textContent = message || "An unknown error occurred.";
    errorMessageDiv.classList.remove("hidden");
    submitButton.disabled = false;
  }

  // Update progress UI
  function updateProgressUI(progressData) {
    // Reset all progress bars initially
    progressFetch.style.width = "0%";
    progressAudio.style.width = "0%";
    progressWords.style.width = "0%";
    progressVideo.style.width = "0%";

    // Reset all step labels to gray
    document.getElementById("step-label-fetch").className = "text-gray-400";
    document.getElementById("step-label-audio").className = "text-gray-400";
    document.getElementById("step-label-words").className = "text-gray-400";
    document.getElementById("step-label-video").className = "text-gray-400";

    if (progressData.percentage !== undefined) {
      const percentage = progressData.percentage;

      // Weight values from PIPELINE_STEPS in app.py
      const fetchWeight = 10;
      const audioWeight = 20;
      const wordsWeight = 20;
      const videoWeight = 50;
      const totalWeight = fetchWeight + audioWeight + wordsWeight + videoWeight;

      // Calculate segment widths based on their weight proportions
      const fetchSegmentWidth = (fetchWeight / totalWeight) * 100;
      const audioSegmentWidth = (audioWeight / totalWeight) * 100;
      const wordsSegmentWidth = (wordsWeight / totalWeight) * 100;
      const videoSegmentWidth = (videoWeight / totalWeight) * 100;

      // Fill each segment proportionally based on progress
      if (percentage <= fetchWeight) {
        // Only in fetch stage
        progressFetch.style.width = `${
          (percentage / fetchWeight) * fetchSegmentWidth
        }%`;
      } else if (percentage <= fetchWeight + audioWeight) {
        // In audio stage
        progressFetch.style.width = `${fetchSegmentWidth}%`; // Fetch complete
        const audioProgress = percentage - fetchWeight;
        progressAudio.style.width = `${
          (audioProgress / audioWeight) * audioSegmentWidth
        }%`;
      } else if (percentage <= fetchWeight + audioWeight + wordsWeight) {
        // In words stage
        progressFetch.style.width = `${fetchSegmentWidth}%`; // Fetch complete
        progressAudio.style.width = `${audioSegmentWidth}%`; // Audio complete
        const wordsProgress = percentage - fetchWeight - audioWeight;
        progressWords.style.width = `${
          (wordsProgress / wordsWeight) * wordsSegmentWidth
        }%`;
      } else {
        // In video stage
        progressFetch.style.width = `${fetchSegmentWidth}%`; // Fetch complete
        progressAudio.style.width = `${audioSegmentWidth}%`; // Audio complete
        progressWords.style.width = `${wordsSegmentWidth}%`; // Words complete
        const videoProgress = Math.min(
          percentage - fetchWeight - audioWeight - wordsWeight,
          videoWeight
        );
        progressVideo.style.width = `${
          (videoProgress / videoWeight) * videoSegmentWidth
        }%`;
      }
    }

    // Highlight current step
    if (progressData.current_step) {
      // Highlight the active step
      if (progressData.current_step === "Fetching Story") {
        document.getElementById("step-label-fetch").className =
          "text-blue-300 font-semibold";
      } else if (progressData.current_step === "Generating Audio") {
        document.getElementById("step-label-audio").className =
          "text-indigo-300 font-semibold";
      } else if (progressData.current_step === "Processing Words") {
        document.getElementById("step-label-words").className =
          "text-purple-300 font-semibold";
      } else if (progressData.current_step === "Rendering Video") {
        document.getElementById("step-label-video").className =
          "text-purple-300 font-semibold";
      }

      // Add percentage and detailed information to the current step text
      if (
        progressData.current_step === "Rendering Video" &&
        progressData.percentage !== undefined
      ) {
        const renderingPercentage = Math.min(
          Math.round((progressData.percentage - 50) * 2),
          100
        );

        // Extract detailed information from the latest logs
        let detailedStatus = "";
        if (progressData.logs && progressData.logs.length > 0) {
          const latestLog = progressData.logs[progressData.logs.length - 1];

          // Check for specific rendering steps in the log
          if (latestLog.includes("Creating caption:")) {
            const captionText = latestLog.split("'")[1] || "caption";
            detailedStatus = `Captioning: "${captionText}"`;
          } else if (latestLog.includes("Writing final video")) {
            detailedStatus = "Writing final video to file";
          } else if (latestLog.includes("Compositing")) {
            detailedStatus = "Compositing video layers";
          } else if (latestLog.includes("title card")) {
            detailedStatus = "Preparing title card";
          } else if (latestLog.includes("Narration audio loaded")) {
            detailedStatus = "Processing audio track";
          } else {
            detailedStatus = "Building video";
          }
        }

        currentStepText.textContent = `${progressData.current_step} (${renderingPercentage}%) - ${detailedStatus}`;
      } else if (progressData.current_step === "Processing Words") {
        // Add details for Processing Words step
        if (progressData.logs && progressData.logs.length > 0) {
          const latestLog = progressData.logs[progressData.logs.length - 1];
          if (latestLog.includes("timestamps")) {
            currentStepText.textContent = `${progressData.current_step} - Analyzing speech timing`;
          } else {
            currentStepText.textContent = progressData.current_step;
          }
        } else {
          currentStepText.textContent = progressData.current_step;
        }
      } else if (progressData.current_step === "Generating Audio") {
        // Add details for Generating Audio step
        currentStepText.textContent = `${progressData.current_step} - Creating narration track`;
      } else if (progressData.current_step === "Fetching Story") {
        // Add details for Fetching Story step
        if (progressData.logs && progressData.logs.length > 0) {
          const latestLog = progressData.logs[progressData.logs.length - 1];
          if (latestLog.includes("Successfully fetched")) {
            currentStepText.textContent = `${progressData.current_step} - Story retrieved successfully`;
          } else {
            currentStepText.textContent = `${progressData.current_step} - Searching for content`;
          }
        } else {
          currentStepText.textContent = progressData.current_step;
        }
      } else {
        currentStepText.textContent = progressData.current_step;
      }
    }

    // Update log entries (only add new ones)
    if (progressData.logs && progressData.logs.length > 0) {
      // Filter out logs we've already seen
      const newLogs = progressData.logs.filter(
        (log) => !previousLogs.includes(log)
      );

      // Add new logs to the UI
      newLogs.forEach((log) => {
        const logEntry = document.createElement("div");
        logEntry.className = "log-entry py-1";
        logEntry.textContent = log;
        progressLog.appendChild(logEntry);
      });

      // Keep scrolled to bottom
      progressLog.scrollTop = progressLog.scrollHeight;

      // Update our seen logs cache
      previousLogs = [...previousLogs, ...newLogs];

      // Trim the previousLogs array if it gets too large
      if (previousLogs.length > 100) {
        previousLogs = previousLogs.slice(-100);
      }
    }
  }

  // Reset UI (Generate Again buttons)
  generateAgainButton.addEventListener("click", showForm);
  errorAgainButton.addEventListener("click", showForm);

  // --- Form Submission & API Interaction ---

  form.addEventListener("submit", async (event) => {
    event.preventDefault(); // Prevent default form submission

    // Validate game selection
    if (!selectedGameInput.value) {
      gameError.classList.remove("hidden");
      return;
    }
    gameError.classList.add("hidden");

    showLoading();
    stopPolling(); // Clear any previous polling

    const formData = new FormData(form);
    // Convert music volume % to float (0.0 to 1.0) - BE expects 0-1 range
    const musicVolumePercent = formData.get("music_volume");
    formData.set("music_volume", (musicVolumePercent / 100).toFixed(2));

    console.log("Submitting form data:", Object.fromEntries(formData)); // Debug log

    try {
      const response = await fetch("/generate", {
        method: "POST",
        body: formData,
      });

      if (response.ok && response.status === 202) {
        // Start polling status endpoint
        console.log("Generation started, polling status...");
        startPolling();
      } else {
        const errorData = await response.json();
        showError(
          `Failed to start generation: ${
            errorData.message || response.statusText
          }`
        );
      }
    } catch (error) {
      console.error("Error submitting form:", error);
      showError("Network error or server unavailable.");
    }
  });

  // --- Polling Logic ---

  function startPolling() {
    pollingInterval = setInterval(async () => {
      try {
        const response = await fetch("/status");
        if (!response.ok) {
          console.error("Status check failed:", response.statusText);
          // Optional: show temporary error or just continue polling?
          return;
        }

        const data = await response.json();
        console.log("Polling status:", data); // Debug log

        // Update progress UI with new data
        if (data.progress) {
          updateProgressUI(data.progress);
        }

        if (!data.in_progress) {
          stopPolling();
          if (data.result_file) {
            showResult("Video generated successfully!", data.result_file);
          } else if (data.error) {
            showError(`Generation failed: ${data.error}`);
          } else {
            showError(
              "Generation finished but no result or error was reported."
            );
          }
        }
      } catch (error) {
        console.error("Error during status polling:", error);
        // Maybe stop polling after too many errors?
      }
    }, 1000); // Poll every 1 second for smoother progress updates
  }

  function stopPolling() {
    if (pollingInterval) {
      clearInterval(pollingInterval);
      pollingInterval = null;
      console.log("Polling stopped.");
    }
  }

  // --- Initialization ---
  // Set default game selection (first card)
  if (gameCards.length > 0) {
    const defaultCard = gameCards[0];
    defaultCard.classList.add("selected");
    selectedGameInput.value = defaultCard.getAttribute("data-game");
  }
});
