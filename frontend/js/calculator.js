const defaults = [
  ['LED bulbs', 9, 5, 9], ['Ceiling fans', 4, 10, 75], ['Refrigerator', 1, 24, 75],
  ['Television', 1, 4, 100], ['Washing machine', 1, 1, 500], ['Air conditioner', 1, 6, 1500]
];
let appliances = defaults.map((item) => [...item]);
let familySize = 4;
const list = document.getElementById('applianceList');
const format = (value) => new Intl.NumberFormat('en-IN', { maximumFractionDigits: 1 }).format(value);

function render() {
  list.innerHTML = appliances.map((item, index) => {
    const daily = item[1] * item[2] * item[3] / 1000;
    return `<div class="appliance-row"><b>${item[0]}</b><input aria-label="${item[0]} quantity" data-index="${index}" data-key="1" type="number" min="0" value="${item[1]}"><input aria-label="${item[0]} power in watts" data-index="${index}" data-key="3" type="number" min="0" value="${item[3]}"><input aria-label="${item[0]} hours per day" data-index="${index}" data-key="2" type="number" min="0" max="24" step="0.5" value="${item[2]}"><span class="kwh">${format(daily)} kWh</span></div>`;
  }).join('');
  list.querySelectorAll('input').forEach((input) => input.addEventListener('input', (event) => {
    const target = event.currentTarget;
    appliances[target.dataset.index][target.dataset.key] = Math.max(0, Number(target.value) || 0);
    updateResults();
  }));
  updateResults();
}

function updateResults() {
  const homeMultiplier = Number(document.getElementById('homeType').value);
  const applianceUsage = appliances.reduce((total, item) => total + item[1] * item[2] * item[3] / 1000, 0);
  const daily = applianceUsage * homeMultiplier * (0.82 + familySize * 0.045);
  const monthly = daily * 30;
  const system = Math.max(1, Math.ceil((daily / 4.2) * 2) / 2);
  document.getElementById('dailyUsage').textContent = format(daily);
  document.getElementById('monthlyUsage').textContent = format(monthly);
  document.getElementById('systemSize').textContent = format(system);
  document.getElementById('dailyGeneration').textContent = `${format(system * 4.2)}–${format(system * 4.8)} kWh`;
  document.getElementById('monthlySaving').textContent = `₹${format(monthly * 7 * 0.75)}–₹${format(monthly * 7)}`;
  document.getElementById('estimatedCost').textContent = `₹${format(system * 65000)}–₹${format(system * 80000)}`;
  document.getElementById('usageMeter').style.width = `${Math.min(100, Math.max(12, daily / 30 * 100))}%`;
}

document.querySelectorAll('[data-counter]').forEach((button) => button.addEventListener('click', () => {
  familySize = Math.min(12, Math.max(1, familySize + Number(button.dataset.counter)));
  document.getElementById('familySize').textContent = familySize;
  updateResults();
}));
document.getElementById('homeType').addEventListener('change', updateResults);
document.getElementById('resetDefaults').addEventListener('click', () => { appliances = defaults.map((item) => [...item]); render(); });
document.getElementById('addAppliance').addEventListener('click', () => { appliances.push(['Other appliance', 1, 2, 100]); render(); });
document.getElementById('calculatorForm').addEventListener('submit', (event) => { event.preventDefault(); const daily = Number(document.getElementById('dailyUsage').textContent.replace(/,/g, '')); localStorage.setItem('lioraCalculation', JSON.stringify({ city: document.getElementById('city').value.trim(), daily, monthly: daily * 30, system: Number(document.getElementById('systemSize').textContent), familySize })); window.location.assign('/solar-recommendation'); });
render();
