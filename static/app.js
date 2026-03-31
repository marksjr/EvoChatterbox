const form = document.getElementById("tts-form");
const statusLabel = document.getElementById("status");
const player = document.getElementById("player");
const downloadLink = document.getElementById("download");
const submitButton = document.getElementById("submit");
const textField = document.getElementById("text");
const charCount = document.getElementById("char-count");
const convertedCount = document.getElementById("converted-count");
const elapsedLabel = document.getElementById("elapsed");
const backendUsed = document.getElementById("backend-used");
const deviceUsed = document.getElementById("device-used");
const languageSelect = document.getElementById("language");
const languageHelp = document.getElementById("language-help");
const emotionSelect = document.getElementById("emotion");
const emotionHelp = document.getElementById("emotion-help");
const emotionChips = document.getElementById("emotion-chips");
const resetEmotionButton = document.getElementById("reset-emotion");
const exaggerationInput = document.getElementById("exaggeration");
const cfgInput = document.getElementById("cfg_weight");
const temperatureInput = document.getElementById("temperature");
const qualityMode = document.getElementById("quality-mode");
const qualityHelp = document.getElementById("quality-help");
const audioPromptHelp = document.getElementById("audio-prompt-help");

const emotionPresets = [
  { id: "neutral", label: "Neutral", help: "Balanced for general use.", exaggeration: 0.5, cfg: 0.5, temperature: 0.8 },
  { id: "calm", label: "Calm", help: "More contained and soft.", exaggeration: 0.2, cfg: 0.55, temperature: 0.55 },
  { id: "soft", label: "Soft", help: "Light, smooth and subtle.", exaggeration: 0.25, cfg: 0.5, temperature: 0.6 },
  { id: "warm", label: "Warm", help: "Friendly and approachable tone.", exaggeration: 0.35, cfg: 0.55, temperature: 0.75 },
  { id: "happy", label: "Happy", help: "More brightness and energy.", exaggeration: 0.7, cfg: 0.45, temperature: 1.0 },
  { id: "excited", label: "Excited", help: "More dynamic and vibrant.", exaggeration: 0.85, cfg: 0.4, temperature: 1.15 },
  { id: "energetic", label: "Energetic", help: "High impulse for calls and announcements.", exaggeration: 0.95, cfg: 0.35, temperature: 1.2 },
  { id: "dramatic", label: "Dramatic", help: "More contrast and intensity.", exaggeration: 1.0, cfg: 0.65, temperature: 0.95 },
  { id: "serious", label: "Serious", help: "Controlled and firm.", exaggeration: 0.4, cfg: 0.65, temperature: 0.65 },
  { id: "authoritative", label: "Authoritative", help: "More command and presence.", exaggeration: 0.55, cfg: 0.7, temperature: 0.6 },
  { id: "narrator", label: "Narrator", help: "More stable for reading.", exaggeration: 0.35, cfg: 0.7, temperature: 0.55 },
  { id: "cinematic", label: "Cinematic", help: "Theatrical style for trailers and spots.", exaggeration: 0.95, cfg: 0.6, temperature: 0.9 },
  { id: "sad", label: "Sad", help: "More contained and dragged.", exaggeration: 0.3, cfg: 0.6, temperature: 0.45 },
  { id: "melancholic", label: "Melancholic", help: "More introspective.", exaggeration: 0.35, cfg: 0.65, temperature: 0.5 },
  { id: "fearful", label: "Tense", help: "Slight instability and tension.", exaggeration: 0.75, cfg: 0.5, temperature: 1.05 },
  { id: "angry", label: "Angry", help: "More emphasis and attack.", exaggeration: 0.9, cfg: 0.75, temperature: 0.85 },
  { id: "whispery", label: "Whisper", help: "Try combining with a reference audio.", exaggeration: 0.15, cfg: 0.45, temperature: 0.5 },
  { id: "romantic", label: "Romantic", help: "Softer and warmer.", exaggeration: 0.35, cfg: 0.5, temperature: 0.72 },
  { id: "comic", label: "Comic", help: "More elasticity in delivery.", exaggeration: 0.9, cfg: 0.4, temperature: 1.1 },
  { id: "commercial", label: "Commercial", help: "Advertising voiceover tone.", exaggeration: 0.65, cfg: 0.55, temperature: 0.9 },
  { id: "podcast", label: "Podcast", help: "Natural and comfortable for long speech.", exaggeration: 0.3, cfg: 0.6, temperature: 0.7 },
  { id: "urgent", label: "Urgent", help: "More pressure and pace.", exaggeration: 0.8, cfg: 0.7, temperature: 1.0 },
  { id: "instructional", label: "Instructional", help: "Clear and didactic.", exaggeration: 0.25, cfg: 0.75, temperature: 0.55 }
];

