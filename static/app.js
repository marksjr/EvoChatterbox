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

const emotionPresets = [
  { id: "neutral", label: "Neutro", help: "Equilibrado para uso geral.", exaggeration: 0.5, cfg: 0.5, temperature: 0.8 },
  { id: "calm", label: "Calmo", help: "Mais contido e suave.", exaggeration: 0.2, cfg: 0.55, temperature: 0.55 },
  { id: "soft", label: "Suave", help: "Leve, macio e pouco enfatico.", exaggeration: 0.25, cfg: 0.5, temperature: 0.6 },
  { id: "warm", label: "Acolhedor", help: "Timbre mais simpatico e proximo.", exaggeration: 0.35, cfg: 0.55, temperature: 0.75 },
  { id: "happy", label: "Feliz", help: "Mais brilho e energia.", exaggeration: 0.7, cfg: 0.45, temperature: 1.0 },
  { id: "excited", label: "Animado", help: "Mais dinamico e vibrante.", exaggeration: 0.85, cfg: 0.4, temperature: 1.15 },
  { id: "energetic", label: "Energetico", help: "Impulso alto para chamadas e anuncios.", exaggeration: 0.95, cfg: 0.35, temperature: 1.2 },
  { id: "dramatic", label: "Dramatico", help: "Mais contraste e intensidade.", exaggeration: 1.0, cfg: 0.65, temperature: 0.95 },
  { id: "serious", label: "Serio", help: "Controlado e firme.", exaggeration: 0.4, cfg: 0.65, temperature: 0.65 },
  { id: "authoritative", label: "Autoritario", help: "Mais comando e presenca.", exaggeration: 0.55, cfg: 0.7, temperature: 0.6 },
  { id: "narrator", label: "Narrador", help: "Mais estavel para leitura.", exaggeration: 0.35, cfg: 0.7, temperature: 0.55 },
  { id: "cinematic", label: "Cinematografico", help: "Mais teatral para trailers e spots.", exaggeration: 0.95, cfg: 0.6, temperature: 0.9 },
  { id: "sad", label: "Triste", help: "Mais contido e arrastado.", exaggeration: 0.3, cfg: 0.6, temperature: 0.45 },
  { id: "melancholic", label: "Melancolico", help: "Mais introspectivo.", exaggeration: 0.35, cfg: 0.65, temperature: 0.5 },
  { id: "fearful", label: "Tenso", help: "Leve instabilidade e tensao.", exaggeration: 0.75, cfg: 0.5, temperature: 1.05 },
  { id: "angry", label: "Bravo", help: "Mais enfase e ataque.", exaggeration: 0.9, cfg: 0.75, temperature: 0.85 },
  { id: "whispery", label: "Sussurrado", help: "Tente combinar com audio de referencia.", exaggeration: 0.15, cfg: 0.45, temperature: 0.5 },
  { id: "romantic", label: "Romantico", help: "Mais macio e caloroso.", exaggeration: 0.35, cfg: 0.5, temperature: 0.72 },
  { id: "comic", label: "Comico", help: "Mais elasticidade na entrega.", exaggeration: 0.9, cfg: 0.4, temperature: 1.1 },
  { id: "commercial", label: "Comercial", help: "Tom de locucao publicitaria.", exaggeration: 0.65, cfg: 0.55, temperature: 0.9 },
  { id: "podcast", label: "Podcast", help: "Mais natural e confortavel para fala longa.", exaggeration: 0.3, cfg: 0.6, temperature: 0.7 },
  { id: "urgent", label: "Urgente", help: "Mais pressao e ritmo.", exaggeration: 0.8, cfg: 0.7, temperature: 1.0 },
  { id: "instructional", label: "Instrucional", help: "Claro e didatico.", exaggeration: 0.25, cfg: 0.75, temperature: 0.55 }
];

let timerId = null;
let startedAt = 0;
let currentAudioUrl = null;

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
  input.addEventListener("input", sync);
  sync();
}

