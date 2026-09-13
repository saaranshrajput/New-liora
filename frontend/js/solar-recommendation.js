const saved = JSON.parse(localStorage.getItem("lioraCalculation") || "{}");
const historyStorage = "lioraPlanHistory";
const daily = saved.daily || 12;
const suggestedSize =
  saved.system || Math.max(1, Math.ceil((daily / 4.2) * 2) / 2);
const format = (value) =>
  new Intl.NumberFormat("en-IN", { maximumFractionDigits: 1 }).format(value);
const sizeInput = document.getElementById("sizeInput");
sizeInput.value = suggestedSize;
document.getElementById("dailyNeed").textContent = format(daily);
if (saved.city)
  document.getElementById("cityLabel").textContent =
    `Energy estimate for ${saved.city}`;

function getHistory() {
  return JSON.parse(localStorage.getItem(historyStorage) || "[]");
}

function saveHistory(entry) {
  const history = getHistory();
  history.unshift(entry);
  localStorage.setItem(historyStorage, JSON.stringify(history.slice(0, 5)));
}

function clearHistory() {
  localStorage.removeItem(historyStorage);
  renderHistory();
}

function renderHistory() {
  const history = getHistory();
  const container = document.getElementById("historyList");
  container.innerHTML = "";
  if (!history.length) {
    container.innerHTML = `<div class="history-empty">No history yet. Save a plan to compare bills after installation.</div>`;
    return;
  }
  history.forEach((entry) => {
    const item = document.createElement("div");
    item.className = "history-item";
    item.innerHTML = `
      <strong>${entry.date}</strong>
      <p>${entry.description}</p>
      <div class="history-values">
        <span>${entry.system_kw} kW</span>
        <span>${entry.monthly_saving}</span>
      </div>
    `;
    container.appendChild(item);
  });
}

function currentPlanSummary() {
  return {
    date: new Date().toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }),
    description: `${format(Number(sizeInput.value))} kW system with ${document.getElementById("panelType").selectedOptions[0].text}`,
    system_kw: format(Number(sizeInput.value)),
    monthly_saving: document.getElementById("saving").textContent,
  };
}

function updateRecommendation() {
  const size = Math.max(1, Number(sizeInput.value) || suggestedSize);
  const panelFactor = Number(document.getElementById("panelType").value);
  const inverterFactor = Number(document.getElementById("inverter").value);
  const batteryCost = Number(document.getElementById("battery").value);
  const dailyGeneration = size * 4.5 * panelFactor;
  const monthlyGeneration = dailyGeneration * 30;
  const monthlySaving = Math.min(monthlyGeneration, daily * 30) * 7;
  const cost = size * 72000 * inverterFactor + batteryCost;
  const area = Math.ceil(size * 85);
  document.getElementById("recommendedSize").textContent = format(size);
  document.getElementById("generation").textContent =
    `${format(dailyGeneration)}–${format(dailyGeneration * 1.08)} kWh`;
  document.getElementById("monthlyGeneration").textContent =
    `${format(monthlyGeneration)} kWh`;
  document.getElementById("saving").textContent = `₹${format(monthlySaving)}`;
  document.getElementById("cost").textContent = `₹${format(cost)}`;
  document.getElementById("payback").textContent =
    `${format(cost / Math.max(monthlySaving * 12, 1))} years`;
  document.getElementById("areaNeeded").textContent = format(area);
}
["panelType", "inverter", "battery", "roofArea", "sizeInput"].forEach((id) =>
  document.getElementById(id).addEventListener("input", updateRecommendation),
);
document.getElementById("savePlan").addEventListener("click", async () => {
  const button = document.getElementById("savePlan");
  const toast = document.getElementById("toast");
  button.disabled = true;
  button.textContent = "Creating your PDF…";
  try {
    const payload = {
      city: saved.city || "Your home",
      daily_kwh: daily,
      system_kw: Number(sizeInput.value),
      panel_type: document.getElementById("panelType").selectedOptions[0].text,
      inverter: document.getElementById("inverter").selectedOptions[0].text,
      mounting: document.getElementById("mount").value,
      battery: document.getElementById("battery").selectedOptions[0].text,
      roof_area: Number(document.getElementById("roofArea").value) || 0,
      daily_generation: document.getElementById("generation").textContent,
      monthly_generation:
        document.getElementById("monthlyGeneration").textContent,
      monthly_saving: document.getElementById("saving").textContent,
      installed_cost: document.getElementById("cost").textContent,
      payback: document.getElementById("payback").textContent,
    };
    const response = await fetch("/solar-plan.pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) throw new Error("PDF creation failed");
    const file = await response.blob();
    const url = URL.createObjectURL(file);
    const link = document.createElement("a");
    link.href = url;
    link.download = "liora-solar-plan.pdf";
    link.click();
    URL.revokeObjectURL(url);
    saveHistory(currentPlanSummary());
    renderHistory();
    toast.textContent = "Your Liora solar plan PDF is ready.";
  } catch (error) {
    toast.textContent = "We could not create the PDF. Please try again.";
  } finally {
    button.disabled = false;
    button.textContent = "Save my solar plan →";
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 3500);
  }
});

renderHistory();
updateRecommendation();
document.getElementById("clearHistory").addEventListener("click", clearHistory);