const qualityPresets = {
  ultra: { exaggeration: 0.3, cfg: 0.7, temperature: 0.55 },
  max: { exaggeration: 0.4, cfg: 0.6, temperature: 0.65 },
  fast: { exaggeration: 0.5, cfg: 0.5, temperature: 0.8 }
};

const qualityHelpByMode = {
  ultra: "High stability splits text into smaller chunks with more natural pauses. Best for non-English languages and longer texts.",
  max: "Balanced stability splits text into smaller chunks for better stability and naturalness.",
  fast: "Direct processing generates the entire text at once. May lose stability on long texts."
};

let timerId = null;
let startedAt = 0;
let currentAudioUrl = null;
let manualSliderOverride = false;
let applyingPreset = false;

function formatElapsed(ms) {
  const totalSeconds = Math.floor(ms / 1000);
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function setRangeValue(inputId, outputId) {
  const input = document.getElementById(inputId);
  const output = document.getElementById(outputId);
  const sync = () => {
    output.textContent = Number(input.value).toFixed(2);
  };
  input.addEventListener("input", () => {
    if (!applyingPreset) {
      manualSliderOverride = true;
    }
    sync();
  });
  sync();
}

function syncDisplayedSliderValues() {
  document.getElementById("exaggeration-value").textContent = Number(exaggerationInput.value).toFixed(2);
  document.getElementById("cfg-value").textContent = Number(cfgInput.value).toFixed(2);
  document.getElementById("temperature-value").textContent = Number(temperatureInput.value).toFixed(2);
}

function applyControlPreset(preset, force = false) {
  if (!preset || (manualSliderOverride && !force)) {
    syncDisplayedSliderValues();
    return false;
  }

  applyingPreset = true;
  exaggerationInput.value = preset.exaggeration;
  cfgInput.value = preset.cfg;
  temperatureInput.value = preset.temperature;
  syncDisplayedSliderValues();
  applyingPreset = false;
  if (force) {
    manualSliderOverride = false;
  }
  return true;
}

function applyQualityPreset(mode, force = false) {
  const preset = qualityPresets[mode];
  return applyControlPreset(preset, force);
}

function renderEmotionChips() {
  emotionChips.innerHTML = "";
  for (const preset of emotionPresets) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "emotion-chip";
    button.dataset.preset = preset.id;
    button.textContent = preset.label;
    button.addEventListener("click", () => {
      emotionSelect.value = preset.id;
      applyEmotionPreset(preset.id);
    });
    emotionChips.appendChild(button);
  }
}

function updateActiveEmotionChip() {
  const chips = emotionChips.querySelectorAll(".emotion-chip");
  for (const chip of chips) {
    chip.classList.toggle("is-active", chip.dataset.preset === emotionSelect.value);
  }
}

function loadEmotionPresets() {
  for (const preset of emotionPresets) {
    const option = document.createElement("option");
    option.value = preset.id;
    option.textContent = preset.label;
    emotionSelect.appendChild(option);
  }
  renderEmotionChips();
  emotionSelect.value = "neutral";
  updateEmotionHelp();
  updateActiveEmotionChip();
}

function applyEmotionPreset(presetId, force = false) {
  const preset = emotionPresets.find((item) => item.id === presetId);
  if (!preset) {
    return;
  }
  applyControlPreset(preset, force);
  updateEmotionHelp();
  updateActiveEmotionChip();
}

function resetEmotionPreset() {
  emotionSelect.value = "neutral";
  manualSliderOverride = false;
  applyEmotionPreset("neutral", true);
}

function updateEmotionHelp() {
  const preset = emotionPresets.find((item) => item.id === emotionSelect.value);
  if (!preset) {
    emotionHelp.textContent = "Intonation preset based on native model controls.";
    return;
  }

  const suffix = manualSliderOverride ? " Manual controls preserved." : "";
  emotionHelp.textContent = `${preset.help} Exaggeration ${preset.exaggeration.toFixed(2)}, CFG ${preset.cfg.toFixed(2)}, Temperature ${preset.temperature.toFixed(2)}.${suffix}`;
}

function updateQualityHelp() {
  const baseHelp = qualityHelpByMode[qualityMode.value] || qualityHelpByMode.max;
  qualityHelp.textContent = manualSliderOverride ? `${baseHelp} Manual controls preserved.` : baseHelp;
}

function updateCharCount() {
  const count = textField.value.length;
  charCount.textContent = `${count} characters`;
}

function startTimer() {
  startedAt = Date.now();
  elapsedLabel.textContent = "00:00";
  timerId = window.setInterval(() => {
    elapsedLabel.textContent = formatElapsed(Date.now() - startedAt);
  }, 250);
}

function stopTimer() {
  if (timerId) {
    window.clearInterval(timerId);
    timerId = null;
  }
}