function syncDisplayedSliderValues() {
  document.getElementById("exaggeration-value").textContent = Number(exaggerationInput.value).toFixed(2);
  document.getElementById("cfg-value").textContent = Number(cfgInput.value).toFixed(2);
  document.getElementById("temperature-value").textContent = Number(temperatureInput.value).toFixed(2);
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

function applyEmotionPreset(presetId) {
  const preset = emotionPresets.find((item) => item.id === presetId);
  if (!preset) {
    return;
  }
  exaggerationInput.value = preset.exaggeration;
  cfgInput.value = preset.cfg;
  temperatureInput.value = preset.temperature;
  syncDisplayedSliderValues();
  updateEmotionHelp();
  updateActiveEmotionChip();
}

function resetEmotionPreset() {
  emotionSelect.value = "neutral";
  applyEmotionPreset("neutral");
}

function updateEmotionHelp() {
  const preset = emotionPresets.find((item) => item.id === emotionSelect.value);
  if (!preset) {
    emotionHelp.textContent = "Preset de entonacao baseado nos controles nativos do modelo.";
    return;
  }
  emotionHelp.textContent = `${preset.help} Exaggeration ${preset.exaggeration.toFixed(2)}, CFG ${preset.cfg.toFixed(2)}, Temperature ${preset.temperature.toFixed(2)}.`;
}

function updateCharCount() {
  const count = textField.value.length;
  charCount.textContent = `${count} caracteres`;
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

async function loadConfig() {
  try {
    const response = await fetch("/config");
    const config = await response.json();

    for (const language of config.languages) {
      const option = document.createElement("option");
      option.value = language.id;
      option.textContent = `${language.label} (${language.id})`;
      option.dataset.backend = language.backend;
      if (language.id === config.default_language) {
        option.selected = true;
      }
      languageSelect.appendChild(option);
    }

    deviceUsed.textContent = config.device.toUpperCase();
    updateLanguageHelp();
  } catch (error) {
    languageHelp.textContent = "Nao foi possivel carregar os idiomas.";
  }
}

function updateLanguageHelp() {
  const selectedOption = languageSelect.selectedOptions[0];
  if (!selectedOption) {
    return;
  }

  const backend = selectedOption.dataset.backend;
  if (backend === "standard") {
    languageHelp.textContent = "English usa o modelo padrao, normalmente mais leve e mais rapido.";
  } else {
    languageHelp.textContent = "Outros idiomas usam o modelo multilingual. No primeiro uso desse idioma, o carregamento pode demorar mais.";
  }
}

textField.addEventListener("input", updateCharCount);
languageSelect.addEventListener("change", updateLanguageHelp);
emotionSelect.addEventListener("change", () => applyEmotionPreset(emotionSelect.value));
resetEmotionButton.addEventListener("click", resetEmotionPreset);

setRangeValue("exaggeration", "exaggeration-value");
setRangeValue("cfg_weight", "cfg-value");
setRangeValue("temperature", "temperature-value");
loadEmotionPresets();
applyEmotionPreset("neutral");
updateCharCount();
loadConfig();

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  if (currentAudioUrl) {
    URL.revokeObjectURL(currentAudioUrl);
    currentAudioUrl = null;
  }

  submitButton.disabled = true;
  downloadLink.classList.add("hidden");
  backendUsed.textContent = "Processando";
  statusLabel.textContent = "Gerando audio. O primeiro carregamento de um backend pode demorar.";
  startTimer();

  try {
    const formData = new FormData(form);
    formData.delete("emotion_preset");
    const response = await fetch("/generate", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Erro inesperado." }));
      throw new Error(error.detail || "Falha ao gerar audio.");
    }

    const blob = await response.blob();
    currentAudioUrl = URL.createObjectURL(blob);

    player.src = currentAudioUrl;
    downloadLink.href = currentAudioUrl;
    downloadLink.classList.remove("hidden");
    convertedCount.textContent = `${response.headers.get("X-Character-Count") || textField.value.length} caracteres`;
    backendUsed.textContent = response.headers.get("X-Backend") || "desconhecido";
    deviceUsed.textContent = (response.headers.get("X-Device") || "desconhecido").toUpperCase();
    statusLabel.textContent = `Audio gerado com sucesso em ${elapsedLabel.textContent}.`;
  } catch (error) {
    statusLabel.textContent = error.message;
  } finally {
    stopTimer();
    submitButton.disabled = false;
  }
});