function renderQualityModes(modes) {
  if (!Array.isArray(modes) || modes.length === 0) {
    return;
  }

  const currentValue = qualityMode.value;
  qualityMode.innerHTML = "";
  for (const mode of modes) {
    const option = document.createElement("option");
    option.value = mode.id;
    option.textContent = mode.label;
    if (mode.id === currentValue) {
      option.selected = true;
    }
    qualityMode.appendChild(option);
  }

  if (![...qualityMode.options].some((option) => option.selected)) {
    qualityMode.value = modes.find((mode) => mode.id === "max")?.id || modes[0].id;
  }
}

async function loadConfig() {
  try {
    const response = await fetch("/config");
    if (!response.ok) {
      throw new Error("Failed to load configuration.");
    }

    const config = await response.json();
    if (!Array.isArray(config.languages) || config.languages.length === 0) {
      throw new Error("No languages returned by the server.");
    }

    languageSelect.innerHTML = "";
    for (const language of config.languages) {
      const option = document.createElement("option");
      option.value = language.id;
      option.textContent = `${language.label} (${language.id})`;
      option.dataset.backend = language.backend;
      option.dataset.modelLanguage = language.model_language_id || language.id;
      option.dataset.help = language.help || "";
      if (language.id === config.default_language) {
        option.selected = true;
      }
      languageSelect.appendChild(option);
    }

    renderQualityModes(config.quality_modes);
    if (typeof config.audio_prompt_max_mb === "number") {
      audioPromptHelp.textContent = `Optional voice reference. Up to ${config.audio_prompt_max_mb} MB.`;
    }

    deviceUsed.textContent = typeof config.device === "string" ? config.device.toUpperCase() : "UNKNOWN";
    updateLanguageHelp();
    updateQualityHelp();
  } catch (error) {
    languageHelp.textContent = error.message || "Could not load languages.";
    deviceUsed.textContent = "UNKNOWN";
  }
}

function updateLanguageHelp() {
  const selectedOption = languageSelect.selectedOptions[0];
  if (!selectedOption) {
    return;
  }

  if (selectedOption.dataset.help) {
    languageHelp.textContent = selectedOption.dataset.help;
    return;
  }

  const backend = selectedOption.dataset.backend;
  const modelLanguage = selectedOption.dataset.modelLanguage || selectedOption.value;
  if (backend === "standard") {
    languageHelp.textContent = "English uses the standard model, usually lighter and faster.";
  } else if (modelLanguage !== selectedOption.value) {
    languageHelp.textContent = `This option maps to the ${modelLanguage.toUpperCase()} multilingual model. Accent fallback without reference audio still depends on the base model voice.`;
  } else {
    languageHelp.textContent = "Other languages use the multilingual model. First use of a language may take longer to load.";
  }
}

textField.addEventListener("input", updateCharCount);
languageSelect.addEventListener("change", updateLanguageHelp);
emotionSelect.addEventListener("change", () => {
  applyEmotionPreset(emotionSelect.value);
  updateQualityHelp();
});
qualityMode.addEventListener("change", () => {
  applyQualityPreset(qualityMode.value);
  updateQualityHelp();
  updateEmotionHelp();
});
resetEmotionButton.addEventListener("click", resetEmotionPreset);

setRangeValue("exaggeration", "exaggeration-value");
setRangeValue("cfg_weight", "cfg-value");
setRangeValue("temperature", "temperature-value");
loadEmotionPresets();
applyEmotionPreset("neutral", true);
applyQualityPreset(qualityMode.value, true);
updateCharCount();
loadConfig();
updateQualityHelp();

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (currentAudioUrl) {
    URL.revokeObjectURL(currentAudioUrl);
    currentAudioUrl = null;
  }

  submitButton.disabled = true;
  downloadLink.classList.add("hidden");
  backendUsed.textContent = "Processing";
  statusLabel.textContent = "Generating audio. First backend load may take a while.";
  startTimer();

  try {
    const formData = new FormData(form);
    formData.delete("emotion_preset");
    const response = await fetch("/generate", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unexpected error." }));
      throw new Error(error.detail || "Failed to generate audio.");
    }

    const blob = await response.blob();
    currentAudioUrl = URL.createObjectURL(blob);

    player.src = currentAudioUrl;
    downloadLink.href = currentAudioUrl;
    downloadLink.download = response.headers.get("X-Output-Filename") || "chatterbox.wav";
    downloadLink.classList.remove("hidden");
    convertedCount.textContent = `${response.headers.get("X-Character-Count") || textField.value.length} characters`;
    backendUsed.textContent = response.headers.get("X-Backend") || "unknown";
    deviceUsed.textContent = (response.headers.get("X-Device") || "unknown").toUpperCase();
    const returnedQuality = response.headers.get("X-Quality-Mode");
    if (returnedQuality) {
      qualityMode.value = returnedQuality;
      updateQualityHelp();
    }
    statusLabel.textContent = `Audio generated successfully in ${elapsedLabel.textContent}.`;
  } catch (error) {
    statusLabel.textContent = error.message;
  } finally {
    stopTimer();
    submitButton.disabled = false;
  }
});


